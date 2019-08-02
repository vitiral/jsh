# jsh: json rpc shell commands

`jsh` refers to both:
 - JSH: a standard protocl for "shell scripts" to be able to talk to eachother
   in a manner similar to JSON-RPC
 - `jsh`: a cmdline tool for converting standard shell-like arguments
   into json.

The JSH spec is almost identical to the [JSON-RPC 2.0] specification. It is
a specification for cmdline programs to take a jsonrpc compatible json
blob via the argument `--jsh2-request` argument. i.e. if `ls` supported
JSH the following might have similar functionality:

```bash
ls --all /foo/bar

REQUEST='{
  "jsonrpc":"2.0",
  "method":"ls",
  "params":{"all":true, "path": "/foo/bar"}
}'
ls --jsh-request "$REQUEST"

ls --jsh-request $(jsh ls --all=true --path='"/foo/bar"')
```

In addition to this, JSH requires that when an applicaiton accepts a
`jsh-request` that it must (normally) output valid json on both stdout and
stderr -- enabling structured logging (from stderr) as well as json-typed
message passing between scripts.

The fundamental goal of this is to elminiate the error-prone parsing of system
outputs and enable more composability of developer tooling, both at the OS
level and higher -- while still allowing for fast development and prototyping.
This also allows for shell scripts to quickly be "hosted", acting as rpc
servers using an already defined interface.

[JSON-RPC 2.0]: https://www.jsonrpc.org/specification_v2
