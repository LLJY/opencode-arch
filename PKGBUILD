# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgname=opencode
pkgver=1.3.4
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
source=("git+$url.git#tag=v$pkgver")
b2sums=('3fec76fe700c9a6b686103b7754e78c9fc7c4f715a8995c875d336505405153431aa181592b6f290e4e80a31e228daac4b81e38a300ac90b407b16d5fa728d28')

prepare() {
  cd $pkgname
  bun install --frozen-lockfile
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
  # Currently broke :(
  # bun test
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
