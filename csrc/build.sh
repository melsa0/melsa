#!/bin/bash
set -e

echo "=== bkg2d — 2D Background Subtraction ==="
echo

echo "[BUILD] Derleniyor..."
gcc -std=c11 -O2 -Wall -Wextra -Iinclude -o bkg2d src/bkg2d.c src/bkg2d_main.c -lm
echo "[OK] bkg2d olusturuldu."
echo

echo "[RUN] Calistiriliyor..."
echo
./bkg2d

echo
echo "=== Tamamlandi ==="
