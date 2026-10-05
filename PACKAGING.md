# V2 main-only downstream packaging

This independent V2 track must never overwrite V1 canonical inputs or retire the installed V1 wrapper/service. Installation and live cutover are deferred. These recipes build and validate private disposable containers only; they do not authorize host package installation, managed-service replacement, production configuration or storage changes.

## Exact release input

- Upstream: **v2.0.23**, `0fd7e2829449b052abf0078666669302923d77af`.
- Reviewed source: `82c4dfc8cf94a9ec021b28e2546e96646312dbb7`; tree `cefea817d6fe483876ab6d9c98910060aa6da40d`.
- Source branch in `LLJY/opencode`: `refs/heads/v2.0.23-downstream-patch`, exact Git/API SHA/tree readback verified.
- Full-index binary-capable canonical patch: `downstream-2.0.23.patch`; SHA-256 `76c84f496c6b8bcdf999b0e6988a5796fb7aae948c653ddaaa1ff39c2545b4a6`.
- `release.json` pins upstream codeload archive, upstream/source trees, patch, compiler, source epoch and approved source identity. Consumers reproduce the complete Git index before and after application, not merely selected hunks.
- Canonical patch regeneration, pristine indexed apply/tree/byte roundtrip and exact `.SRCINFO` regeneration are pre-build gates. Every consumed helper is tracked and must survive a clean Git archive.

The source has a terminal independent successor PASS. The initial checker found an aggregate MCP startup-timeout violation in upstream's new connection retry; the scoped test-first correction bounds retry plus query fallback without changing external-tool replay policy. Four bounded native PRs add Vertex effort support, Console response disposal, text-capable default selection and model-specific Azure Chat routing. Native retained-partial continuation, settled success/failure receipts, unknown-outcome barriers and static Authorization handling remain explicit. Cold OS-process crash/restart and external exactly-once effects are not claimed from fixture tests.

## Matrix and package ownership

Revision **1**, exactly three main packages:

- `opencode-2.0.23-1-x86_64.pkg.tar.zst` — Arch x86_64.
- `opencode_2.0.23-1_amd64.deb` — Debian amd64.
- `opencode_2.0.23-1_arm64.deb` — Debian arm64.

The native web UI is embedded. No `ocd`, separate daemon package, legacy service unit or fourth Ubuntu artifact. Package identity remains `opencode`; coinstallation/cutover policy is deferred rather than inventing replacements/conflicts. Ubuntu 24.04 checks the same arm64 Debian package in target userspace through **direct QEMU**, not native ARM hardware or DGX Spark deployment.

## Build and verification

Build only after the exact committed packaging snapshot receives its independent gate. The standing maintenance job supplies isolated-build/publication authority, not installation authority.

```sh
OUT_DIR=/absolute/fresh/artifacts ./build-makepkg-docker
OUT_DIR=/absolute/fresh/artifacts ./build-deb-docker amd64
OUT_DIR=/absolute/fresh/artifacts ./build-deb-docker arm64
./validate-ubuntu-arm64-docker /absolute/fresh/artifacts/opencode_2.0.23-1_arm64.deb 2.0.23-1
```

Run these from a clean archive of the reviewed packaging commit, never a dirty checkout or an opaque staging helper. Output wrappers refuse existing expected filenames, export from stopped containers, and repeat validation on host-exported bytes offline.

Bun is pinned to **1.4.2** and an official glibc image digest. Arch uses an unprivileged builder with a writable build directory; Debian arm64 is cross-built in an amd64 container with explicit target dependencies and direct `qemu-aarch64-static -L /` for completion/smoke execution. Native CLI targets are `opencode-linux-x64-baseline` and `opencode-linux-arm64`. Frozen all-platform dependency installation preserves the lock; source-owned native build embeds the UI by default. Never pass `--skip-web-ui`, rewrite packageManager, substitute Alpine Bun or relabel native x86_64 output as ARM.

Validators inspect name/version/architecture, dependencies, payload paths, ELF64/machine/interpreter, exact `opencode v2.0.23` version output, help and both completions. They retrieve real embedded HTML and a local JavaScript asset from isolated foreground `serve`; private HOME/XDG/config/database and loopback prevent live-service discovery or replacement. Release acceptance also inspects lifecycle scripts, privileged/world-writable files, licenses and forbidden legacy payloads. Unit helper tests use command spies and are not package-build proof.

Distro apt/pacman repositories remain mutable: source/compiler/image pins do not promise bit-identical future rebuilds. Retain resolved build logs, package hashes and provenance. Source/package branches and fully qualified release tags must be read back; every published asset must be redownloaded into fresh storage and byte-compared before publication success is reported. No existing release tag/assets may be overwritten.
