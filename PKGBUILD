# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgname=opencode
pkgver=1.3.3
pkgrel=2
pkgdesc='The open source coding agent'
arch=('x86_64')
url='https://github.com/anomalyco/opencode'
license=('MIT')
depends=(
  'curl'
  'glibc'
  'icu'
  'ripgrep'
  'tar'
)
checkdepends=(
  'nodejs-lts-jod'
)
makedepends=(
  'bun'
  'git'
)
optdepends=(
  'wl-clipboard: clipboard support on Wayland'
  'xclip: clipboard support on X11'
)
options=(
  '!debug'
  '!strip'
)
source=("git+$url.git#tag=v$pkgver"
        $pkgname-fix-prompt.patch::https://patch-diff.githubusercontent.com/raw/anomalyco/opencode/pull/18584.patch)
b2sums=('2219334ce1f1b1839e78058e4481a1a6ae782620d7947ce850e8fe6cebc4d979a00b87f58d190d257200e64deb67a74e6bf92124ab5e8d0391c1e94d7581fefb'
        '83894805a7683c2bdd880167d85dc21b9a1bc881cc2a91079a2c8a93290ffdaf07b3640440f0fdfce90eb17ce00336e9e59c1da737d024361e3712ae7a467a07')

prepare() {
  cd $pkgname
  bun install --frozen-lockfile

  # Fix broken --prompt
  patch -Np1 -i "$srcdir"/$pkgname-fix-prompt.patch
}

build() {
  cd $pkgname/packages/opencode
  OPENCODE_VERSION=$pkgver bun run ./script/build.ts --single --baseline
}

check() {
  cd $pkgname/packages/opencode
  export GIT_CONFIG_GLOBAL=$PWD/gitconfig
  git config --global user.email "builduser@archlinux.org"
  git config --global user.name "Build User"
  bun test
}

package() {
  cd $pkgname
  case $CARCH in
  aarch64) dir=opencode-linux-arm64 ;;
  x86_64) dir=opencode-linux-x64-baseline ;;
  esac
  install -vDm755 -t "$pkgdir/usr/bin" "packages/opencode/dist/$dir/bin/opencode"

  install -vDm644 -t "$pkgdir/usr/share/licenses/$pkgname" LICENSE

  SHELL=/bin/bash "$pkgdir/usr/bin/opencode" completion \
    | install -vDm644 /dev/stdin "$pkgdir/usr/share/bash-completion/completions/opencode"
  SHELL=/bin/zsh "$pkgdir/usr/bin/opencode" completion \
    | install -vDm644 /dev/stdin "$pkgdir/usr/share/zsh/site-functions/_opencode"
}
