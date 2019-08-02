from __future__ import unicode_literals

def request(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
    }

    if params:
        payload["params"] = params

    return payload


def error(code, message, data=None):
    return {
        "code": code,
        "message": message,
        "data": data,
    }

