# Maintainer: Carl Smedstad <carsme@archlinux.org>
# Maintainer: Sven-Hendrik Haase <svenstaro@archlinux.org>

pkgbase=opencode
pkgname=(
  'opencode'
  'opencode-daemon'
)
pkgver=1.18.19
pkgrel=1
_commit=2b72179c663cadcb54f54d9f19221b3fb3d11fb6
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
  "git+$url.git#commit=$_commit"
  'downstream-1.18.19.patch'
  'opencode-daemon'
  'opencode-daemon.service'
  'LICENSE'
)
b2sums=('SKIP'
        '56e4b05cd43a353916325072f9f8d5c40559d63c292feddb49d55aaf458f36ba6bdb876ca418effb38a8547d172d788abf71e8738737fe7d019393d000767d85'
        '14b099d6f6e2fb6445a5ed52eb53928559603bb15ba1d504ab0b953e2ab6d7c238be0c8a93974b8ed288b2e8353b840c743968769b24e1dde661d0412ef381ec'
        'a4662a1e2caf4b5d24e4bd41a023c29d27590f5da0c881d4ee5570327e269a78652d98a4aa29f8286f808edb1e94b814d7eb145ff24f00fbf8eb07363617aaa7'
        'a29664104e1ee73ca0aee1d633e9095d92a57c92787f8d8740bdb7211ba3205782ed8677f539bdb8cae3dd75a3694be3132e185fa3fc4b3f401e1f88eb776101')

prepare() {
  cd $pkgbase
  patch -Np1 -i ../downstream-1.18.19.patch
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
