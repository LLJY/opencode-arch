# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgname=opencode
pkgver=2.0.4
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
b2sums=('c6e98af12415f5cd9b66732565cb1d3fdafb839eeba7504758f8aa3211e1ee80161f14487600c5a9a2e67c6074c3440686b1948a0f32e5e6b5795edefad4f7a6')

prepare() {
  cd $pkgname
  sed -i 's|"packageManager": "bun@1.4.2"|"packageManager": "bun@1.4.0"|' package.json
  bun install --frozen-lockfile --ignore-scripts
}

build() {
  cd $pkgname/packages/cli
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
  aarch64) dir=cli-linux-arm64 ;;
  x86_64) dir=cli-linux-x64-baseline ;;
  esac
  install -vDm755 -t "$pkgdir/usr/bin" "packages/cli/dist/$dir/bin/opencode"

  install -vDm644 -t "$pkgdir/usr/share/licenses/$pkgname" LICENSE

  "$pkgdir/usr/bin/opencode" --completions bash \
    | install -vDm644 /dev/stdin "$pkgdir/usr/share/bash-completion/completions/opencode"
  "$pkgdir/usr/bin/opencode" --completions zsh \
    | install -vDm644 /dev/stdin "$pkgdir/usr/share/zsh/site-functions/_opencode"
}
