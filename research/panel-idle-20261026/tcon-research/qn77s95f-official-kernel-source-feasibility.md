# Official-source feasibility for the QN77S95F kernel build

Recorded 2026-10-27 UTC. This was primary-source web research plus offline
comparison with retained build evidence. It made no TV, root, firmware,
module, flashing, or target call and downloaded no source archive.

## Result

No official source release was found that is positively identified as the
exact installed build:

```text
model       QN77S95FAFXZC
build       T-RSMFAKUC-0090-REL-202607141953
kernel      Linux 5.4.261, AArch64
vermagic    13781815, release SMP preempt mod_unload aarch64
```

Official material does establish the product/platform family:

* Samsung's exact Canadian support page identifies `QN77S95FAFXZC` and the
  `T-RSMFAKUC-0090_TB-RSWF4AKUC-0090.zip` firmware family. Its presently
  listed package is release `0090-1301.0`, published 2026-09-08. That release
  version/publication date and the installed internal build timestamp
  `202607141953` are different identifier types: the public metadata does not
  bind this listed release to the installed build timestamp, so exact binary
  identity remains unverified. See [Samsung Support Canada: QN77S95FAFXZC](https://www.samsung.com/ca/support/model/QN77S95FAFXZC/).
* Samsung's official TV model-group table places S95F in
  `25TV_PREMIUM3`, on Tizen 9.0. See
  [Samsung Developer: TV Model Groups](https://developer.samsung.com/smarttv/develop/specifications/tv-model-groups.html).
* Tizen publishes a public 9.0 branch and reference-platform releases. The
  official M2 note says source is under `tizen_9.0`; it describes Unified/Base
  images and Raspberry Pi kernel work, not a Samsung retail RSMF kernel build.
  See [Tizen 9.0 M2 release](https://docs.stg.tizen.org/platform/release-notes/tizen-9-0-m2/)
  and the [Tizen 9.0 milestone index](https://download.tizen.org/releases/milestone/TIZEN/Tizen-9.0/).

Those facts are enough to identify a family and public userspace generation.
They are not an exact kernel build tree, generated configuration, symbol CRC
set, or module acceptance proof. The retained official main-firmware MSD is
likewise package-family evidence; without a source-bound, decrypted exact
kernel member identity, it does not bind this public release metadata to the
installed kernel bytes.

## Samsung Open Source Release Center search boundary

The official release center exposes keyword searches, for example:

* [exact model search](https://opensource.samsung.com/uploadSearch?searchValue=QN77S95F)
* [firmware-family search](https://opensource.samsung.com/uploadSearch?searchValue=T-RSMFAKUC)
* [platform-token search](https://opensource.samsung.com/uploadSearch?searchValue=RSMF)

No exact model, `T-RSMFAKUC`, `RSMF`, build timestamp, or `25_DTV` result was
found in indexed official search results during this review. Direct browser
enumeration of these result pages was blocked here by the site's automated
security challenge. Therefore this is **not** proof that Samsung has never
published a matching or family archive; it is a bounded statement that no
exact official release metadata was recoverable from the current indexed and
directly accessible surfaces.

Samsung's older TV entries demonstrate that release-center TV bundles can be
coarse product-group releases with version `1000`, rather than a one-to-one
record of every retail firmware build. Examples are the official
[`21_DTV_KantSU2e` search result](https://opensource.samsung.com/uploadSearch?searchValue=A705)
and [`15_DTV_HawkM` release page](https://opensource.samsung.com/opensource/15_DTV_HawkM/seq/9).
They are examples of portal structure only; neither is source for this TV.

The official fallback is Samsung's
[Open Source Inquiry](https://opensource.samsung.com/requestInquiry), which
offers `Request for source codes` and the `TV/Video/Monitor` category. A
precise inquiry should quote the full model and installed build above and ask
for the corresponding release-center record/archive name. It should also ask
whether the exact build-generated artifacts listed below are available. An
inquiry is the shortest primary-source path; this report did not submit one.

## What public Tizen source does and does not supply

Tizen's official repository index lists generic repositories including:

* `platform/kernel/linux-arm64.git`
* `platform/kernel/tizen-kernel-configs.git`
* `platform/kernel/linux-tizen-modules-source.git`
* `platform/kernel/linux-tizen-modules.git`

See the [official Tizen repository index](https://review.tizen.org/git/).
Tizen's own repository-structure documentation says its public source runs on
the PC emulator and ARM reference devices and gives OEMs a base for commercial
customization; it does not say these repositories reproduce each retail
Samsung TV. See
[Tizen Git Repository Structure](https://docs.stg.tizen.org/platform/get-started/git-repo-structure/)
and [Tizen Open Source Project](https://docs.stg.tizen.org/platform/get-started/open-source-project/).

The public Tizen 9.0 source-package index also contains generic toolchain and
UAPI packages, including GCC 9.2.0 and `linux-glibc-devel-5.4`. See the
[official Tizen 9.0 Base source index](https://download.tizen.org/snapshots/TIZEN/Tizen-9.0/Tizen-9.0-Base/latest/repos/standard/source/).
That is useful family context because the retained kernel banner also names
GCC 9.2.0, but matching a compiler major version and UAPI package does not
reconstruct Samsung's RSMF kernel, vendor drivers, generated configuration,
or module ABI.

No official Tizen page examined here associates any public commit/tag with:

* `QN77S95FAFXZC`;
* `T-RSMFAKUC-0090-REL-202607141953`;
* the retained kernel build time;
* custom vermagic token `13781815`; or
* the exact installed Samsung module set.

## Artifacts required for a compatible observer

A family source archive would improve source-level analysis, but it is not
enough to call an out-of-tree observer module compatible. At minimum the
following must be matched or independently recovered:

1. The exact kernel source revision and Samsung vendor patches used for the
   `202607141953` build.
2. The final `.config`, generated `include/generated/` and `include/config/`
   headers, architecture/generated offsets, and the build scripts that
   produce the custom release/vermagic string.
3. The exact compiler/binutils ABI and flags. GCC 9.2.0 family agreement is
   helpful but insufficient.
4. `Module.symvers` or an equivalent exact symbol/CRC record if modversions
   are enabled, plus the actual policy state that determines whether CRCs are
   checked. A source tree alone does not recreate build-specific CRCs when
   configuration or type definitions differ.
5. The exact tracepoint callback prototypes and config-dependent structure
   layout used by the chosen observer—not merely tracefs event text formats.
6. Samsung's module-file acceptance boundary. Retained installed modules have
   a custom `:UEP` trailer and custom vermagic; public kernel sources do not
   provide an accepted UEP signature/key or prove that a normally signed or
   unsigned new module will load.

The existing offline capability audit positively found exported tracepoint
registration/enumeration APIs in the retained Image, so a tracepoint-only
observer remains architecturally plausible. It also found no supported
module-callable kprobe/function-ftrace registration surface. Official family
source does not change either retained binary fact.

## Practical host-only path

The next bounded steps are metadata-first, without building or loading
anything:

1. Use Samsung's official source-code inquiry with the exact model/build and
   request the matching release URL or archive identifier.
2. If Samsung names an RSMF/2025-TV archive, inspect only its published
   filename, size, checksum, and archive member listing first. Check for
   `.config`, generated headers, `Module.symvers`, vendor kernel/module source,
   and build scripts before treating it as useful for module work.
3. Bind any candidate source revision back to retained binary evidence:
   kernel banner, exact exports, instruction slices, installed-module
   vermagic, module undefined symbols, and vendor structure/tracepoint ABIs.
4. Keep module construction and load testing on HOLD unless the exact ABI and
   UEP acceptance boundary are separately closed. Stock module signatures or
   a generic Tizen 9.0 toolchain must not be assumed sufficient.

If Samsung supplies only family source and omits generated build products,
that source can still improve static interpretation and permit a source-vs-
binary diff. It would not by itself make an observer loadable. The exact
generated ABI and UEP policy remain the decisive gaps.

## Scope and limits

This review did not obtain or inspect a Samsung OSRC archive, because no exact
matching release metadata was found and large downloads were out of scope.
It did not establish that a matching archive is absent from every unindexed
or authenticated Samsung surface. It did not build, sign, stage, insert, or
remove a module and makes no claim that a new module would be accepted.

The official Samsung support package is retail firmware metadata, not source
release metadata. The public Tizen repositories/releases are valid primary
sources for Tizen 9.0 and reference kernels, but no official evidence found
here binds them byte-for-byte or ABI-for-ABI to this commercial RSMF build.
