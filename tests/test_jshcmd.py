import os
import unittest
import subprocess

TESTS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TESTS)
JSH = os.path.join(REPO, 'bin', 'jsh')


def call_jsh(args):
    args = [JSH] + args
    p = Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.communicate()



