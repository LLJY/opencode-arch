# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgname=opencode
pkgver=1.3.5
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
source=("git+$url.git#tag=v$pkgver")
b2sums=('2134e1d053c0ed10573348ccc5c1ebe0495bdff2de5c38bf6d00aa82a59b963c5a8fcbff0dda8f53c78f652a214ba100ccaad3d4646eba8d9b40b7b73b071fd6')

prepare() {
  cd $pkgname
  bun install --frozen-lockfile

  # Remove flaky expect, prone to filesystem options?
  # https://github.com/anomalyco/opencode/blob/a5b1dc081d589598168c0e0d9346a35aeb58548b/packages/opencode/test/plugin/meta.test.ts#L60
  sed '/.*expect.*three.entry.modified.*/d' -i packages/opencode/test/plugin/meta.test.ts
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
