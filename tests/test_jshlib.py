from __future__ import unicode_literals
import unittest
import io

import jshlib


class TestLoadJsh(unittest.TestCase):
    def test_nums(self):
        s = io.StringIO("42 31 2.343")
        result = list(jshlib.load_jsh(s))
        expected = [42, 31, 2.343]
        assert expected == result

    def test_strs(self):
        data = '"hi" "b o"\n"LU"'
        s = io.StringIO(data)
        result = list(jshlib.load_jsh(s))
        expected = ["hi", "b o", 'LU']
        assert expected == result

    def test_escape(self):
        data = r'"hi\"U"'
        s = io.StringIO(data)
        result = list(jshlib.load_jsh(s))
        expected = ['hi"U']
        assert expected == result

    def test_list(self):
        data = r'''
        [1,2,3]
        ["yo", "bob"]
        '''
        s = io.StringIO(data)
        result = list(jshlib.load_jsh(s))
        expected = [
            [1,2,3],
            ["yo", "bob"],
        ]
        assert expected == result

    def test_list_embedded(self):
        data = r'''
        [1,2,[42,3]]
        ["yo", ["yo", "yo"]]
        '''
        s = io.StringIO(data)
        result = list(jshlib.load_jsh(s))
        expected = [
            [1,2,[42,3]],
            ["yo", ["yo", "yo"]],
        ]
        assert expected == result

    def test_object(self):
        data = r'''
        {
            "one": 1,
            "string": "foo",
            "bool": true,
            "list": [1,2,3]
        }
        '''
        s = io.StringIO(data)
        result = list(jshlib.load_jsh(s))
        expected = [
            {
                "one": 1,
                "string": "foo",
                "bool": True,
                "list": [1,2,3],
            },
        ]
        assert expected == result

