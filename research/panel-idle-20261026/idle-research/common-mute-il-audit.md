# Preserved managed-bridge IL evidence

Input: `binaries/Tizen.TV.Service.ViewPlugin.Common.dll`, SHA-256
`19d5024600149b4694f4ff36c371bf39b77d2fec7b0605c0827dce05cba5dd59`.

The original temporary raw IL dump was `/tmp/viewcommon.il`, SHA-256
`5d086fb09d2b435a3ac2ee1c52e7817e1681eb77684c7eb03ee672783619cbd4`
(472036 bytes, captured 2026-10-26 04:43:09 UTC).  Its original extractor
command/version was not retained by the prior session, so this audit does not
invent one.  The important method token/IL regions are copied here before that
temporary dump expires.  The native disassembly portions of this investigation
are reproducible with `PYTHONPATH=/tmp/tcon-capstone python3` (Python 3.14.4,
Capstone 5.0.7) and the parent-owned exact-build scanner
`overnight/trace-avocd-panel-mute.py`.

## `TVServiceController::MuteAV`, token `06000118`

```il
0000: newobj .ctor
0005: stloc.0
0006: ldloc.0
0007: ldarg.0
0008: stfld FieldDefinition:040000fb
000d: ldloc.0
000e: ldarg.1
000f: stfld FieldDefinition:040000fc
0014: nop
0015: ldloc.0
0016: ldftn <MuteAV>b__0
001c: newobj Tizen.TV.Service.CoBA.Common.WorkerTask::.ctor
0021: ldnull
0022: ldc.i4.0
0023: ldc.i4 88130000
0028: call Tizen.TV.Service.CoBA.Common.FSParallelThread::Task
002d: pop
002e: ret
```

## `TVServiceController::TrySetPanelMuteOnResume`, token `06000121`

The decisive branch region (the complete method is token-addressable in the
input DLL and indexed at raw-dump lines 14950–15091):

```il
0002: ldarg.0
0003: call get_PreviousFullScreenApp
0008: ldarg.0
0009: ldfld FieldDefinition:040000aa
000e: call System.String::op_Equality
0013: stloc.1
0014: ldloc.1
0015: brfalse.s 72
...
0089: ldloca.s 00
008b: call Tizen.TV.System.Avoc.Avocd::AvocGetPanelMuteCaseStatus
0090: ldc.i4.0
0091: ceq
0093: stloc.3
0094: ldloc.3
0095: brfalse 82000000
009a: nop
009b: ldloc.0
009c: ldc.i4.1
009d: ceq
009f: stloc.s 04
00a1: ldloc.s 04
00a3: brfalse.s 76
...
0110: ldc.i4.1
0111: call Tizen.TV.System.Avoc.Avocd::AvocSetPanelMute
0116: pop
0117: ldc.i4.1
0118: stloc.2
...
013d: ldc.i4.0
013e: stloc.2
0141: ldloc.2
0142: ret
```

The original IL establishes that local 0 is passed by address to the AVOC
case-status call and is compared against one.  It does not expose the source
of that local in the clipped region; no name is assigned to it here.

## Mute worker, token `06000177`

```il
0002: ldarg.0
0003: ldfld FieldDefinition:040000fb
0008: call get_PIGAutoplaySupport
000d: stloc.0
000e: ldloc.0
000f: brfalse 49020000
...
00aa: call get_TvsSession
00af: ldc.i4.0
00b0: ceq
00b2: stloc.3
00b3: ldloc.3
00b4: brfalse.s 09
00b7: ldnull
00b8: stloc.s 04
00ba: leave C4010000
00bf: call Tizen.TV.Broadcast.TVService.TVServiceAPI::Instance
00c4: ldc.i4.1
00c5: ldc.i4.0
00c6: callvirt Tizen.TV.Broadcast.TVService.TVServiceAPI::CreateAVControl
00cb: stloc.s 05
00ce: ldloc.s 05
00d0: ldarg.0
00d1: ldfld FieldDefinition:040000fc
00d6: callvirt Tizen.TV.Broadcast.TVService.API.Interface.IAVControl::MuteVideo
...
0151: ldloc.s 05
0153: ldarg.0
0154: ldfld FieldDefinition:040000fc
0159: callvirt Tizen.TV.Broadcast.TVService.API.Interface.IAVControl::MuteAudio
...
01d7: ldloc.s 05
01d9: brfalse.s 08
01db: ldloc.s 05
01dd: callvirt System.IDisposable::Dispose
...
0283: ldloc.s 04
0285: ret
```

This is the direct evidence behind the scoped statement that CSFS `MuteAV`
operates the TV-service video and audio planes.  It is not evidence of a
direct AVOC/FRC/TCON panel-mute command.
