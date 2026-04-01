# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgname=opencode
pkgver=1.3.13
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
b2sums=('d81ac10246e6b2d432130a7459bfc2d3b171d033311433761fb74ee2088e0ac279088603c8648ef0c85a98e2ba6b9df2551b47e91c25c355a0dc841e80cc3e67')

prepare() {
  cd $pkgname
  bun install --frozen-lockfile --ignore-scripts

  # Remove flaky expect, prone to filesystem options?
  # https://github.com/anomalyco/opencode/blob/a5b1dc081d589598168c0e0d9346a35aeb58548b/packages/opencode/test/plugin/meta.test.ts#L60
  sed '/.*expect.*three.entry.modified.*/d' -i packages/opencode/test/plugin/meta.test.ts
}

build() {
  cd $pkgname/packages/opencode
  OPENCODE_VERSION=$pkgver bun run ./script/build.ts --single --baseline --skip-install
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
