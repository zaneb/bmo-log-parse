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
import sys

try:
    import yaml
except ImportError:
    pretty_print = functools.partial(json.dumps, indent=2)
else:
    pretty_print = yaml.safe_dump


LOGGERS = (
    COMMAND, RUNTIME,
    CONTROLLER, PROVISIONER,
) = (
    'cmd', 'controller-runtime',
    'baremetalhost', 'baremetalhost_ironic',
)

LEVELS = (
    INFO, ERROR,
) = (
    'info', 'error',
)


def read_records(logstream):
    """Iterate over all Records in a stream."""
    return map(Record,
               filter(lambda l: l.startswith('{'),
                      logstream))


class Record:
    """Class representing a single log record."""

    COMMON_FIELDS = (
        LEVEL, TIMESTAMP, LOGGER, MESSAGE,
    ) = (
        'level', 'ts', 'logger', 'msg',
    )

    def __init__(self, line):
        """Initialise from the (JSON) log text."""
        data = json.loads(line)
        self.level = data.pop(self.LEVEL)
        ts = float(data.pop(self.TIMESTAMP))
        utc = datetime.timezone.utc
        self.timestamp = datetime.datetime.fromtimestamp(ts, tz=utc)
        self.logger = data.pop(self.LOGGER).split('.', 1)[0]
        self.message = data.pop(self.MESSAGE)
        self.context = None
        self.name = (data.get('Request.Name')
                        if self.logger == CONTROLLER
                        else data.get('host'))
        if 'stacktrace' in data:
            self.name = data['request'].split('/', 1)[1]
            self.context = data.pop('stacktrace')
        elif (self.message == 'received introspection data' and
                'data' in data):
            self.context = pretty_print(data.pop('data'))
        data.pop('errorVerbose', None)
        self.data = data

    def format(self, highlight=False):
        """
        Format the log record as a human-readable string.

        :param highlight: Use ANSI escape codes to set colours.
        """
        esc = (('\033[91m', '\033[39m')
                   if highlight and self.level == ERROR
                   else ('', ''))

        extra_data = ''
        if self.data:
            items = ', '.join(f'{k}: {repr(v)}'
                              for k, v in self.data.items())
            extra_data = f' {{{items}}}{esc[1]}'
        if self.context is not None:
            ct = self.context
            if highlight:
                ct = '\n'.join(f'\033[90m{l}\033[39m' for l in ct.splitlines())
            extra_data = '\n'.join([extra_data, ct])
        timestamp = self.timestamp.isoformat(timespec='milliseconds')[:-6]
        return f'{esc[0]}{timestamp} {self.message}{extra_data}'

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
        try:
            output_stream.write(f'{r.format(highlight)}\n')
        except BrokenPipeError:
            break
    try:
        output_stream.flush()
    except BrokenPipeError:
        pass


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
        yield Filter(filter, lambda r: r.logger == CONTROLLER)
    if options.provisioner_only:
        yield Filter(filter, lambda r: r.logger == PROVISIONER)
    if options.name is not None:
        name = options.name
        yield Filter(filter, lambda r: r.name == name)
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
    import argparse
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

    parser.add_argument('-s', '--start', default=None,
                        type=parse_datetime,
                        help='Skip ahead to a given time')
    parser.add_argument('-e', '--end', default=None,
                        type=parse_datetime,
                        help='Stop reading at a given time')

    return parser.parse_args(args)


def input_stream(filename):
    """
    Return a context manager for an input stream given the filename option.

    Returns stdin if the filename is '-'.
    """
    if filename == '-':
        return contextlib.nullcontext(sys.stdin)
    else:
        return open(filename)


@contextlib.contextmanager
def pager(output_stream, line_buffer=False):
    """
    A context manager that launches a pager for the output if appropriate.

    If the output stream is not to the console (i.e. it is piped or
    redirected), no pager will be launched.
    """
    if not output_stream.isatty():
        if line_buffer:
            output_stream.reconfigure(line_buffering=line_buffer)
        yield output_stream
        return

    import subprocess
    pager = subprocess.Popen(['less', '-R'],
                             stdin=subprocess.PIPE)
    try:
        import io
        with io.TextIOWrapper(pager.stdin,
                              line_buffering=line_buffer,
                              errors='backslashreplace') as stream:
            try:
                yield stream
            except KeyboardInterrupt:
                pass
    except OSError:
        pass
    finally:
        while True:
            try:
                pager.wait()
                break
            except KeyboardInterrupt:
                # Pager ignores Ctrl-C, so we should too
                pass


def main():
    """Run the log parser, reading options from the command line."""
    try:
        options = get_options()
    except Exception as exc:
        sys.stderr.write(f'{exc}\n')
        return 1

    filters = get_filters(options)
    with input_stream(options.logfile) as logstream:
        line_buffer = not logstream.seekable()
        with pager(sys.stdout, line_buffer) as output_stream:
            process_log(logstream, filters, output_stream, sys.stdout.isatty())
    return 0


if __name__ == '__main__':
    try:
        return_code = main()
    except KeyboardInterrupt:
        sys.exit(1)
    else:
        sys.exit(return_code)
