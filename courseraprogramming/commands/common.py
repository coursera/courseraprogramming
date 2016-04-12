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
import os


def container_parser():
    "Build an argparse argument parser to parse the command line."

    # The following subcommands operate on a single containers. We centralize
    # all these options here.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        'imageId',
        help='The container image id or container tag to operate on.')

    return parser


def arg_fq_dir(dirname):
    """
    Verifies an argument refers to a directory on the file system, and converts
    it to a fully-qualified path.
    """
    if not os.path.isdir(dirname):
        msg = "%s is not a directory" % dirname
        # TODO: add some sanity checks if on boot2docker system to ensure that
        # the fully qualified path is somewhere within the /Users/$USER
        # directory (or equivalent on windows).
        raise argparse.ArgumentTypeError(msg)
    else:
        return os.path.abspath(os.path.expanduser(dirname))


def mk_submission_volume_str(fq_local_dir_name):
    "Converts a local fully-qualified path to a docker volume string"
    return '%s:/shared/submission' % fq_local_dir_name
