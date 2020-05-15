#!/usr/bin/env python3.8

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


LOGGERS = (
    COMMAND, RUNTIME,
    CONTROLLER, PROVISIONER,
) = (
    'cmd', 'controller-runtime.controller',
    'baremetalhost', 'baremetalhost_ironic',
)

LEVELS = (
    INFO, ERROR,
) = (
    'info', 'error',
)


def read_records(logstream):
    return map(Record,
               filter(lambda l: l.startswith('{'),
                      logstream))


class Record:
    COMMON_FIELDS = (
        LEVEL, TIMESTAMP, LOGGER, MESSAGE,
    ) = (
        'level', 'ts', 'logger', 'msg',
    )

    def __init__(self, line):
        data = json.loads(line)
        self.level = data.pop(self.LEVEL)
        ts = float(data.pop(self.TIMESTAMP))
        utc = datetime.timezone.utc
        self.timestamp = datetime.datetime.fromtimestamp(ts, tz=utc)
        self.logger = data.pop(self.LOGGER)
        self.message = data.pop(self.MESSAGE)
        self.stacktrace = data.pop('stacktrace', None)
        data.pop('errorVerbose', None)
        self.data = data
        if self.stacktrace is not None:
            self.name = data['request'].split('/', 1)[1]
        else:
            self.name = (data.get('Request.Name')
                            if self.logger == CONTROLLER
                            else data.get('host'))

    def format(self, highlight=False):
        esc = (('\033[91m', '\033[39m')
                   if highlight and self.level == ERROR
                   else ('', ''))

        extra_data = ''
        if self.data:
            items = ', '.join(f'{k}: {repr(v)}'
                              for k, v in self.data.items())
            extra_data = f' {{{items}}}{esc[1]}'
        if (st := self.stacktrace) is not None:
            if highlight:
                st = '\n'.join(f'\033[90m{l}\033[39m' for l in st.splitlines())
            extra_data = '\n'.join([extra_data, st])
        timestamp = self.timestamp.isoformat(timespec='milliseconds')[:-6]
        return f'{esc[0]}{timestamp} {self.message}{extra_data}'

    def __str__(self):
        return self.format()


Filter = collections.namedtuple('Filter', ['filterfunc', 'predicate'])


def filtered_records(logstream, filters):
    return functools.reduce(lambda r,f: f.filterfunc(f.predicate, r),
                            filters, read_records(logstream))


def process_log(input_stream, filters, output_stream=sys.stdout):
    highlight = output_stream.isatty()

    for r in filtered_records(input_stream, filters):
        try:
            output_stream.write(f'{r.format(highlight)}\n')
        except BrokenPipeError:
            # Acknowledge failed writes now, otherwise an error is printed to
            # the console on interpreter exit.
            try:
                output_stream.flush()
            except IOError:
                pass
            return


def get_filters(options):
    if (start_time := options.start) is not None:
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
    if (name := options.name) is not None:
        yield Filter(filter, lambda r: r.name == name)
    if (end_time := options.end) is not None:
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=datetime.timezone.utc)
        yield Filter(itertools.takewhile,
                     lambda r: r.timestamp <= end_time)


def get_options(args=None):
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

    time_type = datetime.datetime.fromisoformat
    parser.add_argument('-s', '--start', default=None,
                        type=time_type,
                        help='Skip ahead to a given time')
    parser.add_argument('-e', '--end', default=None,
                        type=time_type,
                        help='Stop reading at a given time')

    return parser.parse_args(args)


def input_stream(filename):
    if filename == '-':
        return contextlib.nullcontext(sys.stdin)
    else:
        return open(filename)


def main():
    try:
        options = get_options()
    except Exception as exc:
        sys.stderr.write(f'{exc}\n')
        return 1

    filters = get_filters(options)
    with input_stream(options.logfile) as logstream:
        process_log(logstream, filters)
    return 0


if __name__ == '__main__':
    try:
        return_code = main()
    except KeyboardInterrupt:
        sys.exit(1)
    else:
        sys.exit(return_code)
