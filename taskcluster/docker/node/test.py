#!/usr/bin/env python
from __future__ import print_function

import functools
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def test_is_subdir(parent_dir, target_dir):
    p1 = Path(os.path.realpath(parent_dir))
    p2 = Path(os.path.realpath(target_dir))
    if p1 not in p2.parents:
        raise Exception("{} is not under {}!".format(target_dir, parent_dir))


def test_var_set(varnames):
    """Test for `varnames` in `os.environ`"""
    errors = []
    for varname in varnames:
        if varname not in os.environ:
            errors.append(("error: {} is not set".format(varname)))
    if errors:
        print("\n".join(errors))
        sys.exit(1)


def run_command(command, **kwargs):
    print("Running {} ...".format(command))
    subprocess.check_call(command, **kwargs)


def get_output(command, **kwargs):
    print("Getting output from {} ...".format(command))
    return subprocess.check_output(command, **kwargs)


def get_package_info():
    if not os.path.exists("package.json"):
        raise Exception("Can't find package.json in {}!".format(os.getcwd()))
    with open("package.json") as fh:
        contents = json.load(fh)
    return contents


def cd(path):
    print("Changing directory to {} ...".format(path))
    os.chdir(path)


def get_hash(path, hash_alg="sha256"):
    h = hashlib.new(hash_alg)
    with open(path, "rb") as fh:
        for chunk in iter(functools.partial(fh.read, 4096), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.environ.get("XPI_INSTALL_TYPE", "yarn") == "yarn":
        run_command(["yarn", "install", "--frozen-lockfile"])
    else:
        run_command(["npm", "install"])

    commands = ["test"]
    if len(sys.argv) != 1:
        commands = sys.argv[1:]

    for command in commands:
        run_command(["yarn", command])


__name__ == '__main__' and main()
