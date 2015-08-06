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

from courseraprogramming.commands import oauth2
import requests
import logging
import time
import sys


def check_auth(args):
    """
    Checks courseraprogramming's connectivity to the coursera.org API servers
    """
    oauth2_instance = oauth2.build_oauth2(args)
    auth = oauth2_instance.build_authorizer()
    my_profile_url = (
        'https://api.coursera.org/api/externalBasicProfiles.v1?'
        'q=me&fields=name'
    )
    r = requests.get(my_profile_url, auth=auth)
    if r.status_code != 200:
        logging.error('Received response code %s from the basic profile API.',
                      r.status_code)
        logging.debug('Response body:\n%s', r.text)
        sys.exit(1)
    try:
        external_id = r.json()['elements'][0]['id']
    except:
        logging.error(
            'Could not parse the external id out of the response body %s',
            r.text)
        external_id = None

    try:
        name = r.json()['elements'][0]['name']
    except:
        logging.error(
            'Could not parse the name out of the response body %s',
            r.text)
        name = None

    if not args.quiet > 0:
        print 'Name: %s' % name
        print 'External ID: %s' % external_id

    if name is None or external_id is None:
        sys.exit(1)


def display_auth_cache(args):
    '''
    Writes to the screen the state of the authentication cache. (For debugging
    authentication issues.) BEWARE: DO NOT email the output of this command!!!
    You must keep the tokens secure. Treat them as passwords.
    '''
    oauth2_instance = oauth2.build_oauth2(args)
    if not args.quiet > 0:
        token = oauth2_instance.token_cache['token']
        if not args.no_truncate and token is not None:
            token = token[:10] + '...'
        print "Auth token: %s" % token

        expires_time = oauth2_instance.token_cache['expires']
        expires_in = int((expires_time - time.time()) * 10) / 10.0
        print "Auth token expires in: %s seconds." % expires_in

        if 'refresh' in oauth2_instance.token_cache:
            refresh = oauth2_instance.token_cache['refresh']
            if not args.no_truncate and refresh is not None:
                refresh = refresh[:10] + '...'
            print "Refresh token: %s" % refresh
        else:
            print "No refresh token found."


def parser(subparsers):
    "Build an argparse argument parser to parse the command line."
    # create the parser for the configure subcommand. (authentication / etc.)
    parser_config = subparsers.add_parser(
        'configure',
        help='Configure %(prog)s for operation!')
    config_subparsers = parser_config.add_subparsers()

    # Local subsubcommand of the grade subcommand
    parser_check_auth = config_subparsers.add_parser(
        'check-auth',
        help=check_auth.__doc__)
    parser_check_auth.set_defaults(func=check_auth)

    parser_local_cache = config_subparsers.add_parser(
        'display-auth-cache',
        help=display_auth_cache.__doc__)
    parser_local_cache.set_defaults(func=display_auth_cache)
    parser_local_cache.add_argument(
        '--no-truncate',
        action='store_true',
        help='Do not truncate the keys [DANGER!!]')

    return parser_config
