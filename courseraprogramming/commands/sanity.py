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

from dockerfile_parse import DockerfileParser
from courseraprogramming import utils
import logging
import semver


def command_sanity(args):
    "Implements the sanity subcommand"
    # Sanity check should:
    #   - Check docker versions
    #   - Check for existance of entrypoint (that isn't /bin/bash)
    #   - Check over copy commands // make sure they look reasonable.
    #   - Check the entrypoint if it's a shell script for keywords like "sudo"
    #     or chroot.
    if not args.skip_environment:
        logging.info("Checking local docker demon...")
        conn = utils.docker_client(args)
        docker_version = conn.version()
        logging.info("Docker version: %s", docker_version["Version"])
        if semver.match(docker_version["Version"], '>1.5.0'):
            logging.info("Docker version ok.")
        else:
            logging.error("Docker version must be >1.5.0.")

    if "docker_file" in args and args.docker_file is not None:
        try:
            docker_file = DockerfileParser(args.docker_file)
        except:
            logging.error("Could not parse Dockerfile at: %s",
                          args.docker_file)
        else:
            structure = docker_file.structure
            seen_entrypoint = False
            for cmd in structure:
                if cmd['instruction'].lower() == 'copy':
                    if not cmd['value'].startswith('/'):
                        logging.warn(
                            'Line %(lineno)s: Copy destination should always '
                            'start with a /.', {
                                "lineno": cmd['startline'],
                            })
                if cmd['instruction'].lower() == 'from':
                    if "ubuntu" in cmd['value']:
                        logging.info(
                            'Line %(lineno)s: We recommend using '
                            'debian, or other smaller base images.', {
                                "lineno": cmd['startline'],
                            })
                if cmd['instruction'].lower() == 'entrypoint':
                    if seen_entrypoint:
                        logging.warn(
                            'Line %(lineno)s: Re-defining entrypoint '
                            'of container.', {
                                "lineno": cmd['startline'],
                            })
                    seen_entrypoint = True
                    if 'bash' in cmd['value']:
                        logging.warn(
                            'Line %(lineno)s: Please mark your grading script '
                            'or binary as the ENTRYPOINT, and not bash', {
                                'lineno': cmd['startline'],
                            })
                if cmd['instruction'].lower() == 'expose':
                    logging.warn(
                        'Line %(lineno)s: EXPOSE commands do not work for '
                        'graders', {
                            'lineno': cmd['startline'],
                        })
                if cmd['instruction'].lower() == 'env':
                    logging.warn(
                        'Line %(lineno)s: ENV-based environment variables are '
                        'stripped in the production environment for security '
                        'reasons. Please set any environment variables you '
                        'need in your grading script.', {
                            'lineno': cmd['startline'],
                        })
                if cmd['instruction'].lower() == 'volume':
                    logging.warn(
                        'Line %(lineno)s: VOLUME commands are stripped in '
                        'the production environment, and will likely not work '
                        'as expected.', {
                            'lineno': cmd['startline'],
                        })
            if not seen_entrypoint:
                logging.warn('Your Dockerfile must define an ENTRYPOINT.')
    else:
        logging.info("No Dockerfile provided... skipping file checks.")


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."

    # create the parser for the sanity check command
    parser_sanity = subparsers.add_parser(
        'sanity',
        help='Run a number of sanity checks over the environment.')
    parser_sanity.set_defaults(func=command_sanity)
    parser_sanity.add_argument(
        '--skip-environment',
        action='store_true',
        help='Skip host / environment checks.')
    parser_sanity.add_argument(
        '-f',
        '--docker-file',
        help='The docker file to check.')

    return parser_sanity
