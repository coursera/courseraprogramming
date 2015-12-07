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
from courseraprogramming.commands import grade
from mock import MagicMock
from mock import patch
from testfixtures import LogCapture


def test_grade_local_parsing():
    # TODO: mock out `os.path.isdir` to make this test more portable.
    parser = main.build_parser()
    args = parser.parse_args('grade local myContainerId /tmp'.split())
    assert args.func == grade.command_grade_local
    assert args.containerId == 'myContainerId'
    assert args.dir == '/tmp'


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_bad_isCorrect(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"isCorrect":"true-string-is-not-true","feedback":"You win!"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
        ('root', 'ERROR', "Field 'isCorrect' is not a boolean value.")
    )
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_no_feedback(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"isCorrect":false, "not-feedback": "garbage"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
        ('root', 'ERROR', "Field 'feedback' not present in parsed output.")
    )
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_fractional_score_boolean(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore": false, "feedback": "wheeeee"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
        ('root', 'ERROR', "Field 'fractionalScore' must be a decimal.")
    )
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_fractional_score_string(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore": "0.3", "feedback": "wheeeee"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
        ('root', 'ERROR', "Field 'fractionalScore' must be a decimal.")
    )
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_fractional_score_too_high(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore":1.1, "feedback": "wheeeee"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
        ('root', 'ERROR', "Field 'fractionalScore' must be <= 1.")
    )
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_fractional_score_too_low(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore":-1.1, "feedback": "wheeeee"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
        ('root', 'ERROR', "Field 'fractionalScore' must be >= 0.")
    )
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_missing_grade(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"feedback": "wheeeee"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
        ('root', 'ERROR', "Required field 'fractionalScore' is missing.")
    )
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_malformed_output(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"isCorrect":false, "not-feedback": "garbageeeeeeee'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
        ('root', 'ERROR', "The output was not a valid JSON document.")
    )
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_bad_return_code(sys):
    with LogCapture():
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 1
        docker_mock.logs.side_effect = [
            'debug output',
            '{"isCorrect":true,"feedback":"You win!"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    sys.exit.assert_called_with(1)


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_good_output_is_correct(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"isCorrect":false, "feedback": "Helpful comment!"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
    )
    assert not sys.exit.called, "sys.exit should not be called!"


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_good_output_fractional_score(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore":0.2, "feedback": "Helpful comment!"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
    )
    assert not sys.exit.called, "sys.exit should not be called!"


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_good_output_fractional_score_one(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore":1, "feedback": "Helpful comment!"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
    )
    assert not sys.exit.called, "sys.exit should not be called!"


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_good_output_fractional_score_one_point_oh(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore":1.0, "feedback": "Helpful comment!"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
    )
    assert not sys.exit.called, "sys.exit should not be called!"


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_good_output_fractional_score_zero(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore":0, "feedback": "Helpful comment!"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
    )
    assert not sys.exit.called, "sys.exit should not be called!"


@patch('courseraprogramming.commands.grade.sys')
def test_check_output_good_output_fractional_score_zero_point_oh(sys):
    with LogCapture() as logs:
        docker_mock = MagicMock()
        container = {
            "Id": "myContainerId"
        }
        args = argparse.Namespace()
        args.timeout = 300

        docker_mock.wait.return_value = 0
        docker_mock.logs.side_effect = [
            '',
            '{"fractionalScore":0.0, "feedback": "Helpful comment!"}'
        ]
        # Run the function under test
        grade.run_container(docker_mock, container, args)
    logs.check(
        ('root', 'INFO', 'Debug log:'),
    )
    assert not sys.exit.called, "sys.exit should not be called!"


@patch('courseraprogramming.commands.grade.common')
@patch('courseraprogramming.commands.grade.utils')
@patch('courseraprogramming.commands.grade.run_container')
def test_command_local_grade_simple(run_container, utils, common):
    args = argparse.Namespace()
    args.dir = '/tmp'
    args.containerId = 'myContainerId'
    common.mk_submission_volume_str.return_value = 'foo'
    docker_mock = MagicMock()
    docker_mock.create_container.return_value = {
        "Id": "myContainerInstanceId",
    }
    utils.docker_client.return_value = docker_mock
    h_config = {'foo': 'bar'}  # just some unique value
    docker_mock.create_host_config.return_value = h_config

    grade.command_grade_local(args)

    docker_mock.create_container.assert_called_with(
        image='myContainerId',
        user='1000',
        host_config=h_config,
    )
    docker_mock.create_host_config.assert_called_with(
        binds=['foo', ],
        network_mode='none',
        mem_limit='1g',
        memswap_limit='1g',
    )
    run_container.assert_called_with(
        docker_mock,
        docker_mock.create_container.return_value,
        args)
