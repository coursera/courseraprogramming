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

from courseraprogramming.commands import oauth2
import requests
import logging
import sys


def command_config(args):
    "Implements the configure subcommand"
    # TODO: check for existance of ~/.coursera directory and create it if
    # required.

    cfg = oauth2.configuration()
    auth = oauth2.build_authorizer(args, cfg)
    whoami_url = \
        'https://api.coursera.org/api/externalBasicProfiles.v1?q=me&fields=name,locale,timezone,privacy'
    r = requests.get(whoami_url, auth=auth)
    print r.status_code
    print r.json()
    print ''


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    # create the parser for the configure subcommand. (authentication / etc.)
    parser_config = subparsers.add_parser(
        'configure',
        help='Configure %(prog)s for operation!')
    parser_config.set_defaults(func=command_config)
    return parser_config
