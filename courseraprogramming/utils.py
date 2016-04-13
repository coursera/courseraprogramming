#!/usr/bin/env python

# Copyright 2015 Coursera
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Coursera's asynchronous grader command line SDK.

You may install it from source, or via pip.
"""

import argparse
from docker.client import Client
from docker.utils import kwargs_from_env
import requests
import logging
import sys
from sys import platform as _platform


def add_logging_parser(main_parser):
    "Build an argparse argument parser to parse the command line."

    main_parser.set_defaults(setup_logging=set_logging_level)

    verbosity_group = main_parser.add_mutually_exclusive_group(required=False)
    verbosity_group.add_argument(
        '--verbose',
        '-v',
        action='count',
        help='Output more verbose logging. Can be specified multiple times.')
    verbosity_group.add_argument(
        '--quiet',
        '-q',
        action='count',
        help='Output less information to the console during operation. Can be \
            specified multiple times.')

    main_parser.add_argument(
        '--silence-urllib3',
        action='store_true',
        help='Silence urllib3 warnings. See '
        'https://urllib3.readthedocs.org/en/latest/security.html for details.')

    return verbosity_group


def set_logging_level(args):
    "Computes and sets the logging level from the parsed arguments."
    root_logger = logging.getLogger()
    level = logging.INFO
    logging.getLogger('requests.packages.urllib3').setLevel(logging.WARNING)
    if "verbose" in args and args.verbose is not None:
        logging.getLogger('requests.packages.urllib3').setLevel(0)  # Unset
        if args.verbose > 1:
            level = 5  # "Trace" level
        elif args.verbose > 0:
            level = logging.DEBUG
        else:
            logging.critical("verbose is an unexpected value. (%s) exiting.",
                             args.verbose)
            sys.exit(2)
    elif "quiet" in args and args.quiet is not None:
        if args.quiet > 1:
            level = logging.ERROR
        elif args.quiet > 0:
            level = logging.WARNING
        else:
            logging.critical("quiet is an unexpected value. (%s) exiting.",
                             args.quiet)
    if level is not None:
        root_logger.setLevel(level)

    if args.silence_urllib3:
        # See: https://urllib3.readthedocs.org/en/latest/security.html
        requests.packages.urllib3.disable_warnings()


def docker_client_arg_parser():
    "Builds an argparse parser for docker client connection flags."
    # The following subcommands operate on a single containers. We centralize
    # all these options here.
    docker_parser = argparse.ArgumentParser(add_help=False)
    docker_parser.add_argument(
        '--docker-url',
        help='The url of the docker demon.')
    docker_parser.add_argument(
        '--strict-docker-tls',
        action='store_true',
        help='Do not disable strict tls checks for the docker client (mac \
            os x only).')
    docker_parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        help='Set the default timeout when interacting with the docker demon')
    return docker_parser


def docker_client(args):
    """
    Attempts to create a docker client.

     - args: The arguments parsed on the command line.
     - returns: a docker-py client
    """
    if _platform == 'linux' or _platform == 'linux2':
        # linux
        if "docker_url" in args:
            return Client(
                base_url=args.docker_url,
                timeout=args.timeout,
                version='auto')
        else:
            # TODO: test to see if this does the right thing by default.
            return Client(
                version='auto',
                timeout=args.timeout,
                **kwargs_from_env())
    elif _platform == 'darwin':
        # OS X - Assume boot2docker, and pull from that environment.
        kwargs = kwargs_from_env()
        if len(kwargs) == 0:
            logging.error('Could not correctly pull in docker environment. '
                          'Try running: eval "$(docker-machine env default)"')
            sys.exit(2)
        if not args.strict_docker_tls:
            kwargs['tls'].assert_hostname = False

        return Client(version='auto', timeout=args.timeout, **kwargs)
    elif _platform == 'win32' or _platform == 'cygwin':
        # Windows.
        logging.fatal("Sorry, windows is not currently supported!")
        sys.exit(2)


def check_int_range(value, lower=None, upper=None):
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('{} is not an integer'.format(value))
    if lower is not None and value < lower:
        raise argparse.ArgumentTypeError(
            '{} is below the lower bound of {}'.format(value, lower))
    if upper is not None and value > upper:
        raise argparse.ArgumentTypeError(
            '{} is above the upper bound of {}'.format(value, upper))
    return value
