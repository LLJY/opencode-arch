# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgname=opencode
pkgver=1.18.21
pkgrel=1
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
#checkdepends=(
#  'nodejs-lts-jod'
#)
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
source=("git+$url.git#tag=v$pkgver")
b2sums=('d675e4973c704432d43ac52d3642f77d766dafa524100e470332b785a082757621b848bf7bb06df7634638d24ec1f7f33f1bae7c2c47cc34d51c3fd65fb17aa1')

prepare() {
  cd $pkgname
  bun install --frozen-lockfile --ignore-scripts
}

build() {
  cd $pkgname/packages/opencode
  OPENCODE_VERSION=$pkgver bun run ./script/build.ts --single --baseline --skip-install
}

#check() {
#  cd $pkgname/packages/opencode

  # I _really_ tried to make the tests work but I'm getting 100s of failures, mostly due to this I think:
  # https://github.com/oven-sh/bun/issues/30014
  # Let's revisit this once the bug is fixed.
  #
  # export GIT_CONFIG_GLOBAL=$PWD/gitconfig
  # git config --global user.email "builduser@archlinux.org"
  # git config --global user.name "Build User"
  # bun test --timeout=20000 --parallel
#}

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
