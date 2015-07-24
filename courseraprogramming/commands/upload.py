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
import logging
import sys


def command_upload(args):
    "Implements the upload subcommand"
    # TODO: IMPLEMENT ME!
    logging.fatal('The upload subcommand is not implemented! :-( Sorry!')
    sys.exit(3)


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    # create the parser for the upload command.
    parser_upload = subparsers.add_parser(
        'upload',
        help='Upload a container to Coursera.',
        parents=[common.container_parser()])
    parser_upload.set_defaults(func=command_upload)

    return parser_upload
