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


def container_parser():
    "Build an argparse argument parser to parse the command line."

    # The following subcommands operate on a single containers. We centralize
    # all these options here.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        'containerId',
        help='The container id to operate on.')

    return parser
