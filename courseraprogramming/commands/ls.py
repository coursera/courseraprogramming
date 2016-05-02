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

from courseraprogramming.commands import common
from courseraprogramming import utils
import logging
import sys


def command_ls(args):
    "Implements the ls subcommand"
    d = utils.docker_client(args)
    command = []
    if args.l:
        command.append('-l')
    if args.human:
        command.append('-h')
    if args.a:
        command.append('-a')
    command.append(args.dir)
    logging.debug("Commands: %s", command)
    try:
        container = d.create_container(
            image=args.imageId,
            entrypoint="/bin/ls",
            command=command)
    except:
        logging.error(
            "Could not set up the container to run the ls command in. Most "
            "likely, this means that you specified an inappropriate container "
            "id.")
        raise
    d.start(container)
    exit_code = d.wait(container, timeout=2)
    if exit_code != 0:
        logging.warn("The ls command did not exit cleanly within the "
                     "container. Exit code: %s", exit_code)

    command_output = d.logs(container)
    # Use sys.stdout to avoid extra trailing newline. (Py3.x compatible)
    sys.stdout.write(command_output)
    if not args.no_rm:
        d.remove_container(container)


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."

    # create the parser for the ls command
    parser_ls = subparsers.add_parser(
        'ls',
        help='Runs the ls command inside your container to check the location \
            of files within the container.',
        parents=[common.container_parser()])
    parser_ls.set_defaults(func=command_ls)
    parser_ls.add_argument(
        '-l',
        action='store_true',
        help='Output additional file information including file size.')
    parser_ls.add_argument(
        '--human',
        action='store_true',
        help='Output file sizes in human-readable denominations (requires -l \
            flag)')
    parser_ls.add_argument(
        '-a',
        action='store_true',
        help='Include "hidden" files in the listing.')
    parser_ls.add_argument(
        'dir',
        help='The directory to list. (e.g. /grader)')
    parser_ls.add_argument(
        '--no-rm',
        action='store_true',
        help="Don't remove the container after running the ls command.")

    return parser_ls
