# V2 MAIN-only canonical packaging checkpoint

**Source gate: terminal PASS. Packaging approval and builds remain pending.**
`release.json` has `source_approved: true` and binds the exact approved source
commit, tree, canonical patch and read-back remote branch HEAD. This flag is a
source-input gate, not authorization to build, commit, tag, push or publish this
packaging checkpoint. The independent packaging checker must approve the frozen
staged tree before the parent authorizes a packaging commit and matrix builds.

## Track and release identity

This is an independent V2 track in `LLJY/opencode-arch`, branch
`v2-022-package`, starting at `6b14ac277914d45916901c3475cbbdfcf47cf3d8`.
Keep V1 refs/worktrees unchanged. The approved source branch in `LLJY/opencode`
is `refs/heads/v2.0.22-downstream-patch`, read back at
`c0f3281662f1f00a81113c3a74069cdb176725a6`. Packaging refs have not been published.
Package identity remains `opencode`; installation/coinstallation policy is
**deferred**. Do not invent conflicts, replacements or a renamed package.

The complete release is exactly these three MAIN packages, all revision 1:

- `opencode-2.0.22-1-x86_64.pkg.tar.zst` — Arch x86_64
- `opencode_2.0.22-1_amd64.deb` — Debian amd64
- `opencode_2.0.22-1_arm64.deb` — Debian arm64

No daemon package, `ocd`, old wrapper, service unit or fourth Ubuntu package.
Ubuntu 24.04 validates the same Debian arm64 package in arm64 userspace under
**direct** `qemu-aarch64-static -L /`; this is not physical DGX Spark validation.

## Reproducible input boundary

- Upstream commit: `527f0b931d1f9b3ebd34e106c51b31ce5db5b075` (v2.0.22).
- Codeload tar is SHA256-pinned in `release.json` and `PKGBUILD`. Both consumers
  reconstruct its full Git tree before applying the patch, then check the
  patched Git tree (all blobs, modes and symlinks), not just textual hunks.
- Approved source commit: `c0f3281662f1f00a81113c3a74069cdb176725a6`;
  full tree: `a7bbcfe9a24aadbc9b0125a870a25f313fb279a5`.
- The canonical full-index/binary patch is regenerated from that immutable commit
  using `git diff --binary --full-index UPSTREAM_COMMIT CANONICAL_COMMIT` and is
  SHA256-pinned as
  `009e46adedb3b0ed102a64ae7db8d50645a58c2815f32542996560370b1f5f2e`.
  Source epoch remains the upstream target timestamp `1790914978`.
- Bun is exactly **1.4.2**. Dockerfiles pin the official glibc image digest;
  Arch overlays its compiler while keeping the distro bun dependency installed.
  No packageManager rewrite, Alpine compiler, floating Bun or arbitrary local
  PTY override. The native CLI build targets are
  `--target=opencode-linux-x64-baseline` and `--target=opencode-linux-arm64`;
  outputs are `cli-linux-x64-baseline` / `cli-linux-arm64`.
- Root `bun install --frozen-lockfile --ignore-scripts --os=* --cpu=*` materializes
  all architectures' native optional dependencies. Then the source-owned
  `packages/cli/script/build.ts --skip-install` builds and embeds the app UI
  through its default `buildAppArchive` path. **Never pass `--skip-web-ui`.**
- Dependencies are resolved by target-aware `dpkg-shlibdeps`, with explicit
  arm64 library paths/environment, no ignore-missing-info fallback. Docker's
  arm64 cross builder installs arm64 libc/libstdc++/libgcc userspace for both
  dependency discovery and direct QEMU execution.
- Validators check package identity/revision/architecture, nonempty installed
  files, forbidden legacy payloads, ELF64/machine/interpreter, native `--version`,
  `--help`, `--completions bash` / `--completions zsh`, and actual bundled HTML
  plus local JS over an isolated loopback foreground `serve`. No installed
  production service or user data is touched. Exported package validation is
  offline (`--network none`); Ubuntu additionally unpacks/configures the package
  and repeats installed-binary smoke checks under direct QEMU.

Source/compiler/image inputs are pinned; distro apt/pacman dependency repositories
remain mutable. This checkpoint does **not** claim bit-identical package bytes
across later distro updates. Capture resolved dependencies/build logs at the
approved matrix build. Build sequentially to stay within the available disk;
wrappers remove work containers (images/cache remain reusable).

## Gate before builds (parent-owned)

1. Source GO is complete. Reconfirm the exact approved commit, tree, base, patch
   SHA256 and remote branch HEAD in `release.json`; do not substitute a later ref.
2. Independently reproduce pinned upstream tar -> Git index -> approved full tree
   and regenerate the patch byte-for-byte, including all postimage blobs/modes.
3. Verify `PKGBUILD` SHA256 sums in source order (tar, patch, release.json,
   packaging.py), and `.SRCINFO` byte-for-byte using unprivileged makepkg in the
   cached Arch builder with read-only inputs and private writable `/tmp` state.
4. Rerun the helper suite and shell/Python syntax checks from the frozen staged
   Git archive. Source-GO refusal tests use false fixture metadata and remain
   valid after approval. Independent packaging approval must bind the exact
   staged tree/diff/manifest before a packaging commit or matrix build.

Source SCOUT 52614 remains **DEFER** and is not included. Same-process durable
re-entry does not prove cold-process/database-reopen crash recovery.

## Approved build and validation commands (DO NOT RUN YET)

All inputs must be from the approved packaging Git archive, not scripts borrowed
from V1 or a live source worktree. Build helpers work without `.git` in that
archive. Docker context is an explicit allowlist of this track's inputs.

```sh
# In the approved clean packaging archive; separate output dirs are optional.
OUT_DIR=/absolute/output/arch ./build-makepkg-docker
OUT_DIR=/absolute/output/debian ./build-deb-docker amd64
OUT_DIR=/absolute/output/debian ./build-deb-docker arm64
./validate-ubuntu-arm64-docker /absolute/output/debian/opencode_2.0.22-1_arm64.deb 2.0.22-1
```

Native toolchain containers may run `./build-deb amd64` or `./build-deb arm64`;
`SOURCE_ARCHIVE=/absolute/path/upstream.tar.gz` optionally reuses a local source
archive, still requiring the exact pinned SHA256. `OUT_DIR` selects output.
Existing same-name outputs are refused. Wrappers select the compiler/builders
from their tracked Dockerfiles; no hidden cached custom matrix helper is required.

`python3 -m unittest discover -s tests -v` uses command spies; it does not produce
packages or compile binaries. TDD RED/GREEN logs and the exact staged checkpoint
archive/manifest live in the external maintenance evidence directory, not inside
release artifacts.
