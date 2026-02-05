# Maintainer: Carl Smedstad <carsme@archlinux.org>

pkgname=opencode
pkgver=1.1.52
pkgrel=1
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
options=(
  '!debug'
  '!strip'
)
source=("git+$url.git#tag=v$pkgver")
b2sums=('269d5236102174be0868717d47fd91e4081b0faa5e4353a6af608a53bdf8ce991938a2e496c829e929de7a1aa182331910af729dc1ea36740d0ed1789b94ea4e')

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

  SHELL=/bin/bash "$pkgdir/usr/bin/opencode" completion \
    | install -vDm644 /dev/stdin "$pkgdir/usr/share/bash-completion/completions/opencode"
  SHELL=/bin/zsh "$pkgdir/usr/bin/opencode" completion \
    | install -vDm644 /dev/stdin "$pkgdir/usr/share/zsh/site-functions/_opencode"
}
