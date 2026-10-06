# V2 main-only downstream packaging

## Frozen source approved — package-input gate remains separate

The exact **2.0.24-1** source passed independent review. Four Client-suite failures were reproduced with identical assertion blocks on pristine v2.0.24 and explicitly accepted as baseline exceptions; the complete suite is not described as all-green. Source Git/API SHA and tree readback passed. The autonomous maintenance authority permits isolated builds and publication only after the exact package-input checker passes. **Host installation, managed-service replacement and live cutover remain forbidden.** Earlier 2.0.23 packages are not successor build evidence.

- Upstream: **v2.0.24**, `e7a34f09bfd9134dfade5a8ddb843f7030bc9a69`; tree `aef0ff8dce5435b3649bdd1fa6feb35015e2b379`.
- Expected local source: `74b173afec0cbb75a30d4075f6dba03ce4f1d9a9`; tree `690b18689e3cd09fd52a2e5df8cd9eb696fccf97`.
- Verified source ref: `LLJY/opencode`, `refs/heads/v2.0.24-downstream-patch`; Git and API readback both name `74b173afec0cbb75a30d4075f6dba03ce4f1d9a9`, with tree `690b18689e3cd09fd52a2e5df8cd9eb696fccf97`.
- Full-index binary-capable patch: `downstream-2.0.24.patch`; SHA-256 `f767dc47095c7d3e49316b692ee9f09cfe9902a41d1f647cca7a66f6485e4059`.
- Immutable upstream codeload archive SHA-256: `a045e473e92a75956585d1957a06707e6757f3da5a3010ef0f4e679f569920de`.

`release.json` has **`source_approved: true`** and pins the reviewed upstream/source identities, archive, patch, source epoch, compiler and verified remote source HEAD. Canonical Git indexed apply/tree/byte roundtrips and actual cached-makepkg `.SRCINFO` regeneration remain required. Source approval does not substitute for the fresh independent checker on the final staged package inputs or the actual three-artifact build/validation matrix.

## Matrix and ownership

Exactly three intended main packages:

- `opencode-2.0.24-1-x86_64.pkg.tar.zst` — Arch x86_64.
- `opencode_2.0.24-1_amd64.deb` — Debian amd64.
- `opencode_2.0.24-1_arm64.deb` — Debian arm64.

The native web UI is embedded by the source-owned build. No `ocd`, separate daemon package, legacy wrapper or service unit, and no fourth Ubuntu artifact. Keep the V1 canonical inputs and installed V1 wrapper/service untouched. Package identity remains `opencode`; coinstallation/cutover policy is deferred.

Ubuntu 24.04 acceptance, after both gates and explicit build authorization, must validate the same arm64 Debian package with direct QEMU in target userspace, not claim native ARM hardware or DGX Spark deployment. No successor matrix or runtime validation has been run during preparation.

## Preserved recipe contracts

Bun is **1.4.2**, using the pinned official glibc image digest. Targets remain `opencode-linux-x64-baseline` and `opencode-linux-arm64`. Frozen all-platform dependency installation preserves the lock; the native source build embeds UI by default. Never pass `--skip-web-ui`, rewrite `packageManager`, substitute Alpine Bun, override the native PTY asset or relabel x86_64 output as ARM.

The Arch recipe retains `curl`, `gcc-libs`, `glibc`, `icu`, `ripgrep`, `tar`; Debian derives target-architecture shared-library dependencies with `dpkg-shlibdeps` and adds `curl`, `ripgrep`, `tar`. Both completion files use native `--completions bash` / `--completions zsh`, with direct QEMU for cross-target execution. The main payload includes the upstream MIT `LICENSE`. V1-only 0BSD wrapper licensing does not imply a V2 daemon payload.

Validators inspect metadata, dependencies, payload paths, ELF class/machine/interpreter, exact `opencode v2.0.24` output, help/completions and real embedded HTML/local JavaScript. Runtime probes are isolated foreground `serve` with private HOME/XDG/config/storage and loopback; never the user's running service. Unit tests use spies and are not compilation, package-build or runtime proof.

All future builds must consume an independently approved clean Git archive, not a dirty historical checkout. Distro repositories remain mutable, so input pins do not promise bit-identical future binary rebuilds. Record resolved logs and artifact hashes. Publication requires separate authority, exact fully qualified source/package ref/tag readback and fresh asset redownload/byte comparison. Never overwrite existing releases or assets.
