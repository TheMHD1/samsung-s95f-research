# Ordinary scan gating and the limits of late samples

This is an offline follow-up in the selected package, SHA256
`bad60bca4d6064406f14e53da3528d46701ec9c81673f4323db1937f6a2017e0`.
Image-1 stored FILE offsets are linked VA plus `0x40200`. It describes the
ordinary existing scan caller without changing it or entering the separate
return-guard, persistence, high-bank or protection-bypass paths. No target
operation occurred.

## Exact ordinary ordering

1. At VA `0xc25e..0xc27a`, function `0xc250` sets CPU byte `0x200004d8`
   to 1 only when `uint16[R+0x2400]==0` and
   `uint16[R+0x240e]==1`. Otherwise it writes 0.
2. At `0xc27c..0xc2a2`, before entering the orchestrator, it separately
   mirrors the alternate byte into the `0x200004c2` halfword and its nonzero
   state into `0x200004c4` when the numeric value changes. This mirror update
   is not behind the later ordinary scan gate.
3. At `0xc2de..0xc2e6`, it loads `r0` from byte `0x200004d8`, loads `r1`
   from `0x200004d7`, and calls `0xb644`.
4. `0xb648` saves incoming `r0` in `r4`. On the ordinary non-refresh route,
   `0xb6a6..0xb6a8` tests `r4==0` and branches to `0xb732` if true.
   That branch skips the status, packed selector/unpacker, final numeric
   predicate, and the frame-completion call at `0xb72e`.
5. A separate refresh route at `0xb662..0xb6a4` also bypasses packed scan.
   Post-scan housekeeping at `0xb732` and later can still run; therefore this
   is not a claim that the whole function or controller has stopped.

The aligned direct-BL census in selected image 1 is:

```text
0xc250 <- 0x4446
0xb644 <- 0xc2e6
0xb7ec <- 0xb6fa
0xbd58 <- 0xb84c, 0xb874, 0xb88a
0x1e68 <- 0xbfbc, 0xbfd0, 0xbfdc
```

This is a bounded direct-call census, not a proof against indirect calls,
interrupts, external writers, configuration reloads, or corruption.

## Implication for the retained context

The packaged event setter changes `R+0x2400` to 1 and `R+0x240e` to 0.
If those values are preserved into the next ordinary invocation, the caller
sets its scan-enable argument to 0. The same routine consequently does not
provide an ordinary continuing scan that would refresh the `+0x0f06/08`
score stores while that state remains latched.

Those stores are still **last-seen values rather than event-exclusive
records**: the code writes them before every reached comparison, including
comparisons that do not fault. No event identifier is stored alongside them.
But their mere position before the comparison does not prove that they kept
rolling after V6. Describing them as definitely refreshed by later ordinary
scans would be inaccurate.

Conversely, the alternate selector's mirror update precedes the scan gate.
If the ordinary caller continues to execute while scanning is disabled,
that mirror can reflect a newer configuration than the last stored score.
A current mirror/flag sample therefore must not automatically be paired with
an old score and called the event-time comparison.

The V6 bus fault pattern, late score reads, and forthcoming selector samples
do not prove continuity of all these CPU values or the execution of every
packaged instruction. In particular, they do not establish whether another
writer or initialization path ran between samples. The event-time record
still needs to capture the actual mode, loaded threshold source/value and
score together at the taken comparison edge. This note narrows the update
model without promoting a late sample to a complete event reconstruction.
