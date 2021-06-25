# Metal³ baremetal-operator log parser

This is tool to produce human-readable logs from the structured log output of
the [baremetal-operator](https://github.com/metal3-io/baremetal-operator) from
the [Metal³](https://metal3.io/) project.

It is written in Python and requires Python 3.6 or later.

## Installation

### On Fedora or CentOS/RHEL

Distro packages are available in Copr:

```bash
sudo dnf copr enable zaneb/autopage
sudo dnf install python3-bmo-log-parse
```

### Everywhere else

Install using pip:

```bash
pip3 install --user https://github.com/zaneb/bmo-log-parse
```

This automatically installs dependencies also. (Specifically, the
[autopage](https://pypi.org/project/autopage/) library is a requirement.)

## Usage

By default, the tool reads from stdin and writes to stdout. It can be used with
either an existing log file or a `tail -f`-style stream. If the output is not
piped or redirected, a pager is automatically invoked.

Several filters are available to winnow the output.


    usage: bmo-log-parse [-h] [-c | -p] [--error] [-n NAME]
                         [--namespace NAMESPACE] [-s START] [-e END]
                         [--list-names]
                         [logfile]

    positional arguments:
      logfile               Input logfile (or "-" to read stdin)

    optional arguments:
      -h, --help            show this help message and exit
      -c, --controller-only
                            Include only controller module logs
      -p, --provisioner-only
                            Include only provisioner module logs
      --error               Include only logs at ERROR level
      -n NAME, --name NAME  Filter by a particular host name
      --namespace NAMESPACE
                            Filter by a particular host namespace
      -s START, --start START
                            Skip ahead to a given time
      -e END, --end END     Stop reading at a given time
      --list-names          List the names of hosts in the log

## Testing

Run the unit tests using `tox`.
