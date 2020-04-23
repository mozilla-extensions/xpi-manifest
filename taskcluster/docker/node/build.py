#!/usr/bin/env python
from __future__ import print_function

import functools
import glob
import hashlib
import json
import os
from pathlib import Path
import shutil
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


def mkdir(path):
    print("mkdir {}".format(path))
    os.makedirs(path, exist_ok=True)


def get_hash(path, hash_alg="sha256"):
    h = hashlib.new(hash_alg)
    with open(path, "rb") as fh:
        for chunk in iter(functools.partial(fh.read, 4096), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    test_var_set([
        "ARTIFACT_PREFIX",
        "XPI_NAME",
    ])

    artifact_prefix = os.environ["ARTIFACT_PREFIX"]
    xpi_name = os.environ["XPI_NAME"]
    xpi_type = os.environ.get("XPI_TYPE")
    repo_prefix = os.environ.get("REPO_PREFIX", "xpi")
    head_repo_env_var = "{}_HEAD_REPOSITORY".format(repo_prefix.upper())
    test_var_set([head_repo_env_var])

    artifact_dir = "/builds/worker/artifacts"
    base_src_dir = "/builds/worker/checkouts/src"

    package_info = get_package_info()

    revision = get_output(["git", "rev-parse", "HEAD"])

    build_manifest = {
        "name": xpi_name,
        "addon-type": xpi_type,
        "repo": os.environ[head_repo_env_var],
        "revision": revision.decode("utf-8").rstrip(),
        "directory": os.path.relpath(base_src_dir, os.getcwd()),
        "version": package_info["version"],
        "artifacts": [],
    }

    if os.environ.get("XPI_INSTALL_TYPE", "yarn") == "yarn":
        run_command(["yarn", "install", "--frozen-lockfile"])
    else:
        run_command(["npm", "install"])

    run_command(["yarn", "build"])

    if 'XPI_ARTIFACTS' in os.environ:
        xpi_artifacts = os.environ["XPI_ARTIFACTS"].split(";")
    else:
        xpi_artifacts = glob.glob('*.xpi')

    for artifact in xpi_artifacts:
        target_path = os.path.join(artifact_dir, os.path.basename(artifact))
        if not os.path.exists(artifact):
            raise Exception("Missing artifact {}".format(artifact))
        test_is_subdir(os.getcwd(), artifact)
        print("Copying {} to {}".format(artifact, target_path))
        path = os.path.join(artifact_prefix, os.path.basename(target_path))
        artifact_info = {
            "path": os.path.join(artifact_prefix, os.path.basename(artifact)),
            "filesize_bytes": int(os.path.getsize(artifact)),
            "sha256": str(get_hash(artifact)),
        }
        build_manifest["artifacts"].append(artifact_info)
        shutil.copyfile(artifact, target_path)

    with open(os.path.join(artifact_dir, "manifest.json"), "w") as fh:
        fh.write(json.dumps(build_manifest, indent=2, sort_keys=True))


__name__ == '__main__' and main()
