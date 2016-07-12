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
from courseraprogramming import commands
from courseraprogramming import utils
import logging
import sys


def build_parser():
    "Build an argparse argument parser to parse the command line."

    parser = argparse.ArgumentParser(
        description="""Coursera asynchronous grader command-line tool. This tool
        helps instructional teams as they develop sophisticated assignments.
        There are a number of subcommands, each with their own help
        documentation. Feel free to view them by executing `%(prog)s
        SUB_COMMAND -h`. For example: `%(prog)s ls -h`.""",
        epilog="""Please file bugs on github at:
        https://github.com/coursera/courseraprogramming/issues. If you
        would like to contribute to this tool's development, check us out at:
        https://github.com/coursera/courseraprogramming""",
        parents=[utils.docker_client_arg_parser()])
    parser.add_argument('-c', '--config', help='the configuration file to use')

    utils.add_logging_parser(parser)

    # We have a number of subcommands. These subcommands have their own
    # subparsers. Each subcommand should set a default value for the 'func'
    # option. We then call the parsed 'func' function, and execution carries on
    # from there.
    subparsers = parser.add_subparsers()

    # create the parser for the cat command
    commands.cat.parser(subparsers)

    # create the parser for the configure subcommand. (authentication / etc.)
    commands.config.parser(subparsers)

    # create the parser for the grade subcommand.
    commands.grade.parser(subparsers)

    # create the parser for the inspect command
    commands.inspect.parser(subparsers)

    # create the parser for the ls command
    commands.ls.parser(subparsers)

    # create the parser for the sanity check command
    commands.sanity.parser(subparsers)

    # create the parser for the version subcommand.
    commands.version.parser(subparsers)

    # create the parser for the run command?

    # create the parser for the build command?

    # create the parser for the upload command.
    commands.upload.parser(subparsers)

    # create the parser for the publish command.
    commands.publish.parser(subparsers)

    # create the parser for the reregister command.
    commands.reregister.parser(subparsers)

    return parser


def main():
    "Boots up the command line tool"
    logging.captureWarnings(True)
    args = build_parser().parse_args()
    # Configure logging
    args.setup_logging(args)
    # Dispatch into the appropriate subcommand function.
    try:
        return args.func(args)
    except SystemExit:
        raise
    except:
        logging.exception('Problem when running command. Sorry!')
        sys.exit(1)


if __name__ == "__main__":
    main()
