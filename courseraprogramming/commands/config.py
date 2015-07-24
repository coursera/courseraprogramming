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

import logging
import sys


def command_config(args):
    "Implements the configure subcommand"
    # TODO: IMPLEMENT ME!
    logging.fatal('The upload subcommand is not implemented! :-( Sorry!')
    sys.exit(3)


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    # create the parser for the configure subcommand. (authentication / etc.)
    parser_config = subparsers.add_parser(
        'configure',
        help='Configure %(prog)s for operation!')
    parser_config.set_defaults(func=command_config)

    return parser_config
