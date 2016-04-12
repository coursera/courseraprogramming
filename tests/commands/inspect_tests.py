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

import argparse
from courseraprogramming import main
from courseraprogramming.commands import inspect
from mock import patch


def test_inspect_parsing():
    parser = main.build_parser()
    args = parser.parse_args('inspect demo/primes'.split())
    assert args.func == inspect.command_inspect
    assert args.imageId == 'demo/primes'
    assert not args.no_rm


@patch('courseraprogramming.commands.inspect.os')
def test_ls_run(os):

    # Set up args
    args = argparse.Namespace()
    args.imageId = 'testImageId'
    args.shell = '/bin/bash'
    args.allow_network = False
    args.unlimited_memory = False
    args.super_user = False
    args.no_rm = False

    # Run the command
    inspect.command_inspect(args)

    # Verify correct command output
    os.execvp.assert_called_with('docker', [
        'docker',
        'run',
        '-it',
        '--entrypoint',
        '/bin/bash',
        '--net',
        'none',
        '-m',
        '1g',
        '--rm',
        '-u',
        '1000',
        'testImageId',
    ])


@patch('courseraprogramming.commands.inspect.os')
def test_ls_run_without_limits(os):

    # Set up args
    args = argparse.Namespace()
    args.imageId = 'testImageId'
    args.shell = '/bin/bash'
    args.allow_network = True
    args.unlimited_memory = True
    args.super_user = True
    args.no_rm = True

    # Run the command
    inspect.command_inspect(args)

    # Verify correct command output
    os.execvp.assert_called_with('docker', [
        'docker',
        'run',
        '-it',
        '--entrypoint',
        '/bin/bash',
        'testImageId',
    ])
