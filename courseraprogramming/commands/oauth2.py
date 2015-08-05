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

'''
Helpers for working with OAuth2 / etc.
'''

import BaseHTTPServer
import ConfigParser
import cPickle
import logging
import requests
import io
import os
import subprocess
import sys
import time
import urlparse
import uuid
from sys import platform as _platform


def configuration():
    'Loads configuration from the file system.'
    defaults = '''
[oauth2]
client_id = NS8qaSX18X_Eu0pyNbLsnA
client_secret = bUqKqGywnGXEJPFrcd4Jpw
hostname = localhost
port = 9876
api_endpoint = https://api.coursera.org
auth_endpoint = https://accounts.coursera.org/oauth2/v1/auth
token_endpoint = https://accounts.coursera.org/oauth2/v1/token
scope = view_profile manage_graders
verify_tls = True
token_cache = ~/.coursera/oauth2_cache.pickle

[upload]
transloadit_bored_api = https://api2.transloadit.com/instances/bored
'''
    cfg = ConfigParser.SafeConfigParser()
    cfg.readfp(io.BytesIO(defaults))
    cfg.read([
        '/etc/coursera/courseraprogramming.cfg',
        os.path.expanduser('~/.coursera/courseraprogramming.cfg'),
        'courseraprogramming.cfg',
    ])
    return cfg


class ExpiredToken(Exception):
    def __init__(self, oauth2Auth):
        self.oauth2Auth = oauth2Auth

    def __str__(self):
        return 'Attempt to use expired token. Expired at: %s.' % \
            self.oauth2Auth.expires


class OAuth2Exception(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'OAuth2 Protocol Exception: %(msg)s' % {
            'msg': self.msg,
        }


class CourseraOAuth2Auth(requests.auth.AuthBase):
    'Attaches OAuth2 access tokens to requests.'

    def __init__(self, token, expires):
        self.token = token
        self.expires = expires

    def is_valid(self):
        'Determines if this authorizer is still valid.'
        return time.time() < self.expires

    def __call__(self, request):
        if self.is_valid():
            logging.debug('About to add an authorization header!')
            request.headers['Authorization'] = 'Bearer %(token)s' % {
                'token': self.token
            }
            return request
        else:
            logging.error(
                'Attempt to use expired Authorizer. Expired: %s, now: %s',
                self.expires, time.time())
            raise ExpiredToken(self)


class CodeHolder:
    '''
    A helper class to hold a token.

    '''

    def __init__(self):
        self.code = None

    def __call__(self, code):
        self.code = code

    def has_code(self):
        return self.code is not None


def make_handler(state_token, done_function):
    '''
    Makes a a handler class to use inside the basic python HTTP server.

    state_token is the expected state token.
    done_function is a function that is called, with the code passed to it.
    '''

    class LocalServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):

        def error_response(self, msg):
            logging.warn(
                'Error response: %(msg)s. %(path)s',
                msg=msg,
                path=self.path)
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(msg)

        def do_GET(self):
            parsed = urlparse.urlparse(self.path)
            if len(parsed.query) == 0 or parsed.path != '/callback':
                self.error_response(
                    'We encountered a problem with your request.')
                return

            params = urlparse.parse_qs(parsed.query)
            if params['state'] != [state_token]:
                self.error_response(
                    'Attack detected: state tokens did not match!')
                return

            if len(params['code']) != 1:
                self.error_response('Wrong number of "code" query parameters.')
                return

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(
                "courseraprogramming: we have captured Coursera's response "
                "code. Feel free to close this browser window now and return "
                "to your terminal. Thanks!")
            done_function(params['code'][0])

    return LocalServerHandler


def _compute_cache_filename(args, cfg):
    'Compute the cache file name.'
    try:
        return os.path.expanduser(args.token_cache)
    except:
        return os.path.expanduser(cfg.get('oauth2', 'token_cache'))


def _check_cache_types(cache_value, strict=False):
    '''
    Checks the cache_value for appropriate type correctness.

    Pass strict=True for strict validation to ensure the latest types are being
    written.

    Returns true is correct type, False otherwise.
    '''
    def check_string_value(name):
        return isinstance(cache_value[name], str) or \
            isinstance(cache_value[name], unicode)

    def check_refresh_token():
        if 'refresh' in cache_value:
            return check_string_value('refresh')
        else:
            return True

    return \
        isinstance(cache_value, dict) and \
        'token' in cache_value and \
        'expires' in cache_value and \
        check_string_value('token') and \
        isinstance(cache_value['expires'], float) and \
        check_refresh_token()


def _read_fs_cache(args, cfg):
    'Reads the local fs cache for pre-authorized access tokens'
    filename = _compute_cache_filename(args, cfg)
    try:
        logging.debug('About to read from local file cache file %s', filename)
        with open(filename, 'rb') as f:
            fs_cached = cPickle.load(f)
            if _check_cache_types(fs_cached):
                return fs_cached
            else:
                logging.warn('Found unexpected value in cache. %s', fs_cached)
                return None
    except IOError:
        logging.debug(
            'Did not find file: %s on the file system.', filename)
        return None
    except:
        logging.info(
            'Encountered exception loading from the file system.',
            exc_info=True)
        return None


def _write_fs_cache(cache_value, args, cfg):
    'Write out to the filesystem a cache of the OAuth2 information.'
    logging.debug('Looking to write to local authentication cache...')
    if not _check_cache_types(cache_value, strict=True):
        logging.error('Attempt to save a non-dict value: %s', cache_value)
        return
    filename = _compute_cache_filename(args, cfg)
    try:
        logging.debug('About to write to fs cache file: %s', filename)
        with open(filename, 'wb') as f:
            cPickle.dump(cache_value, f, protocol=cPickle.HIGHEST_PROTOCOL)
            logging.debug('Finished dumping cache_value to fs cache file.')
    except:
        logging.exception(
            'Could not successfully cache OAuth2 secrets on the file system.')


def _build_redirect_uri(cfg):
    return 'http://%(hostname)s:%(port)s/callback' % {
        'hostname': cfg.get('oauth2', 'hostname'),
        'port': cfg.get('oauth2', 'port')
    }


def _build_authorizaton_url(state_token, args, cfg):
    authorization_request = requests.Request(
        'GET',
        cfg.get('oauth2', 'auth_endpoint'),
        params={
            'access_type': 'offline',
            'response_type': 'code',
            'client_id': cfg.get('oauth2', 'client_id'),
            'redirect_uri': _build_redirect_uri(cfg),
            'scope': cfg.get('oauth2', 'scope'),
            'state': state_token,
        }).prepare()

    logging.debug('Constructed authoriation request at: %s',
                  authorization_request.url)
    return authorization_request.url


def _request_tokens_from_token_endpoint(form_data, args, cfg):
    token_endpoint = cfg.get('oauth2', 'token_endpoint')
    logging.debug(
        'Posting form data %s to token endpoint %s',
        form_data,
        token_endpoint)
    response = requests.post(
        token_endpoint,
        data=form_data,
        verify=cfg.getboolean('oauth2', 'verify_tls'),
        timeout=10,
    )

    logging.debug(
        'Response from token endpoint: (%s) %s',
        response.status_code,
        response.text)

    if response.status_code != 200:
        logging.error(
            'Encountered unexpected status code: %s %s %s',
            response.status_code,
            response,
            response.text)
        raise OAuth2Exception('Unexpected status code from token endpoint')

    body = response.json()
    if 'access_token' not in body or 'expires_in' not in body:
        logging.error('Malformed / missing fields in body. %(body)s',
                      body=body)
        raise OAuth2Exception('Malformed response body from token endpoint.')

    if 'token_type' not in body or body['token_type'].lower() != 'bearer':
        logging.error('Unknown token_type encountered: %s', body['token_type'])
        raise OAuth2Exception('Unknown token_type encountered.')

    expires_time = time.time() + body['expires_in']
    access_token = body['access_token']
    tokens = {
        'token': access_token,
        'expires': expires_time,
    }

    if 'refresh_token' in body:
        refresh = body['refresh_token']
        if isinstance(refresh, str) or isinstance(refresh, unicode):
            tokens['refresh'] = refresh
    return tokens


def _authorize_new_tokens(args, cfg):
    '''
    Stands up a new localhost http server and retrieves new OAuth2 access
    tokens from the Coursera OAuth2 server.
    '''
    logging.info('About to request new OAuth2 tokens from Coursera.')
    fs_cache = _read_fs_cache(args, cfg)
    if fs_cache is not None and 'refresh_token' in fs_cache:
        # TODO: attempt to use refresh token.
        pass
    # Attempt to request new tokens from Coursera via the browser.
    state_token = uuid.uuid4().hex
    authorization_url = _build_authorizaton_url(state_token, args, cfg)

    sys.stdout.write('Please visit the following URL to authorize this app:\n')
    sys.stdout.write('\t%s\n\n' % authorization_url)
    if _platform == 'darwin':
        # OS X -- leverage the 'open' command present on all modern macs
        sys.stdout.write('Mac OS X detected; attempting to auto-open the url '
                         'in your default browser...\n')
        try:
            subprocess.check_call(['open', authorization_url])
        except:
            logging.exception('Could not call `open %(url)s`.',
                              url=authorization_url)

    # Boot up a local webserver to retrieve the response.
    server_address = ('', cfg.getint('oauth2', 'port'))
    code_holder = CodeHolder()

    local_server = BaseHTTPServer.HTTPServer(
        server_address,
        make_handler(state_token, code_holder))

    while not code_holder.has_code():
        local_server.handle_request()

    form_data = {
        'code': code_holder.code,
        'client_id': cfg.get('oauth2', 'client_id'),
        'client_secret': cfg.get('oauth2', 'client_secret'),
        'redirect_uri': _build_redirect_uri(cfg),
        'grant_type': 'authorization_code',
    }
    return _request_tokens_from_token_endpoint(form_data, args, cfg)


def _exchange_refresh_tokens(fs_cache, args, cfg):
    'Exchanges a refresh token for an access token'
    if 'refresh' in fs_cache:
        # Attempt to use the refresh token to get a new access token.
        refresh_form = {
            'grant_type': 'refresh_token',
            'refresh_token': fs_cache['refresh'],
            'client_id': cfg.get('oauth2', 'client_id'),
            'client_secret': cfg.get('oauth2', 'client_secret'),
        }
        try:
            return _request_tokens_from_token_endpoint(refresh_form, args, cfg)
        except OAuth2Exception:
            logging.exception(
                'Encountered an exception during refresh token flow.')
    return None


def build_authorizer(args, cfg):
    '''
    Returns a python requests Authorizer that should work for at least 5
    minutes from the time this function returns.
    '''
    fs_cache = _read_fs_cache(args, cfg)
    logging.debug('read local fs cache... Found: %s', fs_cache)
    if fs_cache is not None and (time.time() + 5 * 60) < fs_cache['expires']:
        logging.debug('Found valid value in local fs cache.')
        return CourseraOAuth2Auth(fs_cache['token'], fs_cache['expires'])
    new_token = _exchange_refresh_tokens(fs_cache, args, cfg)
    if new_token is None:
        logging.info(
            'Attempting to retrieve new tokens from the endpoint. You will be '
            'prompted to authorize the courseraprogramming app in your web '
            'browser.')
        new_token = _authorize_new_tokens(args, cfg)
    logging.debug("New token: %s", new_token)
    _write_fs_cache(new_token, args, cfg)
    return CourseraOAuth2Auth(new_token['token'], new_token['expires'])
