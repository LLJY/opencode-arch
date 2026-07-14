# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgname=opencode
pkgver=1.17.20
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
b2sums=('ee8eb144ee14ff8ac0beaabff8b1221fcdabc8570fdae59b2ed7d25abeef2c17ec011f2e91a0f726369c875f8d175144a5c1807636ab1c365db91eecfd7b130c')

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
