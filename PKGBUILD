# Independent downstream V2 MAIN-only recipe. Canonical source gate: PASS.
# Packaging checker and explicit build authorization are still required.
# Upstream Arch maintainers: Carl Smedstad, Sven-Hendrik Haase
pkgname=opencode
pkgver=2.0.22
pkgrel=1
pkgdesc='The open source coding agent (V2 native CLI with bundled web UI)'
arch=('x86_64')
url='https://github.com/anomalyco/opencode'
license=('MIT')
depends=('curl' 'gcc-libs' 'glibc' 'icu' 'ripgrep' 'tar')
makedepends=('bun' 'git' 'python')
optdepends=(
  'wl-clipboard: clipboard support on Wayland'
  'xclip: clipboard support on X11'
)
options=('!debug' '!strip')
_commit=527f0b931d1f9b3ebd34e106c51b31ce5db5b075
_srcname=opencode-$_commit
source=(
  "opencode-$pkgver.tar.gz::https://codeload.github.com/anomalyco/opencode/tar.gz/$_commit"
  "downstream-$pkgver.patch"
  'release.json'
  'packaging.py'
)
sha256sums=(
  '910b87aa2521583773312e207bf6a9e7990ebb7cb70d6e7aa928a2b6b5573641'
  '009e46adedb3b0ed102a64ae7db8d50645a58c2815f32542996560370b1f5f2e'
  'd1732c3d008e01a794f1f07b61701356415ff874a7b17407c5183225417e9f91'
  '2b74b5b76cc74a6adff5974519720c233a7fdd36b1dd04b2b6c1cc0d96f90139'
)

prepare() {
  # Verifies tar's complete Git tree, then applies the full-index binary patch
  # through Git's index and verifies the exact approved canonical source tree.
  python3 "$srcdir/packaging.py" prepare "$srcdir/$_srcname" "$srcdir/downstream-$pkgver.patch"
}

build() {
  # The source-native buildAppArchive path is the default; never skip web UI.
  # Explicit baseline target avoids --single selecting both x64 variants.
  python3 "$srcdir/packaging.py" compile "$srcdir/$_srcname" amd64
}

check() {
  python3 "$srcdir/packaging.py" smoke \
    "$srcdir/$_srcname/packages/cli/dist/cli-linux-x64-baseline/bin/opencode" amd64 "$pkgver-$pkgrel"
}

package() {
  python3 "$srcdir/packaging.py" stage "$srcdir/$_srcname" \
    "$srcdir/$_srcname/packages/cli/dist/cli-linux-x64-baseline/bin/opencode" \
    "$pkgdir" amd64 usr/share/zsh/site-functions
}
