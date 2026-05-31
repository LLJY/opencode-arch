# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgbase=opencode
pkgname=(
  'opencode'
  'opencode-daemon'
)
pkgver=1.15.13
pkgrel=1
pkgdesc='The open source coding agent'
arch=('x86_64')
url='https://github.com/anomalyco/opencode'
license=('MIT')
checkdepends=(
  'nodejs-lts-jod'
)
makedepends=(
  'bun'
  'git'
)
options=(
  '!debug'
  '!strip'
)
source=(
  "git+$url.git#tag=v$pkgver"
  'downstream-1.15.13.patch'
  'opencode-daemon'
  'opencode-daemon.service'
  'LICENSE'
)
b2sums=('fddf7bb60f5d3f5a0c1790798e73349934d2b12646542aa66095368293ddeff627b10a724bb06180070014929f37c53ffd2721698eea7ab689c32adb8b6f2256'
        'd33dfb2795423a39d9da4f62f362ce0245f9e536773033890660e2d9ba935d2606a569dff17846122376ac99e57bf41030a59ec158a1ede6bfbea4fc29bc501c'
        'a2e4e1d739dafced870982347c00c017c6040dd281893df6fd181090348d7dd771cbaa99065f2d27a4ec93be9aca24ca9510f6b63e704407e3d142ca3cf5f2c9'
        'e6a605c6838925a84f6cedbabf7dd02923e83e12c492db08bf58141ae08d46d1d046af5765f099d1d804aea38a84f5d563ae34abeea5d5fb3142d2894ddfe480'
        'a29664104e1ee73ca0aee1d633e9095d92a57c92787f8d8740bdb7211ba3205782ed8677f539bdb8cae3dd75a3694be3132e185fa3fc4b3f401e1f88eb776101')

prepare() {
  cd $pkgbase
  patch -Np1 -i ../downstream-1.15.13.patch
  bun install --frozen-lockfile --ignore-scripts
}

build() {
  cd $pkgbase/packages/opencode
  OPENCODE_VERSION=$pkgver bun run ./script/build.ts --single --baseline --skip-install
}

check() {
  cd $pkgbase/packages/opencode

  # I _really_ tried to make the tests work but I'm getting 100s of failures, mostly due to this I think:
  # https://github.com/oven-sh/bun/issues/30014
  # Let's revisit this once the bug is fixed.
  #
  # export GIT_CONFIG_GLOBAL=$PWD/gitconfig
  # git config --global user.email "builduser@archlinux.org"
  # git config --global user.name "Build User"
  # bun test --timeout=20000 --parallel
}

package_opencode() {
  depends=(
    'curl'
    'glibc'
    'icu'
    'ripgrep'
    'tar'
  )
  optdepends=(
    'wl-clipboard: clipboard support on Wayland'
    'xclip: clipboard support on X11'
  )

  cd $pkgbase
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

package_opencode-daemon() {
  pkgdesc='Systemd user service wrapper for opencode'
  license=('0BSD')
  depends=(
    "opencode=$pkgver-$pkgrel"
    'systemd'
  )

  install -vDm755 "$srcdir/opencode-daemon" "$pkgdir/usr/bin/opencode-daemon"
  ln -sf opencode-daemon "$pkgdir/usr/bin/ocd"
  install -vDm644 "$srcdir/opencode-daemon.service" "$pkgdir/usr/lib/systemd/user/opencode-daemon.service"
  install -vDm644 "$srcdir/LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
