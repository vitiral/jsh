from __future__ import unicode_literals
import sys
import json
import traceback


CODE = 'code'
DATA = 'data'
METHOD = 'method'
MESSAGE = 'message'
JSONRPC = 'jsonrpc'
JSONRPC_VALUE = '2.0'
PARAMS = 'params'

INFO = 'INFO'
ERROR = 'ERROR'

def parse_jsh_argv(argv):
    """Attempt to parse the argv for a ``--jsh_request=<json rpc>``

    returns: Request if the request exists or None if it does not.
    raise: ValueError if the request is invalid.
    """
    for arg in argv:
        if arg.startswith('--jsh_request='):
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
