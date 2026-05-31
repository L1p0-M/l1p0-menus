# Maintainer: L1p0 <lipovicsmartin@l1p0-industries.hu>
pkgname=l1p0-menus-git
pkgver=1.0.0.r0.g1234567
pkgrel=1
pkgdesc="GTK4 Layer Shell menus for Hyprland written in Python"
arch=('any')
url="https://github.com/L1p0-M/l1p0-menus"
license=('MIT')
depends=(
    'python'
    'python-gobject'
    'gtk4'
    'gtk4-layer-shell'
    'python-pulsectl'
    'bluez'
    'networkmanager'
    'python-requests'
)
makedepends=(
    'git'
    'glib2-devel'
    'python-build'
    'python-installer'
    'python-hatchling'
    'python-wheel'
)
provides=('l1p0-menus')
conflicts=('l1p0-menus')
source=("git+${url}.git")
sha256sums=('SKIP')

pkgver() {
  cd "${pkgname%-git}"
  git describe --long --tags | sed 's/-g/.r/;s/-/./g'
}

build() {
  cd "${pkgname%-git}"
  python -m build --wheel --no-isolation
}

package() {
  cd "${pkgname%-git}"
  python -m installer --destdir="${pkgdir}" dist/*.whl
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
