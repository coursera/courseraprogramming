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

from courseraprogramming.commands import oauth2

import argparse
import ConfigParser
from mock import MagicMock
import time


def test_compute_cache_filename_args_override():
    args = argparse.Namespace()
    args.token_cache = '/tmp/cache'
    cfg = ConfigParser.ConfigParser()
    cfg.add_section('oauth2')
    cfg.set('oauth2', 'token_cache', '/tmp/not_cache')
    assert oauth2._compute_cache_filename(args, cfg) == '/tmp/cache'


def test_compute_cache_filename():
    args = argparse.Namespace()
    cfg = ConfigParser.ConfigParser()
    cfg.add_section('oauth2')
    cfg.set('oauth2', 'token_cache', '/tmp/configured_cache')
    assert oauth2._compute_cache_filename(args, cfg) == '/tmp/configured_cache'


def test_compute_cache_filname_expanded_path():
    args = argparse.Namespace()
    cfg = ConfigParser.ConfigParser()
    cfg.add_section('oauth2')
    cfg.set('oauth2', 'token_cache', '~/.coursera/oauth2_cache.pickle')
    computed = oauth2._compute_cache_filename(args, cfg)
    assert '~' not in computed, 'Computed contained "~": %s' % computed


def test_compute_cache_filname_expanded_path_overrides():
    args = argparse.Namespace()
    args.token_cache = '~/.coursera/override_cache.pickle'
    cfg = ConfigParser.ConfigParser()
    cfg.add_section('oauth2')
    cfg.set('oauth2', 'token_cache', '~/.coursera/oauth2_cache.pickle')
    computed = oauth2._compute_cache_filename(args, cfg)
    assert '~' not in computed, 'Computed contained "~": %s' % computed
    assert 'override_cache.pickle' in computed, 'Computed was not override!'


def test_check_cache_types():
    # test cases are tuples of:
    # (name, cache_value, expected_strict, expected_non_strict)
    test_cases = [
        ('basic dict', {}, False, False),
        ('basic array', [], False, False),
        ('basic int', 3, False, False),
        ('populated dict', {'token': 'asdfg', 'expires': 12345.0}, True, True)
    ]
    for test_case in test_cases:
        check_cache_types_impl.description = \
            'test_check_cache_types: %s (strict)' % test_case[0]
        yield check_cache_types_impl, test_case[1], True, test_case[2]

        check_cache_types_impl.description = \
            'test_check_cache_types: %s (non-strict)' % test_case[0]
        yield check_cache_types_impl, test_case[1], False, test_case[3]


def check_cache_types_impl(
        cache_type,
        strict_validation,
        should_be_allowed):
    result = oauth2._check_cache_types(cache_type, strict=strict_validation)
    assert result == should_be_allowed, \
        'Got %(result)s. Expected: %(expected)s' % {
            'result': result,
            'expected': should_be_allowed,
        }


def test_load_configuration():
    cfg = oauth2.configuration()
    assert cfg.get('oauth2', 'hostname') == 'localhost', 'hostname incorrect'
    assert cfg.getint('oauth2', 'port') == 9876, 'oauth2.port not correct'
    assert cfg.get('oauth2', 'api_endpoint') == 'https://api.coursera.org', \
        'oauth2.api_endpoint incorrect'
    assert cfg.getboolean('oauth2', 'verify_tls'), 'oauth2.verify_tls wrong'
    assert cfg.get('upload', 'transloadit_bored_api') == \
        'https://api2.transloadit.com/instances/bored', 'transloadit bored API'


def test_expired_token_serialization():
    authorizer = oauth2.CourseraOAuth2Auth(token='asdf', expires=time.time())
    exception = oauth2.ExpiredToken(authorizer)
    assert len("%s" % exception) > 0


def test_authorizer_throws_when_expired():
    authorizer = oauth2.CourseraOAuth2Auth(token='asdf',
                                           expires=time.time()-10)
    fake_request = MagicMock()
    try:
        authorizer(fake_request)
    except oauth2.ExpiredToken:
        pass
    else:
        assert False, 'authorizer should have thrown an exception'


def test_authorizer_does_not_throw_when_not_expired():
    authorizer = oauth2.CourseraOAuth2Auth(token='asdf',
                                           expires=time.time()+10)
    fake_request = MagicMock()
    authorizer(fake_request)


def test_build_authorization_url():
    args = argparse.Namespace()
    cfg = ConfigParser.ConfigParser()
    cfg.add_section('oauth2')
    cfg_values = [
        ('auth_endpoint', 'https://accounts.coursera.org/oauth2/v1/auth'),
        ('client_id', 'my_fake_client_id'),
        ('hostname', 'localhost'),
        ('port', '9876'),
        ('scope', 'view_profile manage_graders'),
    ]
    for (key, value) in cfg_values:
        cfg.set('oauth2', key, value)

    state_token = 'my_fake_state_token'

    actual = oauth2._build_authorizaton_url(
        state_token,
        args,
        cfg)

    expected_url = (
        'https://accounts.coursera.org/oauth2/v1/auth?'
        'access_type=offline&'
        'state=my_fake_state_token&'
        'redirect_uri=http%3A%2F%2Flocalhost%3A9876%2Fcallback&'
        'response_type=code&'
        'client_id=my_fake_client_id&'
        'scope=view_profile+manage_graders'
    )

    assert expected_url == actual, 'Got unexpected URL: %s' % actual
