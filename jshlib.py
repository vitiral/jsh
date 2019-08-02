from __future__ import unicode_literals
import sys
import json
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



def parse_jsh_argv(argv):
    """Attempt to parse the argv for a ``--jsh-request=<json rpc>``

    returns: Request if the request exists or None if it does not.
    raise: ValueError if the request is invalid.
    """
    for arg in argv:
        if arg.startswith(ARGV_JSH_REQUEST):
            _, reqstr = arg.split('=', 1)
            return parse_jsh_request(reqstr)

    return None


def parse_jsh_request(reqstr):
    req = json.loads(reqstr)
    if METHOD in req:
        jsonrpc_value = req.get(JSONRPC, JSONRPC_VALUE)
        if jsonrpc_value != JSONRPC_VALUE:
            raise ValueError("Invalid jsonrpc value: {}".format(jsonrpc_value))
        params = req.get(PARAMS)
        return Request(method=method, params=params)
    elif CODE in req:
        code = req[CODE]
        if MESSAGE not in req:
            raise ValueError("Error must have message: {}".format(repr(reqstr)))
        message = req[MESSAGE]
        data = req.get(DATA)
        return Error(code=code, message=message, data=data)
    else:
        raise ValueError("Unknown json blob: {}".format(repr(reqstr)))



def request(method, params=None):
    payload = {
        JSONRPC: "2.0",
        METHOD: method,
    }

    if params:
        payload["params"] = params

    return payload


def error(code, message, data=None):
    return {
        CODE: code,
        MESSAGE: message,
        DATA: data,
    }


class Serializable:
    def serialize(self):
        raise TypeError("Must override serialize")


class Request(Serializable):
    def __init__(self, method, params):
        self.method = method
        self.params = params

    def serialize(self):
        return request(method=self.method, params=self.params)


class Error(Exception, Serializable):
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


def log(msg, lvl=ERROR):
    """Log the message at appropriate lvl to stderr and return the object."""
    payload = log_payload(msg, lvl=lvl)
    dump_stderr(payload)
    return payload


def log_payload(msg, lvl=None, data=None):
    lvl = ERROR if lvl is None else lvl
    out = {'lvl': lvl, "msg": msg}
    if data:
        out['data'] = data
    return out


def load_jsh(socket):
    """Iteratively load jsh objects from a socket.
    """
    for slist in _load_jsh_strlist(socket):
        valuestr = ''.join(slist)
        value = json.loads(valuestr)
        yield value


def _load_jsh_strlist(socket):
    """Load jsh strings from a socket."""
    alltext = []

    ignore_next = False
    open_curly = False
    open_bracket = False
    open_string = False
    is_digits = False
    brackets = 0

    def consolodate_result(alltext, text, i):
        """Consolodate the result into alltext and return what was excluded."""
        include, text = text[:i+1], text[i+1:]
        alltext.append(include)
        return text, 0


    # import pdb; pdb.set_trace()
    for text in socket:
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

            elif c in _DIGITS and not (open_string or open_bracket or open_curly):
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



def dump_stderr(payload):
    if isinstance(payload, Serializable):
        payload = payload.serialize()
    sys.stderr.write(json.dumps(payload))
    sys.stderr.write('\n')


def dump_stdout(payload):
    if isinstance(payload, Serializable):
        payload = payload.serialize()
    sys.stdout.write(json.dumps(payload))
    sys.stdout.write('\n')
