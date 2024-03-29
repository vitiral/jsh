from __future__ import unicode_literals
import os
import unittest
import subprocess
import json
import jshlib
from pprint import pprint

TESTS = os.path.dirname(os.path.abspath(__file__))
ECHO = os.path.join(TESTS, 'echo')
REPO = os.path.dirname(TESTS)
JSH = os.path.join(REPO, 'bin', 'jsh')


def convert_stderr(stderr):
    errors = []
    for line in stderr.split(b'\n'):
        line = line.strip()
        if line:
            errors.append(json.loads(line))
    return errors


def call_jsh(args):
    args = [JSH] + args
    env = {
        "PYTHONPATH": "{}:{}".format(REPO, os.environ.get("PYTHONPATH", ""))
    }

    p = subprocess.Popen(args,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         env=env)

    stdout, stderr = p.communicate()

    logs = convert_stderr(stderr)
    result = json.loads(stdout)

    return p.returncode, result, logs


def error_pop_data_logs(error):
    return error.pop(jshlib.DATA)['errors']


class TestJsh(unittest.TestCase):
    def test_method(self):
        rc, result, logs = call_jsh(['method=foo'])
        expected = jshlib.request('foo')
        assert expected == result
        assert [] == logs
        assert rc == 0

    def test_simple_params(self):
        rc, result, logs = call_jsh([
            'm=foo-bar',
            '--boolean=true',
            '--string="foo bar"',
            '--int=42',
            '--list=["one", 2, 3.0, [4], {"five": true}]',
        ])
        params = {
            "boolean": True,
            "string": "foo bar",
            "int": 42,
            "list": ["one", 2, 3.0, [4], {
                "five": True
            }],
        }
        expected = jshlib.request(method='foo-bar', params=params)
        assert expected == result
        assert [] == logs
        assert rc == 0

    def test_no_method_error(self):
        rc, result, logs = call_jsh([
            '--boolean=true',
        ])

        expected_logs = [
            {
                'lvl': 'ERROR',
                'msg': 'no method found'
            },
        ]

        expected = {
            jshlib.CODE: jshlib.Error.INVALID_PARAMS,
            jshlib.MESSAGE: 'errors encountered when parsing arguments',
        }
        result_logs = error_pop_data_logs(result)

        assert expected == result
        assert expected_logs == result_logs
        assert expected_logs == logs
        assert rc == 1

    def test_extra_methods_error(self):
        rc, result, logs = call_jsh([
            'm=one',
            'm=two',
            'm=three',
        ])

        expected_logs = [
            {
                'lvl': 'ERROR',
                'msg': 'Found a extra method specified: two'
            },
            {
                'lvl': 'ERROR',
                'msg': 'Found a extra method specified: three'
            },
        ]

        expected = {
            jshlib.CODE: jshlib.Error.INVALID_PARAMS,
            jshlib.MESSAGE: 'errors encountered when parsing arguments',
        }
        result_logs = error_pop_data_logs(result)

        assert expected == result
        assert expected_logs == result_logs
        assert expected_logs == logs
        assert rc == 1

    def test_overlapping_params_error(self):
        rc, result, logs = call_jsh([
            'm=method',
            '--boolean=true',
            '--boolean=false',
        ])

        expected_logs = [
            {
                'lvl': 'ERROR',
                'msg': 'found at least two params with same key: boolean'
            },
        ]

        expected = {
            jshlib.CODE: jshlib.Error.INVALID_PARAMS,
            jshlib.MESSAGE: 'errors encountered when parsing arguments',
        }
        result_logs = error_pop_data_logs(result)

        assert expected == result
        assert expected_logs == result_logs
        assert expected_logs == logs
        assert rc == 1

    def test_bad_json_error(self):
        rc, result, logs = call_jsh([
            'method=method',
            '--bad=\'foo\'',
        ])

        expected_logs = [
            {
                'lvl':
                'ERROR',
                'msg':
                "param 'bad' with value=<'foo'> did not parse:" +
                " No JSON object could be decoded",
            },
        ]

        expected = {
            jshlib.CODE: jshlib.Error.INVALID_PARAMS,
            jshlib.MESSAGE: 'errors encountered when parsing arguments',
        }
        result_logs = error_pop_data_logs(result)

        assert expected == result
        assert expected_logs == result_logs
        assert expected_logs == logs
        assert rc == 1


class TestRunJsh(unittest.TestCase):
    def test_echo_method_only(self):
        request = jshlib.Request("echo")
        returncode, outputs, logs = jshlib.run_jsh(ECHO, request.method)

        assert [] == outputs
        assert [request.serialize()] == logs
        assert 0 == returncode

    def test_echo_all(self):
        request = jshlib.Request("echo", {"testing": "true"})
        inputs = ["foo"]
        returncode, outputs, logs = jshlib.run_jsh(
            ECHO, request.method, request.params, inputs=inputs
        )

        assert ["foo"] == outputs
        assert [request.serialize()] == logs
        assert 0 == returncode
