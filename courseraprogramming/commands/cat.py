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


def command_cat(args):
    "Implements the cat subcommand"
    d = utils.docker_client(args)
    try:
        container = d.create_container(
            image=args.imageId,
            entrypoint="/bin/cat",
            command=args.file)
    except:
        logging.error(
            "Could not set up the container to run the cat command in. Most "
            "likely, this means that you specified an inappropriate container "
            "id.")
        raise
    d.start(container)
    exit_code = d.wait(container, timeout=2)
    if exit_code != 0:
        logging.warn("The cat command did not exit cleanly within the "
                     "container. Exit code: %s", exit_code)

    command_output = d.logs(container)
    # Use sys.stdout to avoid extra trailing newline. (Py3.x compatible)
    sys.stdout.write(command_output)


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    # create the parser for the cat command
    parser_cat = subparsers.add_parser(
        'cat',
        help='Output files within the container to the console for debugging',
        parents=[common.container_parser()])
    parser_cat.set_defaults(func=command_cat)
    parser_cat.add_argument('file', help='File(s) to output.', nargs='+')
    return parser_cat
