#!/bin/bash

# node-14 images (and likely older) require this /etc/apt/sources.list change
# to install a compatible version of python 3. node-16 images break if we
# run this step. Adding this helper script to only run this step if our node
# major version is an int, and less-than-or-equal-to 14.

set -x
set -e

test `echo $1 | cut -d'.' -f 1` -le 14 && (echo "deb http://deb.debian.org/debian testing main" >> /etc/apt/sources.list) || echo "Skipping py3 workaround"