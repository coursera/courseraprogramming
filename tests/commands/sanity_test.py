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
from courseraprogramming.commands import sanity
from mock import mock_open, patch
from testfixtures import LogCapture


# Set up mocking of the `open` call. See http://www.ichimonji10.name/blog/6/
from sys import version_info
if version_info.major == 2:
    import __builtin__ as builtins  # pylint:disable=import-error
else:
    import builtins  # pylint:disable=import-error


def test_command_sanity():
    "Test generator to test a number of different sanity cases"
    testCases = [
        ("general1", [
            "FROM ubuntu:latest\n",
            "\n",
            "COPY foo foo\n"], (
            ('root', 'INFO', 'Line 0: We recommend using debian, or other '
                'smaller base images.'),
            ('root', 'WARNING', 'Line 2: Copy destination should always start '
                'with a /.'),
            ('root', 'WARNING', 'Your Dockerfile must define an ENTRYPOINT.'),
            )),
        ("doubleEntrypoint", [
            "FROM debian\n",
            "\n",
            "ENTRYPOINT /grader.sh\n",
            "ENTRYPOINT /other_grader.sh"], (
            ('root', 'WARNING', 'Line 3: Re-defining entrypoint of '
                'container.'),)),
        ("bash_entrypoint", [
            "FROM debian\n",
            "\n",
            "ENTRYPOINT /bin/bash"], (
            ('root', 'WARNING', 'Line 2: Please mark your grading script or '
                'binary as the ENTRYPOINT, and not bash'),)),
    ]
    for testcase in testCases:
        testFn = command_sanity_impl
        testFn.description = 'test_command_sanity: %s' % testcase[0]
        print ":LKJSDF:LSKJDF:LSJKDF:LKSJ:DFLKJSD:LFKJL:JE"
        print "Test name: %s, input: %s, output: %s" % testcase
        yield testFn, testcase[1], testcase[2]


def command_sanity_impl(dockerFile, expectedLogs):
    print "TESTING %s WITH %s" % (dockerFile, expectedLogs)
    with LogCapture() as logs:
        open_ = mock_open(read_data=''.join(dockerFile))
        open_().readlines.return_value = dockerFile
        with patch.object(builtins, 'open', open_, create=True):
            args = argparse.Namespace()
            args.docker_file = "."
            args.skip_environment = True
            sanity.command_sanity(args)
            logs.check(*expectedLogs)


def test_sanity_parsing():
    parser = main.build_parser()
    args = parser.parse_args('sanity'.split())
    assert args.func == sanity.command_sanity
