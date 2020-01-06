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
    course = "course2345"
    item = "item3456"
    write_access_token = "token4567"
    authoring_pa_id = "{}~{}".format(course, item)
    quiet = 1
    additional_items = None
    config = None
    docker_url = None
    verbose = None


def fake_get_write_access_token(oauth, get_endpoint, authoring_pa_id):
    return "token4567"


def fake_get_authoring_pa_id(oauth, course_id, item_id):
    return "{}~{}".format(course_id, item_id)


# def fake_get_authoring_pa_id_item(oauth, course_id, item_id):
#     return authoring_pa_id_item


# def fake_get_authoring_pa_id_atom(oauth, course_id, item_id):
#     return authoring_pa_id_atom


def test_called_with_write_access_token():
    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = MagicMock()

    publish.command_publish(PublishParams)

    publish.publish_item.assert_called_with(
        ANY,
        "fake-endpoint",
        "fake-action",
        "course2345~item3456",
        "token4567"
    )


def test_multiple_items():
    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = MagicMock()

    PublishParams.additional_items = ['item4567', 'item5678']
    publish.command_publish(PublishParams)
    PublishParams.additional_items = None

    publish.publish_item.assert_has_calls([
        call(
            ANY,
            "fake-endpoint",
            "fake-action",
            "course2345~item3456",
            "token4567"
        ),
        call(
            ANY,
            "fake-endpoint",
            "fake-action",
            "course2345~item4567",
            "token4567"
        ),
        call(
            ANY,
            "fake-endpoint",
            "fake-action",
            "course2345~item5678",
            "token4567"
        )
    ])


@patch('courseraprogramming.commands.publish.sys')
def test_item_not_found_metadata(sys):
    def fake_get_token_throw(oauth, get_endpoint, authoring_pa_id):
        raise publish.ItemNotFoundError(
            PublishParams.authoring_pa_id)

    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_token_throw

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_internal_error_metadata(sys):
    def fake_get_token_throw(oauth, get_endpoint, authoring_pa_id):
        raise publish.InternalError()

    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_token_throw

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_failed_validation(sys):
    def fake_publish_item(oauth, endpoint, action, authoring_pa_id, token):
        raise publish.ValidationError()

    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = fake_publish_item

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_pending_executor(sys):
    def fake_publish_item(oauth, endpoint, action, authoring_pa_id, token):
        raise publish.GraderExecutorError(
            status=publish.GraderExecutorStatus.PENDING)

    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = fake_publish_item

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.RETRYABLE_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_failed_executor(sys):
    def fake_publish_item(oauth, endpoint, action, authoring_pa_id, token):
        raise publish.GraderExecutorError(
            status=publish.GraderExecutorStatus.FAILED)

    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = fake_publish_item

    publish.command_publish(PublishParams)
    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_missing_executor(sys):
    def fake_publish_item(oauth, endpoint, action, authoring_pa_id, token):
        raise publish.GraderExecutorError(
            status=publish.GraderExecutorStatus.MISSING)

    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = fake_publish_item

    publish.command_publish(PublishParams)
    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_internal_error_publish(sys):
    def fake_publish_item(oauth, endpoint, action, authoring_pa_id, token):
        raise publish.InternalError()

    publish.get_authoring_pa_id = fake_get_authoring_pa_id
    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = fake_publish_item

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_item_not_found_publish(sys):
    def fake_publish_item(oauth, endpoint, action, authoring_pa_id, token):
        raise publish.ItemNotFoundError(
            PublishParams.authoring_pa_id)

    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = fake_publish_item

    publish.command_publish(PublishParams)

    sys.exit.assert_called_with(publish.ErrorCodes.FATAL_ERROR)


@patch('courseraprogramming.commands.publish.sys')
def test_assignment_not_ready_publish(sys):
    def fake_publish_item(oauth, endpoint, action, authoring_pa_id, token):
        raise publish.ProgrammingAssignmentDraftNotReadyError(
            PublishParams.authoring_pa_id)

    publish.get_write_access_token = fake_get_write_access_token
    publish.publish_item = fake_publish_item

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
                             '--additional-items ITEM_2 ITEM_3 ITEM_4'.split())
    print(args.additional_items)
    assert args.additional_items == ['ITEM_2', 'ITEM_3', 'ITEM_4']
