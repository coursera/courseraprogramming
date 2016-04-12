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
import os


def command_inspect(args):
    'Implements the inspect subcommand'
    command_line = [
        'docker',
        'run',
        '-it',
        '--entrypoint',
        args.shell,
    ]
    if 'submission' in args and args.submission is not None:
        command_line.append('-v')
        command_line.append(common.mk_submission_volume_str(args.submission))
    if not args.allow_network:
        command_line.append('--net')
        command_line.append('none')
    if not args.unlimited_memory:
        command_line.append('-m')
        command_line.append('1g')
    if not args.no_rm:
        command_line.append('--rm')
    if not args.super_user:
        # Note: docker run CLI doesn't support setting the group. :-(
        command_line.append('-u')
        command_line.append('1000')
    command_line.append(args.imageId)
    logging.debug("About to execute command: %s", ' '.join(command_line))
    os.execvp('docker', command_line)


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    # create the parser for the inspect command
    parser_inspect = subparsers.add_parser(
        'inspect',
        help='Starts a shell in the foreground inside your container to poke '
             'around the container.',
        parents=[common.container_parser()])
    parser_inspect.set_defaults(func=command_inspect)
    parser_inspect.add_argument(
        '-s',
        '--shell',
        help='Shell to use.',
        default='/bin/bash')
    parser_inspect.add_argument(
        '-d',
        '--submission',
        help='Submission directory to mount into the container.',
        type=common.arg_fq_dir)
    parser_inspect.add_argument(
        '--allow-network',
        action='store_true',
        help='Enable network access within the container. (Default off.)')
    parser_inspect.add_argument(
        '--unlimited-memory',
        action='store_true',
        help='Remove memory limits. (Default: limited memory.)')
    parser_inspect.add_argument(
        '--super-user',
        action='store_true',
        help='Inspect as super-user. (Default: userid 1000.)')
    parser_inspect.add_argument(
        '--no-rm',
        action='store_true',
        help="Do not clean up the container from the file system after exit.")
    return parser_inspect
