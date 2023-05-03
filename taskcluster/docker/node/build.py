#!/usr/bin/env python

from datetime import datetime
import functools
import glob
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile


# Changes to this list need to be synced with AMO.
# Please reach out to the Add-ons Operations Team (awagner) before making any changes!
ID_ALLOWLIST = (
    "@mozilla.com",
    "@mozilla.org",
    "@pioneer.mozilla.org",
    "@search.mozilla.org",
    "@shield.mozilla.com",
    "@shield.mozilla.org",
    "@mozillaonline.com",
    "@mozillafoundation.org",
    "@rally.mozilla.org",
    # A temporary special case for aboutsync, which has a "legacy" ID.
    "aboutsync@mhammond.github.com",
)


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


def write_package_info(package_info):
    with open("package.json", "w") as fh:
        json.dump(package_info, fh)
    assert get_package_info() == package_info


def get_buildid():
    now = datetime.utcnow()
    return now.strftime("%Y%m%d.%H%M%S")


def get_buildid_version(version):
    """Version schema check+append a `buildid{buildid}` to ensure unique version."""
    # XXX is there a more precise schema we should verify ourselves against?
    if len(version.split(".")) not in (1, 2, 3):
        raise Exception("{version} has too many version parts!")
    if "buildid" in version:
        raise Exception("{version} already has a buildid specified!")
    buildid_version = f"{version}buildid{get_buildid()}"
    print(f"Buildid version is {buildid_version}")
    return buildid_version


def find_manifests():
    manifest_list = []
    for dir_name, subdir_list, file_list in os.walk("."):
        for dir_ in subdir_list:
            if dir_ in (".git", "node_modules"):
                subdir_list.remove(dir_)
                continue
        if "manifest.json" in file_list:
            manifest_list.append(f"{dir_name}/manifest.json")
    return manifest_list


def find_update_manifest_json(buildid_version):
    """We also have manifest.json files; let's update them as well."""
    for manifest in find_manifests():
        print(f"Updating {manifest} version...")
        with open(manifest) as fh:
            contents = json.load(fh)
        old_version = contents["version"]
        contents["version"] = buildid_version
        with open(manifest, "w") as fh:
            json.dump(contents, fh)
        print(f"    was {old_version}, now {buildid_version}")


def cd(path):
    print(f"Changing directory to {path} ...")
    os.chdir(path)


def mkdir(path):
    print(f"mkdir {path}")
    os.makedirs(path, exist_ok=True)


def get_hash(path, hash_alg="sha256"):
    h = hashlib.new(hash_alg)
    with open(path, "rb") as fh:
        for chunk in iter(functools.partial(fh.read, 4096), b''):
            h.update(chunk)
    return h.hexdigest()


def check_manifest(path, buildid_version):
    xpi = ZipFile(path, "r")
    manifest = {}
    _found = False
    for manifest_name in ("manifest.json", "webextension/manifest.json"):
        try:
            with xpi.open(manifest_name, "r") as f:
                manifest = json.load(f)
        except KeyError:
            print(f"{manifest_name} doesn't exist in {path}...")
            continue
        for _key in ("applications", "browser_specific_settings"):
            _id = manifest.get(_key, {}).get("gecko", {}).get("id", None)
            if _id is None:
                continue
            _found = True
            if not _id.endswith(ID_ALLOWLIST):
                raise Exception(f"{_key}.gecko.id {_id} must end with one of the following suffixes!\n{ID_ALLOWLIST}")
            else:
                print(f"Add-on id {_id} matches the allowlist.")
        if manifest["version"] != buildid_version:
            raise Exception(f"{manifest['version']} doesn't match buildid version {buildid_version}!")
    if not _found:
        raise Exception("Can't find addon ID in manifest.json!")


def main():
    test_var_set([
        "ARTIFACT_PREFIX",
        "XPI_NAME",
    ])

    artifact_prefix = os.environ["ARTIFACT_PREFIX"]
    xpi_name = os.environ["XPI_NAME"]
    xpi_type = os.environ.get("XPI_TYPE")
    repo_prefix = os.environ.get("REPO_PREFIX", "xpi")
    head_repo_env_var = f"{repo_prefix.upper()}_HEAD_REPOSITORY"
    test_var_set([head_repo_env_var])

    artifact_dir = "/builds/worker/artifacts"
    base_src_dir = "/builds/worker/checkouts/src"

    package_info = get_package_info()

    revision = get_output(["git", "rev-parse", "HEAD"])
    orig_version = package_info["version"]
    buildid_version = get_buildid_version(orig_version)

    # Make sure we use the buildid_version during the build
    package_info["version"] = buildid_version
    print(f"Updating package.json version from {orig_version} to {buildid_version}...")
    write_package_info(package_info)
    find_update_manifest_json(buildid_version)

    build_manifest = {
        "name": xpi_name,
        "addon-type": xpi_type,
        "repo": os.environ[head_repo_env_var],
        "revision": str(revision.rstrip()),
        "directory": os.path.relpath(base_src_dir, os.getcwd()),
        "version": buildid_version,
        "artifacts": [],
    }

    if os.environ.get("XPI_INSTALL_TYPE", "yarn") == "yarn":
        run_command(["yarn", "install", "--frozen-lockfile"])
        run_command(["yarn", "build"])
    else:
        run_command(["npm", "install"])
        run_command(["npm", "run", "build"])

    if 'XPI_ARTIFACTS' in os.environ:
        xpi_artifacts = os.environ["XPI_ARTIFACTS"].split(";")
    else:
        xpi_artifacts = glob.glob('*.xpi') + glob.glob("**/*.xpi")

    all_paths = []
    for artifact in xpi_artifacts:
        target_path = os.path.join(artifact_dir, os.path.basename(artifact))
        if target_path in all_paths:
            raise Exception(f"{target_path} already exists!")
        all_paths.append(target_path)
        if not os.path.exists(artifact):
            raise Exception(f"Missing artifact {artifact}")
        test_is_subdir(os.getcwd(), artifact)
        print(f"Copying {artifact} to {target_path}")
        artifact_info = {
            "path": os.path.join(artifact_prefix, os.path.basename(artifact)),
            "filesize_bytes": int(os.path.getsize(artifact)),
            "sha256": str(get_hash(artifact)),
        }
        build_manifest["artifacts"].append(artifact_info)
        shutil.copyfile(artifact, target_path)
        check_manifest(target_path, buildid_version)

    with open(os.path.join(artifact_dir, "manifest.json"), "w") as fh:
        fh.write(json.dumps(build_manifest, indent=2, sort_keys=True))


__name__ == '__main__' and main()
