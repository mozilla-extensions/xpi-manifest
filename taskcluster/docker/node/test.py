#!/usr/bin/env python

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
        raise Exception(f"{target_dir} is not under {parent_dir}!")


def test_var_set(varnames):
    """Test for `varnames` in `os.environ`"""
    errors = []
    for varname in varnames:
        if varname not in os.environ:
            errors.append(f"error: {varname} is not set")
    if errors:
        print("\n".join(errors))
        sys.exit(1)


def run_command(command, **kwargs):
    print(f"Running {command} ...")
    subprocess.check_call(command, **kwargs)


def get_output(command, **kwargs):
    print(f"Getting output from {command} ...")
    return subprocess.check_output(command, **kwargs)


def get_package_info():
    if not os.path.exists("package.json"):
        raise Exception(f"Can't find package.json in {os.getcwd()}!")
    with open("package.json") as fh:
        contents = json.load(fh)
    return contents


def cd(path):
    print(f"Changing directory to {path} ...")
    os.chdir(path)


def get_hash(path, hash_alg="sha256"):
    h = hashlib.new(hash_alg)
    with open(path, "rb") as fh:
        for chunk in iter(functools.partial(fh.read, 4096), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    install_type = os.environ.get("XPI_INSTALL_TYPE", "yarn")

    match install_type:
        case "yarn":
            run_command(["yarn", "install", "--frozen-lockfile"])
        case "npm":
            run_command(["npm", "install"])

    commands = []
    if len(sys.argv) != 1:
        commands = sys.argv[1:]
    elif install_type != "mach":
        package_info = get_package_info()
        if "test" in package_info.get("scripts", {}):
            commands = ["test"]

    if not commands:        
        print("Could not determine test command; noop")

    cmd_prefix = []
    match install_type:
        case "yarn":
            cmd_prefix = ["yarn"]
        case "npm":
            cmd_prefix = ["npm", "run"]
        case "mach":
            cmd_prefix = ["./mach"]

    for command in commands:
        run_command(cmd_prefix + [command])


if __name__ == '__main__':
    sys.exit(main())
