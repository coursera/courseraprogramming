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
The grade subcommand executes the grader on a sample submission, simulating the
way it would run within Coursera's production environment.
"""

import argparse
from courseraprogramming.commands import common
from courseraprogramming import utils
import docker.utils
import json
import logging
from requests.exceptions import ReadTimeout
import sys


EXTRA_DOC = """
Beware: the Coursera Grid system uses a defense-in-depth strategy to protect
against security vulnerabilities. Some of these layers are not reproducible
outside of Coursera's environment.
"""


def run_container(docker, container, args):
    "Runs the prepared container (and therefore grader), checking the output"
    docker.start(container)
    try:
        exit_code = docker.wait(container, timeout=args.timeout)
    except ReadTimeout:
        logging.error("The grader did not complete within the required "
                      "timeout of %s seconds.", args.timeout)
        logging.debug("About to terminate the container: %s" % container)
        docker.kill(container)
        logging.debug("Successfully killed the container.")
        if not args.no_rm:
            logging.debug("Removing container...")
            docker.remove_container(container)
            logging.debug("Successfully cleaned up the container.")
        sys.exit(1)
    if exit_code != 0:
        logging.warn("The grade command did not exit cleanly within the "
                     "container. Exit code: %s", exit_code)

    if logging.getLogger().isEnabledFor(logging.INFO):
        stderr_output = docker.logs(container, stdout=False, stderr=True)
        logging.info('Debug log:')
        sys.stdout.write('-' * 80)
        sys.stdout.write('\n')
        sys.stdout.write(stderr_output)
        sys.stdout.write('-' * 80)
        sys.stdout.write('\n')

    stdout_output = docker.logs(container, stdout=True, stderr=False)
    error_in_grader_output = False
    try:
        parsed_output = json.loads(stdout_output)
    except ValueError:
        logging.error("The output was not a valid JSON document.")
        error_in_grader_output = True
    else:
        if "fractionalScore" in parsed_output:
            if isinstance(parsed_output['fractionalScore'], bool):
                logging.error("Field 'fractionalScore' must be a decimal.")
                error_in_grader_output = True
            elif not (isinstance(parsed_output['fractionalScore'], float) or
                      isinstance(parsed_output['fractionalScore'], int)):
                logging.error("Field 'fractionalScore' must be a decimal.")
                error_in_grader_output = True
            elif parsed_output['fractionalScore'] > 1:
                logging.error("Field 'fractionalScore' must be <= 1.")
                error_in_grader_output = True
            elif parsed_output['fractionalScore'] < 0:
                logging.error("Field 'fractionalScore' must be >= 0.")
                error_in_grader_output = True
        elif "isCorrect" in parsed_output:
            if not isinstance(parsed_output['isCorrect'], bool):
                logging.error("Field 'isCorrect' is not a boolean value.")
                error_in_grader_output = True
        else:
            logging.error("Required field 'fractionalScore' is missing.")
            error_in_grader_output = True
        if "feedback" not in parsed_output:
            logging.error("Field 'feedback' not present in parsed output.")
            error_in_grader_output = True
    finally:
        if logging.getLogger().isEnabledFor(logging.WARNING):
            sys.stdout.write('Grader output:\n')
            sys.stdout.write('=' * 80)
            sys.stdout.write('\n')
            sys.stdout.write(stdout_output)
            sys.stdout.write('=' * 80)
            sys.stdout.write('\n')
        if not args.no_rm:
            logging.debug("About to remove container: %s", container)
            docker.remove_container(container)
    if exit_code != 0 or error_in_grader_output:
        sys.exit(1)


class MemoryFormatError(BaseException):
    def __repr__(self):
        return "mem-limit must be a multiple of 1024."


def compute_memory_limit(args):
    """
    Convert the memory limit input into a format Docker expects. Raises an
    exception if it is of an unexpected value.
    """
    if args.mem_limit % 1024 == 0:
        return "%sg" % (args.mem_limit / 1024)
    else:
        raise MemoryFormatError()


def command_grade_local(args):
    """
    The 'local' sub-sub-command of the 'grade' sub-command simulates running a
    grader on a sample submission from the local file system.
    """
    d = utils.docker_client(args)
    memory_limit = compute_memory_limit(args)
    try:
        volume_str = common.mk_submission_volume_str(args.dir)
        logging.debug("Volume string: %s", volume_str)
        host_config = d.create_host_config(
                binds=[volume_str, ],
                network_mode='none',
                mem_limit=memory_limit,
                memswap_limit=memory_limit,
            )
        user = '%s' % 1000

        if 'args' in args and len(args.args) > 0:
            # Handle additional command-line arguments which will
            # be passed to the grader.
            inspect = d.inspect_image(image=args.imageId)
            cmd = inspect['Config']['Entrypoint']
            if not type(cmd) is list:
                logging.error('ENTRYPOINT in Dockerfile must be a list in ' +
                              'order to pass in command-line arguments')
                raise
            cmd.extend(args.args)
            container = d.create_container(
                image=args.imageId,
                entrypoint=cmd,
                user=user,
                host_config=host_config,
            )
        else:
            container = d.create_container(
                image=args.imageId,
                user=user,
                host_config=host_config,
            )
    except:
        logging.error(
            "Could not set up the container to run the grade command in. Most "
            "likely, this means that you specified an inappropriate container "
            "id.")
        raise
    run_container(d, container, args)


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    module_doc_string = sys.modules[__name__].__doc__
    # create the parser for the grade command
    parser_grade = subparsers.add_parser(
        'grade',
        description=module_doc_string + EXTRA_DOC,
        help=module_doc_string)

    common_flags = argparse.ArgumentParser(add_help=False)
    common_flags.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='The time out the grader after TIMEOUT seconds')
    common_flags.add_argument(
        '--mem-limit',
        type=int,
        default=1024,
        help='The amount of memory allocated to the grader')
    grade_subparsers = parser_grade.add_subparsers()

    # Local subsubcommand of the grade subcommand
    parser_grade_local = grade_subparsers.add_parser(
        'local',
        help=command_grade_local.__doc__,
        parents=[common_flags, common.container_parser()])

    parser_grade_local.set_defaults(func=command_grade_local)
    parser_grade_local.add_argument(
        '--no-rm',
        action='store_true',
        help='Do not clean up the container after grading completes.')
    parser_grade_local.add_argument(
        'dir',
        help='Directory containing the submission.',
        type=common.arg_fq_dir)
    parser_grade_local.add_argument(
        'args',
        nargs=argparse.REMAINDER,
        help='Arguments to the docker executable')
    return parser_grade
