# Independent downstream V2 MAIN-only recipe. Canonical source gate: PASS.
# Packaging checker and explicit build authorization are still required.
# Upstream Arch maintainers: Carl Smedstad, Sven-Hendrik Haase
pkgname=opencode
pkgver=2.0.23
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
_commit=0fd7e2829449b052abf0078666669302923d77af
_srcname=opencode-$_commit
source=(
  "opencode-$pkgver.tar.gz::https://codeload.github.com/anomalyco/opencode/tar.gz/$_commit"
  "downstream-$pkgver.patch"
  'release.json'
  'packaging.py'
)
sha256sums=(
  'b2af2db700690328f5a9382124cfc63bda4821f3fc9e79c0edbb614acdee46a9'
  '76c84f496c6b8bcdf999b0e6988a5796fb7aae948c653ddaaa1ff39c2545b4a6'
  'ff87ce034da890652e0e75f83f67e252cbe7a24e695e017865ce3d83cb031528'
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
