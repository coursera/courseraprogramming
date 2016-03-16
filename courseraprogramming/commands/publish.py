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

"""
Coursera's asynchronous grader command line SDK.

You may install it from source, or via pip.
"""

import logging
import requests
import sys

from courseraprogramming.commands import common
from courseraprogramming.commands import oauth2


class ErrorCodes():
    FATAL_ERROR = 1
    RETRYABLE_ERROR = 2


class GraderExecutorStatus():
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    MISSING = "MISSING"


class GraderExecutorError(Exception):

    def __init__(self, status):
        self.status = status


class ItemNotFoundError(Exception):

    def __init__(self, course_id, item_id):
        self.course_id = course_id
        self.item_id = item_id


class ValidationError(Exception):
    pass


class InternalError(Exception):
    pass


def command_publish(args):
    oauth2_instance = oauth2.build_oauth2(args)
    course_id = args.course
    item_ids = [args.item] + getattr(args, 'additional_items', [])
    for item_id in item_ids:
        try:
            metadata = get_metadata(
                oauth2_instance, args.get_endpoint, course_id, item_id)
            post_publish(
                oauth2_instance,
                args.publish_endpoint,
                args.publish_action,
                course_id,
                item_id,
                metadata)
        except ItemNotFoundError as e:
            sys.exit(ErrorCodes.FATAL_ERROR)
        except ValidationError as e:
            sys.exit(ErrorCodes.FATAL_ERROR)
        except GraderExecutorError as e:
            if e.status == GraderExecutorStatus.PENDING:
                sys.exit(ErrorCodes.RETRYABLE_ERROR)
            elif e.status == GraderExecutorStatus.FAILED:
                sys.exit(ErrorCodes.FATAL_ERROR)
            elif e.status == GraderExecutorStatus.MISSING:
                sys.exit(ErrorCodes.FATAL_ERROR)
        except InternalError as e:
            sys.exit(ErrorCodes.FATAL_ERROR)


def get_metadata(oauth2_instance, get_endpoint, course_id, item_id):
    auth = oauth2_instance.build_authorizer()
    resp = requests.get(
        '{}/{}~{}'.format(get_endpoint, course_id, item_id),
        auth=auth)
    print resp.status_code
    if resp.status_code == 404:
        raise ItemNotFoundError(course_id, item_id)
    elif resp.status_code == 500:
        raise InternalError()
    return resp.json()['elements'][0]['metadata']


def post_publish(
        oauth2_instance,
        publish_endpoint,
        publish_action,
        course_id,
        item_id,
        metadata):

    auth = oauth2_instance.build_authorizer()
    params = {
        "action": publish_action,
        "id": "{}~{}".format(course_id, item_id)
    }
    resp = requests.post(
        publish_endpoint, params=params, json=metadata, auth=auth)
    print resp.status_code
    if resp.status_code == 400:
        status = get_executor_status(resp.json())
        if status is None:
            raise ValidationError()
        else:
            raise GraderExecutorError(status)
    elif resp.status_code == 404:
        raise ItemNotFoundError(course_id, item_id)
    elif resp.status_code in (409, 500):
        raise InternalError()


def get_executor_status(resp_body):
    try:
        return resp_body['details'][0]['status']
    except KeyError:
        return None


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    # create the parser for the publish command.
    parser_publish = subparsers.add_parser(
        'publish',
        help='Publish ALL changes made to a programming assignment.')

    parser_publish.set_defaults(func=command_publish)

    parser_publish.add_argument(
        'course',
        help='The id of the course containing the assignment to publish.')

    parser_publish.add_argument(
        'item',
        help='The id of the assignment to publish.')

    parser_publish.add_argument(
        '--additional_item',
        action='append',
        help='The next two args specify an item ID which will also be '
             'published.')

    parser_publish.add_argument(
        '--get-endpoint',
        default='https://api.coursera.org/api/'
                'authoringProgrammingAssignments.v1',
        help='Override the endpoint used to get the assignment (draft)')

    parser_publish.add_argument(
        '--publish-endpoint',
        default='https://api.coursera.org/api/'
                'authoringProgrammingAssignments.v1',
        help='Override the endpoint used to publish the assignment (draft)')

    parser_publish.add_argument(
        '--publish-action',
        default='publish',
        help='The name of the Naptime action used to publish the assignment')

    return parser_publish
