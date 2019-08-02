# jsh: json rpc shell commands

`jsh` refers to both:
 - JSH: a standard protocl for "shell scripts" to be able to talk to eachother
   in a manner similar to JSON-RPC, along with a `jshlib.py` single-file python
   library.
 - `jsh`: a cmdline tool for converting standard shell-like arguments
   into json.

The JSH spec is almost identical to the [JSON-RPC 2.0] specification. It is
a specification for cmdline programs to take a jsonrpc compatible json
blob via the argument `--jsh-request` argument. i.e. if `ls` supported
JSH the following might have similar functionality:

```bash
ls --all /foo/bar

REQUEST='{
  "jsonrpc":"2.0",
  "method":"ls",
  "params":{"all":true, "path": "/foo/bar"}
}'
ls --jsh-request "$REQUEST"

ls --jsh-request $(jsh m=ls --all=true --path='"/foo/bar"')
```

In addition to this, JSH requires the following when the `--jsh-request` is passed:
- **MUST** output valid json on stdout _UNLESS_ a documented application
  defined flag in `params` or `method` specifies otherwise.
  - If outputing multiple 'results' (i.e. list of files, results of search, etc), **MuST**
    output one record followed by the null character `\0`.
- **SHOULD** output structured logs to stderr, one json record per line, in the form:


```json
{"lvl":"ERROR", "msg":"this is a message"}
```

JSH was explicitly developed for use in build systems, which often need to
combine outputs from multiple stages using many different programming languages.
However, it's purpose is broader reaching:
- Elminiate the error-prone parsing of outputs, using JSON instead.
  - Standard composability of developer tooling, both at the OS level and higher.
  - Still allowing for fast development and prototyping in any language.
- Enable the user of json query tools (like `jq`) to munge and redirect data,
  as opposed to text-based tools like `awk` or `sed`.
- Allow for shell scripts to quickly be "hosted".
  - Trivial to make them work via web requests, allowing faster and cleaner
    sysadmin interfaces.


# License

The source code is Licensed under either of

* Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or
  http://www.apache.org/licenses/LICENSE-2.0)
* MIT license ([LICENSE-MIT](LICENSE-MIT) or
  http://opensource.org/licenses/MIT)

at your option.

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall
be dual licensed as above, without any additional terms or conditions.

[JSON-RPC 2.0]: https://www.jsonrpc.org/specification_v2
