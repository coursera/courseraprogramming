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

from courseraprogramming.commands import common
from courseraprogramming.commands import oauth2
from courseraprogramming import utils
import json
import logging
import multiprocessing
import os.path
import re
import requests
import sys
import time
import uuid


def authorize_upload(args, auth):
    "Retrieves a signature to authenticate the transloadit upload."
    # Signatures not currently required for this upload.
    pass


def get_container_image(args, d):
    '''
    Saves the container image to the file system in tar form. (similar to the
    `docker save` command.)

    Returns the name of the file containing the export.
    '''
    # TODO: get information on the image, and run a few basic sanity checks.
    # (e.g. check for ENTRYPOINT, etc.)

    image = d.get_image(args.containerId)
    image_file_name = \
        args.containerId if args.file_name is None else args.file_name
    image_file_name = image_file_name.replace('/', '_')
    if not image_file_name.endswith('.tar'):
        image_file_name += '.tar'
    logging.debug('Image file name: %s', image_file_name)
    image_file_path = os.path.join(args.temp_dir, image_file_name)
    logging.debug('Image file path: %s', image_file_path)
    if not args.quiet > 0:
        sys.stdout.write(
            'Saving image %s to %s...' % (args.containerId, image_file_path))
        sys.stdout.flush()
    with open(image_file_path, 'w') as image_tar:
        image_tar.write(image.data)
    if not args.quiet > 0:
        sys.stdout.write(' done.\n')
        sys.stdout.flush()
    return (image_file_path, image_file_name)


def idle_transloadit_server(args):
    result = requests.get('https://api2.transloadit.com/instances/bored')
    if result.status_code != 200:
        logging.error('Transloadit board instance API failure. Code: %s',
                      result.status_code)
        raise Exception('TransloadIt bored instances API failure.')

    if result.json()['ok'] != 'BORED_INSTANCE_FOUND':
        logging.error(
            'TransloadIt bord instances API did not find a bored instance. %s',
            result.json())
        raise Exception('No Bored Transloadit instance found.')
    return result.json()['host']


def upload(args, upload_url, file_info):
    '''
    The long-running upload request. This runs in a separate process for
    concurrency reasons.
    '''
    with open(file_info[0], 'rb') as image_file:
        files = [
            ('file', (file_info[1], image_file, 'application/x-tar')),
        ]
        transloadit_auth_info = {
            'auth': {
                'key': args.transloadit_account_id,
            },
            'template_id': args.transloadit_template,
        }
        params = json.dumps(transloadit_auth_info)
        logging.debug('About to start the upload.')
        response = requests.post(upload_url,
                                 files=files,
                                 data={'params': params})
        logging.debug('Upload complete... code: %s %s', response.status_code,
                      response.text)


def poll_transloadit(args, upload_url):
    """
    Polls Transloadit's API to determine the status of the upload. Outputs
    information to stdout (unless suppressed). Raises an exception if there is
    an error, returns tuple of response information when complete, and None
    otherwise
    """
    if args.upload_to_requestbin:
        logging.info('Skipping polling transloadit...')
        return
    response = requests.get(upload_url)
    logging.debug(response.text)
    # TODO: return True if we're done. Throw an exception if there's an error.
    if response.status_code != 200:
        logging.error('Polling API returned non-200 code. Response body: %s',
                      response.text)
        raise Exception('Non-200 status code returned from polling API.')
    if 'error' in response.json():
        logging.error('Upload encountered an error: %s --- %s',
                      response.json()['error'], response.text)
        raise Exception('Upload in an error state. :-(')
    if 'ok' in response.json():
        body = response.json()
        stage = body['ok']
        if stage == 'ASSEMBLY_UPLOADING':
            progress = float(body['bytes_received']) / body['bytes_expected']
            if not args.quiet > 0:
                sys.stdout.write("\rUploading... %(progress)s%% complete." % {
                    'progress': int(progress * 100),
                })
                sys.stdout.flush()
            return None
        elif stage == 'ASSEMBLY_EXECUTING':
            if not args.quiet > 0:
                sys.stdout.write(
                    "\rTransloadIt is processing... (typically < 2 min)")
                sys.stdout.flush()
            return None
        elif stage == 'ASSEMBLY_COMPLETED':
            if not args.quiet > 1:
                sys.stdout.write("\rAssembly upload complete.\n")
                sys.stdout.flush()
            try:
                s3_link = body['results'][':original'][0]['ssl_url']
            except:
                logging.error(
                    'Could not parse the upload link from the transloadit '
                    'response: %s',
                    body)
                raise Exception('Error parsing the transloadit response.')
            else:
                match = re.match('https://([^\\.]+).s3.amazonaws.com/(.+)',
                                 s3_link)
                if match is None:
                    logging.error(
                        'Could not parse the uploaded url correctly. URL: %s',
                        s3_link)
                    raise Exception('Error parsing the upload url!')
                return (match.group(1), match.group(2))


def lookup_course_information(args, auth):
    'Lookups up a course to get the course id / name / etc.'
    if re.match('[A-z0-9_-]{22}', args.course):
        logging.debug('Requesting course info based on id.')
        # Assume they passed us a course id.
        course_response = requests.get(
            '%s/%s' % (args.course_info_endpoint, args.course),
            auth=auth)
    else:
        # Assume they passed us a course slug.
        logging.debug('Requesting course info based on slug.')
        params = {
            'q': 'slug',
            'slug': args.course
        }
        course_response = requests.get(
            args.course_info_endpoint,
            params=params,
            auth=auth)
    logging.debug('Course response body: %s', course_response.text)
    if course_response.status_code != 200:
        logging.error(
            'Could not look up the course. %s',
            course_response.text)
        raise Exception('Failed to find course on coursera.')
    try:
        course = course_response.json()['elements'][0]
        args.course_id = course['id']
        args.course_slug = course['slug']
    except:
        logging.exception(
            'Error while handling the response from the course info '
            'endpoint. Response body: %s',
            course_response.text)
        raise


def output_courtesy_link(args):
    if not args.quiet > 0:
        sys.stdout.write(
            'Edit assignment descriptions, passing thresholds, and publish '
            'the new course grader at:\n\t')
        courtesy_link_path = '/teach/%(slug)s/author/programming/%(item)s/' % {
            'slug': args.course_slug,
            'item': args.item
        }
        courtesy_link = 'https://www.coursera.org' + courtesy_link_path
        sys.stdout.write(courtesy_link)
        sys.stdout.write('\n')
        sys.stdout.flush()


def command_upload(args):
    "Implements the upload subcommand"
    d = utils.docker_client(args)
    image = get_container_image(args, d)

    oauth2_instance = oauth2.build_oauth2(args)
    auth = oauth2_instance.build_authorizer()
    lookup_course_information(args, auth)
    # TODO: use transloadit's signatures for upload signing.
    # authorization = authorize_upload(args, auth)

    # Generate a random uuid for upload.
    upload_id = uuid.uuid4().hex
    transloadit_host = idle_transloadit_server(args)
    upload_url = 'https://%(host)s/assemblies/%(id)s' % {
        'host': transloadit_host,
        'id': upload_id,
    }
    if args.upload_to_requestbin is not None:
        upload_url = 'http://requestb.in/%s' % args.upload_to_requestbin

    if not args.quiet > 0:
        sys.stdout.write(
            'About to upload to server:\n\t%(transloadit_host)s\n'
            'with upload id:\n\t%(upload_id)s\nStatus API:\n'
            '\t%(upload_url)s\nUploading...' % {
                'transloadit_host': transloadit_host,
                'upload_id': upload_id,
                'upload_url': upload_url,
            })
        sys.stdout.flush()
    p = multiprocessing.Process(target=upload, args=(args, upload_url, image))
    p.daemon = True  # Auto-kill when the main process exits.
    p.start()
    time.sleep(10)  # Yield control to the child process to kick off upload.

    upload_information = None

    while p.is_alive():
        upload_information = poll_transloadit(args, upload_url)
        if upload_information is not None:
            logging.warn(
                'Upload information retrieved before upload completed??! %s',
                upload_information)
            break
        time.sleep(10)  # 10 seconds

    p.join(1)  # Join to clean up zombie.

    # TODO: make time waiting for transloadit to finish processing configurable
    for i in xrange(300):
        upload_information = poll_transloadit(args, upload_url)
        if upload_information is not None:
            break
        time.sleep(5)

    if upload_information is None:
        logging.error(
            'Upload did not complete within expected time limits. Upload '
            'URL: %s',
            upload_url)
        return 1
    # Register the grader with Coursera to initiate the image cleaning process
    logging.debug('Grader upload info is: %s', upload_information)

    # Rebuild an authorizer to ensure it's fresh and not expired
    auth = oauth2_instance.build_authorizer()
    register_request = {
        'courseId': args.course_id,
        'bucket': upload_information[0],
        'key': upload_information[1],
    }
    logging.debug('About to POST data to register endpoint: %s',
                  json.dumps(register_request))
    register_result = requests.post(
        args.register_endpoint,
        data=json.dumps(register_request),
        auth=auth)
    if register_result.status_code != 201:  # Created
        logging.error(
            'Failed to register grader (%s) with Coursera: %s',
            upload_information[1],
            register_result.text)
        return 1

    try:
        grader_id = register_result.json()['elements'][0]['executorId']
        location = register_result.headers['location']
    except:
        logging.exception(
            'Could not parse the response from the Coursera register grader '
            'endpoint: %s',
            register_result.text)
        return 1

    logging.info('The grader status API is at: %s', location)

    update_assignment_params = {
        'action': args.update_part_action,
        'id': '%s~%s' % (args.course_id, args.item),
        'partId': args.part,
        'executorId': grader_id,
    }
    update_result = requests.post(
        args.update_part_endpoint,
        params=update_assignment_params,
        auth=auth)
    if update_result.status_code != 200:
        logging.error(
            'Unable to update the assignment to use the new grader. Param: %s '
            'URL: %s Response: %s',
            update_assignment_params,
            update_result.url,
            update_result.text)
        return 1
    logging.info('Successfully updated assignment part %s to new executor %s',
                 args.part, grader_id)
    output_courtesy_link(args)
    return 0


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    # create the parser for the upload command.
    parser_upload = subparsers.add_parser(
        'upload',
        help='Upload a container to Coursera.',
        parents=[common.container_parser()])
    parser_upload.set_defaults(func=command_upload)

    parser_upload.add_argument(
        'course',
        help='The course id to associate the grader.')

    parser_upload.add_argument(
        'item',
        help='The id of the item to associate the grader.')

    parser_upload.add_argument(
        'part',
        help='The id of the part to associate the grader.')

    parser_upload.add_argument(
        '--temp-dir',
        default='/tmp',
        help='Temporary directory to use when exporting the container.')

    parser_upload.add_argument(
        '--file-name',
        help='File name to use when saving the docker container image. '
             'Defaults to the name of the container image.')

    parser_upload.add_argument(
        '--upload-to-requestbin',
        help='Pass the ID of a request bin to debug uploads!')

    parser_upload.add_argument(
        '--transloadit-template',
        default='7531c0b023f611e5aa2ecf267b4b90ee',
        help='The transloadit template to upload to.')

    parser_upload.add_argument(
        '--transloadit-account-id',
        default='05912e90e83346abb96c261bf458b615',
        help='The Coursera transloadit account id.')

    parser_upload.add_argument(
        '--register-endpoint',
        default='https://api.coursera.org/api/gridExecutorCreationAttempts.v1',
        help='Override the endpoint used to register the graders after upload')

    parser_upload.add_argument(
        '--update-part-endpoint',
        default='https://api.coursera.org/api/'
                'authoringProgrammingAssignments.v1',
        help='Override the endpoint used to update the assignment (draft)')

    parser_upload.add_argument(
        '--update-part-action',
        default='setGridExecutorId',
        help='The name of the Naptime action called to update the assignment')

    parser_upload.add_argument(
        '--course-info-endpoint',
        default='https://api.coursera.org/api/onDemandCourses.v1',
        help='Override the endpoint used to look up course information.')

    return parser_upload
