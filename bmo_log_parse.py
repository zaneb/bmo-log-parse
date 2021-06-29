#!/usr/bin/env python3

#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

"""
Utility for filtering and displaying logs from the Metal³ baremetal-operator.

Written by Zane Bitter.
"""

import collections
import contextlib
import datetime
import functools
import itertools
import json
import re
import sys

import autopage

try:
    import yaml
except ImportError:
    pretty_print = functools.partial(json.dumps, indent=2)
else:
    pretty_print = functools.partial(yaml.safe_dump, default_flow_style=False)


LOGGERS = (
    COMMAND,
    RUNTIME,
    CONTROLLER,
    PROVISIONER,
) = (
    {'cmd', 'setup', ''},
    {'controller-runtime'},
    {'controller', 'baremetalhost', 'controllers'},
    {'baremetalhost_ironic', 'provisioner'},
)

LEVELS = (
    INFO, ERROR,
) = (
    'info', 'error',
)


_matcher = re.compile(r'''
(?:
20[0-9]{2}-[0-1][0-9]-[0-3][0-9]                # ISO8601 date
T[0-2][0-9]:[0-5][0-9]:[0-6][0-9](?:\.[0-9]+)Z  # ISO8601 time
[ ])?                                           # drop any leading datetime
(\{.*?\})                                       # match JSON object
\n''', re.VERBOSE).fullmatch


class ParseException(Exception):
    def __init__(self, error, match, lineno=None):
        self.err_msg = error.msg
        self.lineno = lineno
        self.column = error.colno + match.start(1)
        self.line = match.group(0)

        ln = f'line {self.lineno}, ' if self.lineno is not None else ''
        super().__init__(f'Record parse error: {self.err_msg} '
                         f'(at {ln}column {self.column}): {self.line}')


def _parse_record(m):
    i, match = m
    if match is None:
        return None
    try:
        return json.loads(match.group(1))
    except json.decoder.JSONDecodeError as exc:
        raise ParseException(exc, match, i)


def read_records(logstream):
    return (Record(p) for p in map(_parse_record, enumerate(map(_matcher,
                                                                logstream)))
            if p is not None)


class Record:
    """Class representing a single log record."""

    COMMON_FIELDS = (
        LEVEL, TIMESTAMP, LOGGER, MESSAGE,
    ) = (
        'level', 'ts', 'logger', 'msg',
    )

    def __init__(self, data):
        """Initialise from the (JSON) log text."""
        self.level = data.pop(self.LEVEL)
        ts = float(data.pop(self.TIMESTAMP))
        utc = datetime.timezone.utc
        self.timestamp = datetime.datetime.fromtimestamp(ts, tz=utc)
        self.logger = data.pop(self.LOGGER, '').split('.', 1)[0]
        self.message = data.pop(self.MESSAGE)
        self.context = None
        fq_name = (data.get('baremetalhost',
                            data.get('Request.Name',
                                     data.get('name')))
                   if self.logger not in PROVISIONER
                   else data.get('host', '').replace('~', '/', 1) or None)
        if 'stacktrace' in data:
            if fq_name is None:
                fq_name = data['request']
            self.context = data.pop('stacktrace')
        elif (self.message == 'received introspection data' and
                'data' in data):
            self.context = pretty_print(data.pop('data'))
        ns_name = fq_name.split('/', 1) if fq_name is not None else (None,
                                                                     None)
        self.name = ns_name[-1]
        self.namespace = data.get('namespace',
                                  data.get('Request.Namespace',
                                           ns_name[0] if len(ns_name) > 1
                                           else None))
        self.error = data.pop('error', None) if self.level == ERROR else None
        data.pop('errorVerbose', None)
        data.pop('reconciler group', None)
        data.pop('reconciler kind', None)
        self.data = data

    def format(self, highlight=False):
        """
        Format the log record as a human-readable string.

        :param highlight: Use ANSI escape codes to set colours.
        """
        if highlight:
            if self.level == ERROR:
                esc = ('\033[91m', '\033[31m', '\033[39m')
            else:
                esc = ('\033[37m', '\033[39m', '\033[39m')
        else:
            esc = ('', '', '')

        extra_data = ''
        if self.data:
            items = ', '.join(f'{k}: {repr(v)}' for k, v in self.data.items())
            extra_data = f' {{{items}}}'
            if highlight:
                extra_data = f'{esc[0]}{extra_data}{esc[2]}'
        else:
            if highlight:
                extra_data = esc[2]
        if self.error is not None:
            err = f'{esc[1]}{self.error}{esc[2]}'
            extra_data = '\n'.join([extra_data, err])
        if self.context is not None:
            ct = self.context
            if highlight:
                ct = '\n'.join(f'\033[90m{l}\033[39m' for l in ct.splitlines())
            extra_data = '\n'.join([extra_data, ct])
        timestamp = self.timestamp.isoformat(timespec='milliseconds')[:-6]
        return f'{esc[0]}{timestamp} {esc[1]}{self.message}{extra_data}'

    def __str__(self):
        return self.format()


Filter = collections.namedtuple('Filter', ['filterfunc', 'predicate'])


def filtered_records(logstream, filters):
    """Iterate over all log Records in the stream that match the filters."""
    return functools.reduce(lambda r,f: f.filterfunc(f.predicate, r),
                            filters, read_records(logstream))


def process_log(input_stream, filters, output_stream=sys.stdout,
                highlight=False):
    """Process the input log stream and write to an output stream."""
    for r in filtered_records(input_stream, filters):
        output_stream.write(f'{r.format(highlight)}\n')


def list_host_names(input_stream, filters, output_stream=sys.stdout):
    seen = set()
    for r in filtered_records(input_stream, filters):
        if r.name not in seen and r.name is not None:
            output_stream.write(f'{r.name}\n')
            seen.add(r.name)


def get_filters(options):
    """Iterate over the Filters specified by the given CLI options."""
    if options.start is not None:
        start_time = options.start
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=datetime.timezone.utc)
        yield Filter(itertools.dropwhile,
                     lambda r: r.timestamp < start_time)
    if options.error:
        yield Filter(filter, lambda r: r.level == ERROR)
    if options.controller_only:
        yield Filter(filter, lambda r: r.logger in CONTROLLER)
    if options.provisioner_only:
        yield Filter(filter, lambda r: r.logger in PROVISIONER)
    if options.name is not None:
        name = options.name
        yield Filter(filter, lambda r: r.name == name)
    if options.namespace is not None:
        namespace = options.namespace
        yield Filter(filter, lambda r: r.namespace == namespace)
    if options.end is not None:
        end_time = options.end
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=datetime.timezone.utc)
        yield Filter(itertools.takewhile,
                     lambda r: r.timestamp <= end_time)


def parse_datetime(dtstr):
    if hasattr(datetime.datetime, 'fromisoformat'):
        return datetime.datetime.fromisoformat(dtstr)

    fmt = '%Y-%m-%d'
    if 'T' in dtstr:
        fmt += 'T%H:%M'
        if dtstr.count(':') > 1:
            fmt += ':%S'
            if '.' in dtstr:
                fmt += '.%f'
    return datetime.datetime.strptime(dtstr, fmt)


def get_options(args=None):
    """Parse the CLI arguments into options."""
    from autopage import argparse
    import pydoc

    desc = pydoc.getdoc(sys.modules[__name__])
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('logfile', nargs='?', default='-',
                        help='Input logfile (or "-" to read stdin)')

    logger_group = parser.add_mutually_exclusive_group()
    logger_group.add_argument('-c', '--controller-only', action='store_true',
                              help='Include only controller module logs')
    logger_group.add_argument('-p', '--provisioner-only', action='store_true',
                              help='Include only provisioner module logs')

    parser.add_argument('--error', action='store_true',
                        help='Include only logs at ERROR level')
    parser.add_argument('-n', '--name', default=None,
                        help='Filter by a particular host name')
    parser.add_argument('--namespace', default=None,
                        help='Filter by a particular host namespace')

    parser.add_argument('-s', '--start', default=None,
                        type=parse_datetime,
                        help='Skip ahead to a given time')
    parser.add_argument('-e', '--end', default=None,
                        type=parse_datetime,
                        help='Stop reading at a given time')

    parser.add_argument('--list-names', action='store_true',
                        help='List the names of hosts in the log')

    return parser.parse_args(args)


def input_stream(filename):
    """
    Return a context manager for an input stream given the filename option.

    Returns stdin if the filename is '-'.
    """
    if filename == '-':
        @contextlib.contextmanager
        def nullcontext(arg):
            yield arg

        return nullcontext(sys.stdin)
    else:
        return open(filename)


def _report_error(message, stream=None):
    if stream is None:
        stream = sys.stderr
    colour = stream.isatty()
    if colour:
        line = f'\033[93m{message}\033[39m\n'
    else:
        line = f'{message}\n'
    stream.write(line)


def main():
    """Run the log parser, reading options from the command line."""
    try:
        options = get_options()
    except Exception as exc:
        _report_error(str(exc))
        return 1

    filters = get_filters(options)
    with input_stream(options.logfile) as logstream:
        if logstream.isatty():
            _report_error('No input found.')
            return 1

        line_buffer = autopage.line_buffer_from_input(logstream)
        error_strategy = autopage.ErrorStrategy.BACKSLASH_REPLACE
        pager = autopage.AutoPager(line_buffering=line_buffer,
                                   reset_on_exit=True,
                                   errors=error_strategy)
        highlight = pager.to_terminal()
        try:
            with pager as output_stream:
                if options.list_names:
                    list_host_names(logstream, filters, output_stream)
                else:
                    process_log(logstream, filters, output_stream, highlight)
        except KeyboardInterrupt:
            pass
        except ParseException as exc:
            _report_error(str(exc))
        return pager.exit_code()


if __name__ == '__main__':
    sys.exit(main())
