#!/bin/sh
VERSION='3.0'
ARCHIVE="v${VERSION}.tar.gz"
wget -N "https://github.com/pgsql-io/multicorn2/archive/refs/tags/${ARCHIVE}"
tar -xvf "${ARCHIVE}"
rm -f "${ARCHIVE}"
cd "multicorn2-${VERSION}"
make && sudo make install