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

from courseraprogramming import main
from courseraprogramming import utils
import logging

# Set up mocking of the `open` call. See http://www.ichimonji10.name/blog/6/
from sys import version_info
if version_info.major == 2:
    import builtins as builtins  # pylint:disable=import-error
else:
    import builtins  # pylint:disable=import-error


def test_chattiness_parsing_quiet():
    parser = main.build_parser()
    args = parser.parse_args('-qq version'.split())
    assert args.quiet == 2


def test_chattiness_parsing_verbose():
    parser = main.build_parser()
    args = parser.parse_args('-v version'.split())
    assert args.verbose == 1


def test_set_logging_level():
    parser = main.build_parser()
    args = parser.parse_args('-vv version'.split())
    utils.set_logging_level(args)
    assert logging.getLogger().getEffectiveLevel() == 5  # "Trace"


def test_set_logging_level_noneSpecified():
    parser = main.build_parser()
    args = parser.parse_args('version'.split())
    utils.set_logging_level(args)
    assert logging.getLogger().getEffectiveLevel() == logging.INFO or \
        logging.getLogger().getEffectiveLevel() == logging.NOTSET


def test_set_timeout():
    parser = main.build_parser()
    args = parser.parse_args('--timeout 120 version'.split())
    assert args.timeout == 120


def test_no_timeout():
    parser = main.build_parser()
    args = parser.parse_args('version'.split())
    assert args.timeout == 60
