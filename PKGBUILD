# Maintainer: Carl Smedstad <carsme@archlinux.org>

pkgname=opencode
pkgver=1.1.49
pkgrel=2
pkgdesc='The open source coding agent'
arch=('x86_64')
url='https://github.com/anomalyco/opencode'
license=('MIT')
depends=(
  'curl'
  'gcc-libs'
  'glibc'
  'icu'
  'ripgrep'
  'tar'
)
makedepends=(
  'bun'
  'git'
)
optdepends=(
  'wl-clipboard: clipboard support on Wayland'
  'xclip: clipboard support on X11'
)
options=('!strip')
source=("git+$url.git#tag=v$pkgver")
b2sums=('ab2c3fc3a1182f0470551510756d4a39ca853db404033393f86cb467f8f270e8300fdd416e60564c507215484b4275e4f6a03cff60f562eb4423cd2d05e993f3')

prepare() {
  cd $pkgname
  bun install --frozen-lockfile
}

build() {
  cd $pkgname/packages/opencode
  OPENCODE_VERSION=$pkgver bun run ./script/build.ts --single
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
  install -vDm755 -t "$pkgdir/usr/bin" packages/opencode/dist/opencode-linux-*/bin/opencode
  install -vDm644 -t "$pkgdir/usr/share/licenses/$pkgname" LICENSE
}
