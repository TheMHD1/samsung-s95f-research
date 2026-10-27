# Managed TCON selector-0x128 read helper

Status: **PREPARED, NOT DEPLOYED — TARGET EXECUTION HOLD**

This directory contains a restricted, portable-IL .NET 6 helper for one
future, separately coordinated ARM32 Tizen execution. It has no runner,
staging command, remote command, retry, polling loop, arbitrary selector, or
generic command-line interface. Nothing in this directory has been executed
on the television.

The compiled request is fixed to:

```text
device          /dev/tztv_tcon
ioctl           0xc010749f
16-byte words   00000013,a55a5aa5,0000f300,00000128
command         0x0000f30000000128
wire direction  write f3 00 00 00 01 28, then request four response bytes
```

Operation 19 is the reviewed generic read route. Operation 18 is the distinct
write-only `SendOneCommand` route and is not present here. The protocol is
still active write-then-read I/O; “read” does not mean passive or prove that
the controller selector lacks read-to-clear or other state effects.

Before opening the device, the helper requires all of the following:

- no command-line arguments;
- runtime architecture `Arm`, four-byte pointers, little endian;
- exact 16-byte struct size and field offsets 0/4/8/12;
- real/effective UID zero; and
- ARM EABI `getpid` syscall number 20 returning the same positive PID as
  libc `getpid`.

After an open, the descriptor is closed from `finally`. A result is classified
as `kernel_output_written` only when ioctl returns zero, word1 changes from
`0xa55a5aa5`, words0/2/3 remain exact, and close succeeds. Sentinel unchanged
is not read success. Mutation of any command word is rejected. A fresh value
outside `0..1023` gets the distinct `incompatible_profile_range`
classification and a nonzero exit.

The `0..1023` check is only the low-ten-bit range of the getter in the copied,
selected controller profile. It is not a calibrated brightness, emitted-light
measurement, panel-state inference, or proof that the packaged image equals
the currently executing controller image.

## Build and local guard check

The project was built only with the already installed SDK 6.0.428:

```sh
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet \
  restore --configfile NuGet.Config ManagedTconDutyRead.csproj
${S95F_EVIDENCE_ROOT}/live-cast/sdk/runtime/dotnet \
  build -c Release --no-restore ManagedTconDutyRead.csproj
```

`NuGet.Config` clears all package sources; restore uses only the SDK's local
framework/reference packs. The build has no external package dependency and
cannot download a package through this configuration. Local x64 execution is used
only to verify fail-before-open behavior; it must print `REFUSED_ARCH_ABI`
and exit 64. That local refusal is not target validation.

Any future target decision remains on hold pending independent exact-byte
review, a new coordinated capture plan, installed source/driver/CLR identity
preflight, and explicit treatment of the generic-read path's missing
status-query flash guard. This package does not provide those transport or
preflight steps.

## Evidence scope

`build-manifest.json` pins the exact ABI report and its independent review,
plus the selected-profile controller getter evidence that reads a low-ten-bit
field. Those are static/package provenance only. They do not prove live
callback installation, current controller firmware identity, selector side
effects, physical brightness, or safety of repeated use. Each process can
perform at most one ioctl; no internal retry is authorized or implemented.
