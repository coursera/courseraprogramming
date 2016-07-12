#!/usr/bin/env python

# Copyright 2016 Coursera
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

from courseraprogramming.commands.upload import register_grader
from courseraprogramming.commands.upload import setup_registration_parser
from courseraprogramming.commands.upload import update_assignments
from courseraprogramming.commands import common
from courseraprogramming.commands import oauth2
from courseraprogramming import utils

import json
import logging
import requests


def command_reregister(args):
    "Implements the reregister command."

    oauth2_instance = oauth2.build_oauth2(args)
    auth = oauth2_instance.build_authorizer()

    # retrieve the currentGraderId
    url = args.register_endpoint + '/' + args.currentGraderId
    result = requests.get(
        args.register_endpoint + '/' + args.currentGraderId,
        auth=auth)

    if result.status_code != 200:
        logging.error(
            'Unable to retrieve grader details with id! Code: %s',
            result.status_code)
        return 1

    try:
        s3bucket = result.json()['elements'][0]['bucket']
        s3key = result.json()['elements'][0]['key']
    except:
        logging.error(
            'Cannot parse the response from the grader details'
            'endpoint: %s', result.text)
        return 1

    grader_id = register_grader(auth, args, s3bucket, s3key)
    return update_assignments(auth, grader_id, args)


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."

    # create the parser for the upload command.
    parser_reregister = subparsers.add_parser(
        'reregister',
        help='Reregister an already uploaded created container')
    parser_reregister.set_defaults(func=command_reregister)

    parser_reregister.add_argument(
        'currentGraderId',
        help='The id of the grader already in the system which you want to '
        'reregister. The executorId is an double-length UUID in the form of '
        'Kvns6O3tQHuk5tBZc0DJOE~z8VsfYIYEeWxFFoymFg8zQ. '
        'You can get a list of ids for graders for a given course by querying '
        'the Executor Creation API '
        'https://api.coursera.org/api/gridExecutorCreationAttempts.v1?'
        'q=listByCourse&courseId=<<COURSEID>>')

    setup_registration_parser(parser_reregister)

    return parser_reregister
