# Control v3 launch-receipt escape diagnosis

Date: 2026-10-27 UTC

Scope: offline inspection only. This diagnosis made no target request, retried no
launch, ran no native helper, and changed no frozen candidate file. The evidence
record is `control-smoke-v3/record.json` (SHA-256
`fed51d0624c3c627e3cb49e40fa03a588c0314c9e06cff95fb9189e6b4d518f7`).

## Finding

The control-v3 target launch request completed with exit code 0, and its saved
`/proc` stat/start material was emitted. The host then rejected the response
because the first separator was the two printable characters backslash and `n`,
not a line-feed byte:

```text
LAUNCH_ACK 9136 9140 28569437\nHANDSHAKE_STAT_BEGIN
```

The strict parser therefore saw `LAUNCH_ACK ...\nHANDSHAKE_STAT_BEGIN` as its
first line. That cannot match the anchored `LAUNCH_ACK <pid> <pid> <ticks>`
expression in `parse_launch()`. This was a correct fail-closed rejection of a
malformed receipt.

The defect is in the interaction between the generated `printf` format and the
root agent's command-argument quoting:

1. Frozen `run-once.py` SHA-256
   `25b942ae2dbca8b210d9b195bb79b2b509d7501825e0b8d107ddc718911b6bd6`
   contains two backslashes in its Python source at the ACK emitter:

   ```python
   printf 'LAUNCH_ACK %s %s %s\\n' "$dispatch" "$p" "$ticks"
   ```

2. Python string evaluation produces one backslash followed by `n` in the
   generated shell command. Offline byte inspection of that exact fragment gave
   `...25735c6e27...`; `5c 6e` is `\n`.

3. The deployed root-agent source builds
   `start.Arguments = "/bin/sh -c " + QuoteArgument(command)`. Its
   `QuoteArgument()` globally applies
   `value.Replace("\\", "\\\\")` before quoting the command. The corresponding
   offline quoted fragment contains two backslashes before `n`.

4. The authenticated target result is the decisive end-to-end observation: the
   shell `printf` received the doubled escape and printed a literal `\n`.
   Everything following it retained normal real line feeds, so this was not a
   general stdout/base64 corruption.

The successful marker-only qualifier used a materially different source form.
Its Python source had one backslash in `printf '...\n'`; Python converted that
escape into an actual line-feed byte inside the generated shell format string.
That left no backslash for the root agent to double. Offline inspection confirms
the generated qualifier fragment contains byte `0a` immediately after `%s`,
whereas the frozen onset wrapper contains `5c 6e`.

## What succeeded before the host rejection

The same authenticated response records all of the following:

- command exit code `0` and empty stderr;
- dispatch PID `9136`, actual supervisor PID `9140`, and start ticks `28569437`;
- a saved stat record whose PID, process group, and session are `9140`;
- a saved start record and final uptime framing;
- the complete `HANDSHAKE_STAT` and `HANDSHAKE_START` bodies.

This shows that the in-request file handshake and the two bounded supervisor
identity checks reached the ACK emitter. It does **not** prove that the detached
supervisor or native child subsequently stopped, nor does it prove that no USB
transfer occurred. The supervisor starts its finite child independently of the
host parser. The only established post-failure host behavior is that no further
target request was made: the record has 30 calls, `cleanup_deferred=true`,
`no_retry=true`, and `automatic_ui=false`.

Accordingly, the retained v3 stage is an ambiguous live-execution artifact, not
a clean no-transfer lineage. Absence or later disappearance of its processes or
files would still not reveal the controller parser phase.

## Why the frozen offline suite missed it

The 19-case suite exercised the parser and launcher components separately, but
not the production serialization path between them.

- `FakeRoot.root()` detects the launch command and directly returns a Python
  string beginning `LAUNCH_ACK 699 700 12345\n...`. In that ordinary Python
  string, `\n` is already a real line feed. It does not execute the generated
  `printf`, pass the command through `SamsungTvRootAgent.QuoteArgument()`, or
  emulate the target process-argument parser. The real `parse_launch()` thus
  received ideal framing in all fake accepted/rejected cases.

- `local_launcher_contract()` builds a separate, reduced launch string and runs
  it directly as `subprocess.run(['/bin/sh', '-c', launch])`. It checks
  `setsid -f`, the actual child identity, inherited-FD closure, and completion,
  but it neither calls production `launch_command()` nor production
  `parse_launch()`. It also bypasses root-agent argument quoting.

- The source-contract assertion checks the expected nohup/setsid/FD-closure
  shape. The multiline-base64 assertion protects against the earlier `tr -d`
  corruption class. Neither asserts the byte representation of the ACK newline
  after root-agent transport.

- Shell syntax checking can accept both `\n` and `\\n` format strings; it cannot
  detect this semantic output difference.

Thus the normal and `python -O` passes were meaningful for their stated cases,
but they were not an end-to-end framing test of
`launch_command -> root-agent QuoteArgument -> /bin/sh -c -> printf ->
parse_launch`.

## Bounded correction and test requirements

No correction was applied here. A candidate-specific correction should avoid a
backslash escape in fixed receipt framing. For example, the numeric-only ACK can
be emitted with shell `echo` arguments, or the generated command can carry a
literal newline as the proven qualifier did. Changing the shared root-agent
quoting algorithm is a broader security and compatibility boundary and should
not be inferred from this one caller.

Before another deployment, offline coverage should additionally establish:

1. The exact production `launch_command()` is used, not a reduced facsimile.
2. The command passes through the root agent's actual argument-construction
   behavior (or a demonstrated byte-faithful model of it).
3. The resulting shell stdout is passed to the real `parse_launch()`.
4. The first separator is byte `0a`, with no `5c 6e` or `5c 5c 6e` at the ACK
   boundary.
5. A deliberately literal `\n` receipt is rejected and preserves the existing
   no-retry/no-cleanup behavior.

A bounded metadata fetch after this already-completed but host-rejected request
is a separate recovery-policy decision. It must not be treated as an automatic
extension of the failed run: the present wrapper intentionally made no request
after ambiguity, and any exception would need explicit review against that
invariant and the unresolved controller-phase state.

## Evidence pins

- v3 record:
  `fed51d0624c3c627e3cb49e40fa03a588c0314c9e06cff95fb9189e6b4d518f7`
- frozen qualified `run-once.py`:
  `25b942ae2dbca8b210d9b195bb79b2b509d7501825e0b8d107ddc718911b6bd6`
- frozen qualified `test-wrapper.py`:
  `adc62341f046850402df8c929742bdc936176b002fd8f7e42e8c920684daf9c1`
- frozen qualified `build-wrapper.py`:
  `0c443b28315b3cc288c2d5d3f8cd777a517c14592c0b4d0bca1b6c41b8c06992`
- successful marker qualifier source:
  `74d964fa6e80d4834409d4e3b86998c729203c8448a5237b6139e8a7649e87d0`
- inspected common `SamsungTvRootAgent.cs` source:
  `3b53e8c9de66331ca5336f57bc8eba33adf66ca2860a29daedbbeb3a98ea8405`
