# Independent downstream V2 MAIN-only recipe. Canonical source gate: PASS with baseline exceptions.
# Packaging checker and explicit build authorization are still required.
# Upstream Arch maintainers: Carl Smedstad, Sven-Hendrik Haase
pkgname=opencode
pkgver=2.0.24
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
_commit=e7a34f09bfd9134dfade5a8ddb843f7030bc9a69
_srcname=opencode-$_commit
source=(
  "opencode-$pkgver.tar.gz::https://codeload.github.com/anomalyco/opencode/tar.gz/$_commit"
  "downstream-$pkgver.patch"
  'release.json'
  'packaging.py'
)
sha256sums=(
  'a045e473e92a75956585d1957a06707e6757f3da5a3010ef0f4e679f569920de'
  'f767dc47095c7d3e49316b692ee9f09cfe9902a41d1f647cca7a66f6485e4059'
  '0908e621a09d2f53f0df361cedc44c89d29f62667d991316dfbd05d18830b31f'
  '9286d36f67ab08014cad2ab7037bd948b52b053d49072dfac953b86e11dde073'
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
