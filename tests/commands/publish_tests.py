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

from courseraprogramming import main
from courseraprogramming.commands import publish

from mock import ANY
from mock import call
from mock import MagicMock
from mock import patch


class PublishParams:
    get_endpoint = "fake-endpoint"
    publish_endpoint = "fake-endpoint"
    publish_action = "fake-action"
    course = "2345"
    item = "3456"
    quiet = 1


def fake_get_metadata(oauth, get_endpoint, course_id, item_id):
    return {
        "version": 0,
        "authorId": 1234,
        "publishedAssignmentId": 4321,
        "updatedAt": 10000000,
    }


def test_called_with_metadata():
    publish.get_metadata = fake_get_metadata
    publish.post_publish = MagicMock()

    publish.command_publish(PublishParams)

    publish.post_publish.assert_called_with(
        ANY,
        "fake-endpoint",
        "fake-action",
        "2345",
        "3456",
        {
            "version": 0,
            "authorId": 1234,
            "publishedAssignmentId": 4321,
            "updatedAt": 10000000,
        }
    )


def test_multiple_items():
    publish.get_metadata = fake_get_metadata
    publish.post_publish = MagicMock()

    PublishParams.additional_items = ['4567', '5678']
    publish.command_publish(PublishParams)

    publish.post_publish.assert_has_calls([
        call(
            ANY,
            "fake-endpoint",
            "fake-action",
            "2345",
            "3456",
            {
                "version": 0,
                "authorId": 1234,
                "publishedAssignmentId": 4321,
                "updatedAt": 10000000,
            }
        ),
        call(
            ANY,
            "fake-endpoint",
            "fake-action",
            "2345",
            "4567",
            {
                "version": 0,
                "authorId": 1234,
                "publishedAssignmentId": 4321,
                "updatedAt": 10000000,
            }
        ),
        call(
            ANY,
            "fake-endpoint",
            "fake-action",
            "2345",
            "5678",
            {
                "version": 0,
                "authorId": 1234,
                "publishedAssignmentId": 4321,
                "updatedAt": 10000000,
            }
        )
    ])


@patch('courseraprogramming.commands.publish.sys')
def test_item_not_found_metadata(sys):
    def fake_get_metadata_throw(oauth, get_endpoint, course_id, item_id):
        raise publish.ItemNotFoundError(
            PublishParams.course, PublishParams.item)

    publish.get_metadata = fake_get_metadata_throw

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_internal_error_metadata(sys):
    def fake_get_metadata_throw(oauth, get_endpoint, course_id, item_id):
        raise publish.InternalError()

    publish.get_metadata = fake_get_metadata_throw

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_failed_validation(sys):
    def fake_post_publish(oauth, endpoint, action, course, item, metadata):
        raise publish.ValidationError()

    publish.get_metadata = fake_get_metadata
    publish.post_publish = fake_post_publish

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_pending_executor(sys):
    def fake_post_publish(oauth, endpoint, action, course, item, metadata):
        raise publish.GraderExecutorError(
            status=publish.GraderExecutorStatus.PENDING)

    publish.get_metadata = fake_get_metadata
    publish.post_publish = fake_post_publish

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.RETRYABLE_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_failed_executor(sys):
    def fake_post_publish(oauth, endpoint, action, course, item, metadata):
        raise publish.GraderExecutorError(
            status=publish.GraderExecutorStatus.FAILED)

    publish.get_metadata = fake_get_metadata
    publish.post_publish = fake_post_publish

    publish.command_publish(PublishParams)
    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_missing_executor(sys):
    def fake_post_publish(oauth, endpoint, action, course, item, metadata):
        raise publish.GraderExecutorError(
            status=publish.GraderExecutorStatus.MISSING)

    publish.get_metadata = fake_get_metadata
    publish.post_publish = fake_post_publish

    publish.command_publish(PublishParams)
    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_internal_error_publish(sys):
    def fake_post_publish(oauth, endpoint, action, course, item, metadata):
        raise publish.InternalError()

    publish.get_metadata = fake_get_metadata
    publish.post_publish = fake_post_publish

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_item_not_found_publish(sys):
    def fake_post_publish(oauth, endpoint, action, course, item, metadata):
        raise publish.ItemNotFoundError(
            PublishParams.course, PublishParams.item)

    publish.get_metadata = fake_get_metadata
    publish.post_publish = fake_post_publish

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


def test_get_executor_status_pending():
    resp_body = {
        "errorCode": "",
        "message": "",
        "details": [
            {
                "id": "",
                "bucket": "",
                "key": "",
                "status": "PENDING",
                "filename": "",
                "uploadedBy": 1,
                "uploadedAt": 1458001594555
            }
        ]
    }

    actual = publish.get_executor_status(resp_body)
    expected = publish.GraderExecutorStatus.PENDING

    assert actual == expected


def test_get_executor_status_failed():
    resp_body = {
        "errorCode": "",
        "message": "",
        "details": [
            {
                "id": "",
                "bucket": "",
                "key": "",
                "status": "FAILED",
                "filename": "",
                "uploadedBy": 1,
                "uploadedAt": 1458001594555
            }
        ]
    }

    actual = publish.get_executor_status(resp_body)
    expected = publish.GraderExecutorStatus.FAILED

    assert actual == expected


def test_get_executor_status_missing():
    resp_body = {
        "errorCode": "",
        "message": "",
        "details": [
            {
                "id": "",
                "bucket": "",
                "key": "",
                "status": "MISSING",
                "filename": "",
                "uploadedBy": 1,
                "uploadedAt": 1458001594555
            }
        ]
    }

    actual = publish.get_executor_status(resp_body)
    expected = publish.GraderExecutorStatus.MISSING

    assert actual == expected


def test_get_executor_status_none():
    resp_body = {
        "errorCode": "",
        "message": "",
        "details": {}
    }

    actual = publish.get_executor_status(resp_body)
    expected = None

    assert actual == expected


def test_publish_parsing():
    parser = main.build_parser()
    args = parser.parse_args('publish COURSE_ID ITEM_ID'.split())
    assert args.course == 'COURSE_ID'
    assert args.item == 'ITEM_ID'
    assert args.additional_items is None


def test_upload_parsing_with_additional_items():
    parser = main.build_parser()
    args = parser.parse_args('publish COURSE_ID ITEM_ID'.split() +
                             '--additional_items ITEM_2 ITEM_3 ITEM_4'.split())
    print args.additional_items
    assert args.additional_items == ['ITEM_2', 'ITEM_3', 'ITEM_4']
