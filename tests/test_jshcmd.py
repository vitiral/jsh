from __future__ import unicode_literals
import os
import unittest
import subprocess
import json
import jshlib

TESTS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TESTS)
JSH = os.path.join(REPO, 'bin', 'jsh')


def convert_stderr(stderr):
    errors = []
    for line in stderr.split('\n'):
        line = line.strip()
        if line:
            errors.append(json.loads(line))
    return errors



def call_jsh(args):
    args = [JSH] + args
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()

    return json.loads(stdout), convert_stderr(stderr)


class TestJsh(unittest.TestCase):
    def test_method(self):
        result, logs = call_jsh(['foo'])
        expected = jshlib.request('foo')
        assert expected == result
        assert [] == logs

    def test_simple_params(self):
        result, logs = call_jsh([
            'foo-bar',
            '--boolean=true',
            '--string="foo bar"',
            '--int=42',
            '--list=["one", 2, 3.0, [4], {"five": true}]',
        ])
        params = {
            "boolean": True,
            "string": "foo bar",
            "int": 42,
            "list": ["one", 2, 3.0, [4], {"five": True}],
        }
        expected = jshlib.request(method='foo-bar', params=params)
        assert expected == result
        assert [] == logs


