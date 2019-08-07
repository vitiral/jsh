# jsh: JSON-RPC standards for the shell
#
# Copyright (C) 2019 Rett Berg <github.com/vitiral>
#
# The source code is Licensed under either of
#
# * Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or
#   http://www.apache.org/licenses/LICENSE-2.0)
# * MIT license ([LICENSE-MIT](LICENSE-MIT) or
#   http://opensource.org/licenses/MIT)
#
# at your option.
#
# Unless you explicitly state otherwise, any contribution intentionally submitted
# for inclusion in the work by you, as defined in the Apache-2.0 license, shall
# be dual licensed as above, without any additional terms or conditions.
"""
jsh: JSON-RPC standards for the shell
"""
# pylint: disable=invalid-name,too-few-public-methods

from __future__ import unicode_literals
import sys
import json
import subprocess
import traceback
import io

ARGV_JSH_REQUEST = '--jsh-request'

CODE = 'code'
DATA = 'data'
METHOD = 'method'
MESSAGE = 'message'
JSONRPC = 'jsonrpc'
JSONRPC_VALUE = '2.0'
PARAMS = 'params'

INFO = 'INFO'
ERROR = 'ERROR'

_DIGITS = {str(n) for n in range(10)}
_DIGITS.add('.')
_CURLY = {'{', '}'}
_BRACKET = {'[', ']'}

def run_jsh(cmd, method, params, inputs=None):
    """Run a Jsh process, blocking until it is complete.

    `inputs` can be a list of serializable values to dump into the stream.

    Returns (returncode, outputs, logs)

    rc: integer return code
    outputs: list of python objects from stdout
    logs: list of python objects from stderr
    """

    p = PopenJsh.run_jsh(cmd=cmd, method=method, params=params)
    outputs, logs = p.communicate(inputs=inputs)
    return p.returncode, outputs, logs


class PopenJsh(subprocess.Popen):
    """Run a Jsh process in the background using Popen.

    Use the `run_jsh` classmethod to start it, or construct your own Popen.

    This is similar to Popen but provides a generator for reading the logs and
    data.

    TODO:
    Currently this only provides the `communicate` method. Eventually it might
    implement the generator interface (in python3 only).
    """
    @classmethod
    def run_jsh(cls,
                cmd,
                method,
                params,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **kwargs):
        r = request(method=method, params=params)
        args = [cmd, "--jsh-request={}".format(json.dumps(r))]

        return cls(args=args,
                   stdin=stdin,
                   stderr=stderr,
                   stdout=stdout,
                   **kwargs)

    def communicate(self, inputs=None):
        """Communicate with the jsh process, returning the deserialized
        stdout, stderr.

        `inputs` can be a list of serializable values to dump into the stream.
        """

        if inputs:
            strinput = b'\n'.join(json.dumps(v) for v in inputs)
        else:
            strinput = None

        stdout, stderr = super(PopenJsh, self).communicate(strinput)

        outputs = load_json_iter(stdout)
        logs = load_json_iter(stderr)
        return outputs, logs



def parse_jsh_argv(argv):
    """Attempt to parse the argv for a ``--jsh-request=<json rpc>``

    returns: Request if the request exists, Error if it is an Error,
      or None if --jsh-request does not exist.
    raise: ValueError if the request is invalid.
    """
    for arg in argv:
        if arg.startswith(ARGV_JSH_REQUEST):
            _, reqstr = arg.split('=', 1)
            return parse_jsh_request(reqstr)

    return None


def parse_jsh_request(reqstr):
    """Attempt to parse a string as a JSON-RPC object.

    returns: Request if the request exists, Error if it is an Error.
    raise: ValueError if the request is invalid.
    """
    req = json.loads(reqstr)
    if METHOD in req:
        jsonrpc_value = req.get(JSONRPC, JSONRPC_VALUE)
        if jsonrpc_value != JSONRPC_VALUE:
            raise ValueError("Invalid jsonrpc value: {}".format(jsonrpc_value))
        return Request(method=req[METHOD], params=req.get(PARAMS))

    if CODE in req:
        code = req[CODE]
        if MESSAGE not in req:
            raise ValueError("Error must have message: {}".format(
                repr(reqstr)))
        message = req[MESSAGE]
        data = req.get(DATA)
        return Error(code=code, message=message, data=data)

    raise ValueError("Unknown json blob: {}".format(repr(reqstr)))


class Serializable:
    """An object that can call serialize() to be json serializable."""

    # pylint: disable=no-self-use
    def serialize(self):
        """Convert to basic python types."""
        raise TypeError("Must override serialize")


class Request(Serializable):
    """Standard JSON-RPC Request object."""
    def __init__(self, method, params):
        self.method = method
        self.params = params

    def serialize(self):
        """Convert to basic python types."""
        return request(method=self.method, params=self.params)


class Error(Exception, Serializable):
    """JSON-RPC error.

    Can also be used to construct a python error for JSON-RPC.
    """
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    def __init__(self, code, message, data):
        super(Error, self).__init__(message)
        self.code = code
        self.message = message
        self.data = data

    @classmethod
    def internal_exc(cls, exc, tb=True):
        """Create an internal error, possibly from another exc.

        If tb, the exception traceback will be added as ``data``.
        """
        data = None
        message = repr(exc)
        if tb:
            data = traceback.format_exc().split('\n')
        return cls(code=cls.INTERNAL_ERROR, message=message, data=data)

    def serialize(self):
        return error(code=self.code, message=self.message, data=self.data)


def request(method, params=None):
    """Create a standard JSON-RPC Request object."""
    payload = {
        JSONRPC: "2.0",
        METHOD: method,
    }

    if params:
        payload["params"] = params

    return payload


def error(code, message, data=None):
    """Create a standard JSON-RPC Error object."""
    return {
        CODE: code,
        MESSAGE: message,
        DATA: data,
    }


def log(msg, lvl=ERROR):
    """Log the message at appropriate lvl to stderr and return the object."""
    payload = log_payload(msg, lvl=lvl)
    dump_stderr(payload)
    return payload


def log_payload(msg, lvl=None, data=None):
    """Create a standard log payload object."""
    lvl = ERROR if lvl is None else lvl
    out = {'lvl': lvl, "msg": msg}
    if data:
        out['data'] = data
    return out


def dump_stdout(payload):
    """Dump a python object to stdout as json with a newline."""
    if isinstance(payload, Serializable):
        payload = payload.serialize()
    sys.stdout.write(json.dumps(payload))
    sys.stdout.write('\n')


def dump_stderr(payload):
    """Dump a python object to stderr as json with a newline."""
    if isinstance(payload, Serializable):
        payload = payload.serialize()
    sys.stderr.write(json.dumps(payload))
    sys.stderr.write('\n')


def load_json_iter(stream):
    """Iteratively load json objects from a stream.
    """
    if isinstance(stream, str):
        stream = io.StringIO(stream)

    for slist in _load_json_striter(stream):
        valuestr = ''.join(slist)
        value = json.loads(valuestr)
        yield value


# pylint: disable=too-many-statements
# pylint: disable=too-many-branches
def _load_json_striter(stream):
    """Load jsh strings from a stream."""
    alltext = []

    ignore_next = False
    open_curly = False
    open_bracket = False
    open_string = False
    is_digits = False
    brackets = 0

    def consolodate_result(alltext, text, i):
        """Consolodate the result into alltext and return what was excluded."""
        include, text = text[:i + 1], text[i + 1:]
        alltext.append(include)
        return text, 0

    for text in stream:
        i = 0
        while i < len(text):
            c = text[i]

            if ignore_next:
                ignore_next = False
            elif c == '\\':
                ignore_next = True
            elif is_digits is True and c not in _DIGITS:
                # We found a Number
                text, i = consolodate_result(alltext, text, i)
                yield alltext
                alltext = []
                is_digits = False
                continue
            elif c == '"':
                if not (open_curly or open_bracket):
                    if open_string:
                        # We found a String
                        text, i = consolodate_result(alltext, text, i)
                        yield alltext
                        alltext = []
                        open_string = False
                        continue

                open_string = not open_string

            elif c in _DIGITS and not (open_string or open_bracket
                                       or open_curly):
                is_digits = True

            elif c in _BRACKET and not (open_string or open_curly):
                if c == '[':
                    open_bracket = True
                    brackets += 1
                elif c == ']':
                    brackets -= 1
                    if brackets == 0:
                        # We found a List
                        text, i = consolodate_result(alltext, text, i)
                        yield alltext
                        alltext = []
                        open_bracket = False
                        continue

            elif c in _CURLY and not (open_string or open_bracket):
                if c == '{':
                    open_curly = True
                    brackets += 1
                elif c == '}':
                    brackets -= 1
                    if brackets == 0:
                        # We found an Object
                        text, i = consolodate_result(alltext, text, i)
                        yield alltext
                        alltext = []
                        open_curly = False
                        continue

            i += 1

        if text.strip():
            alltext.append(text)

    if alltext:
        yield alltext
