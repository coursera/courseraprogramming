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
import docker
from courseraprogramming import main
from courseraprogramming.commands import cat
from mock import MagicMock
from mock import patch


def test_cat_parsing():
    parser = main.build_parser()
    args = parser.parse_args('cat imageId /root/foo bar /bar/baz'.split())
    assert args.func == cat.command_cat
    assert args.imageId == 'imageId'
    assert args.file == ['/root/foo', 'bar', '/bar/baz']


@patch('courseraprogramming.commands.cat.utils')
def test_ls_run(utils):

    docker_mock = MagicMock(spec=docker.Client)
    docker_mock.create_container.return_value = {
        u'Id': u'really-long-container-id-hash',
        u'Warnings': None
    }
    docker_mock.wait.return_value = 0
    docker_mock.logs.return_value = "1231\n1241\n41211"
    utils.docker_client.return_value = docker_mock

    # Set up args
    args = argparse.Namespace()
    args.imageId = 'testImageId'
    args.file = '/grader/testCases.txt'

    with patch('courseraprogramming.commands.cat.sys.stdout') as stdout:
        # Run the command
        cat.command_cat(args)

    # Verify correct command output
    stdout.write.assert_called_with(docker_mock.logs.return_value)

    docker_mock.create_container.assert_called_with(
        image='testImageId',
        entrypoint='/bin/cat',
        command='/grader/testCases.txt')
    docker_mock.start.assert_called_with(
        docker_mock.create_container.return_value)
    docker_mock.logs.assert_called_with(
        docker_mock.create_container.return_value)
