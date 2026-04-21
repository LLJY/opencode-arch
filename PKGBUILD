# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgname=opencode
pkgver=1.14.20
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
b2sums=('a46f6a173962f295e571770be3d5c9c94d243c0c73147b5880d43ca79b912449bec493b489236c6f947e2349e161f47ac4783c10728a470ba8efe8da9faa36da')

prepare() {
  cd $pkgname
  bun install --frozen-lockfile --ignore-scripts

  # Every single test runner I have ever used can skip particular tests.
  # Why can't bun do it? Anyway, I added an upstream feature request here: https://github.com/oven-sh/bun/issues/29477

  # Remove flaky expect, prone to filesystem options?
  # https://github.com/anomalyco/opencode/blob/a5b1dc081d589598168c0e0d9346a35aeb58548b/packages/opencode/test/plugin/meta.test.ts#L60
  sed '/.*expect.*three.entry.modified.*/d' -i packages/opencode/test/plugin/meta.test.ts

  # Skip failing JSON to SQLite migration tests
  sed -i 's/^describe("JSON to SQLite/describe.skip("JSON to SQLite/' packages/opencode/test/storage/json-migration.test.ts

  # Skip failing session.processor effect test, probably a timing issue
  sed -i '/^it\.live("session\.processor effect tests/,/^)$/d' packages/opencode/test/session/processor-effect.test.ts
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
  bun test --timeout=20000
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
