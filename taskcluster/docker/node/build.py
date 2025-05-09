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
    # A temporary special case for aboutsync, which has a "legacy" ID.
    "aboutsync@mhammond.github.com",
    # Allow https://github.com/mozilla-extensions/privileged-test-xpi.
    "test@tests.mozilla.org",
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


def get_buildid():
    now = datetime.utcnow()
    # note the `-` (hyphen) in `%-H`
    # this removes the leading zero
    # from the hour (leading zeros are not allowed)
    return now.strftime("%Y%m%d.%-H%M%S")


def get_buildid_version(version):
    """Check the version's formating and append `date.time` as a buildid to ensure a unique version.
    The addon's in-tree manifest files specify `major.minor.0`.
    The format of the resulting version field is:
        <number>.<number>.%Y%m%d.%-H%M%S
    """
    parts = version.split(".")
    if len(parts) not in (1, 2, 3):
        raise Exception(
            f"{version} has an invalid number of version parts! The pipeline supports a `major.minor.0` version format in the extension's manifest"
        )
    # Append (or override) the last two parts of the version with a timestamp to ensure a unique version that is compliant with MV3.
    if len(parts) == 3:
        # Print a noisy warning if we override an element in the extension's version field.
        if parts[2] != "0":
            msg = f"! THE 3RD ELEMENT IN THE VERSION {version} IS {parts[2]} NOT 0. THIS VALUE IS OVERRIDEN BY THE PIPELINE TO CREATE A UNIQUE VERSION !"
            raise ValueError(f"\n{'!' * len(msg)}\n\n{msg}\n\n{'!' * len(msg)}")
        parts = parts[:2]
        version = ".".join(parts)
    buildid_version = f"{version}.{get_buildid()}"
    print(f"Updating version from {version} to {buildid_version}...")
    return buildid_version


def find_manifests():
    for dir_name, subdir_list, file_list in os.walk("."):
        for dir_ in subdir_list:
            if dir_ in (".git", "node_modules"):
                subdir_list.remove(dir_)
                continue
        if "manifest.json" in file_list:
            yield f"{dir_name}/manifest.json"


def get_and_update_version() -> str:
    """Find the original version number, change it to include a buildid,
    then update all references to the version.

    Returns:
        str: the new version with a buildid.
    """
    orig_version = None
    new_version = None
    has_package_json = os.path.isfile("package.json")

    # If there's a package.json file, the version there will overwrite
    # everything else to preserve backwards compatibility. Otherwise, we grab
    # the version from the manifest.json file(s). If there are more than one,
    # their versions must be internally consistent.
    if has_package_json:
        with open("package.json") as fh:
            package_info = json.load(fh)

        orig_version = package_info["version"]
        new_version = get_buildid_version(orig_version)
        package_info["version"] = new_version

        with open("package.json", "w") as fh:
            json.dump(package_info, fh)

    for manifest in find_manifests():
        with open(manifest) as fh:
            contents = json.load(fh)

        if "version" not in contents:
            continue

        if not orig_version:
            orig_version = contents["version"]
            new_version = get_buildid_version(orig_version)

        elif not has_package_json and contents["version"] != orig_version:
            raise Exception(
                "Version mismatch between some manifest.json files, "
                f"{orig_version} != {contents['version']}!"
            )

        assert new_version
        contents["version"] = new_version

        print(f"Writing new version to {manifest}")
        with open(manifest, "w") as fh:
            json.dump(contents, fh)

    if not new_version:
        raise Exception(
            "Could not detect a version number in any manifest.json / package.json files!"
        )

    return new_version


def cd(path):
    print(f"Changing directory to {path} ...")
    os.chdir(path)


def mkdir(path):
    print(f"mkdir {path}")
    os.makedirs(path, exist_ok=True)


def get_hash(path, hash_alg="sha256"):
    h = hashlib.new(hash_alg)
    with open(path, "rb") as fh:
        for chunk in iter(functools.partial(fh.read, 4096), b""):
            h.update(chunk)
    return h.hexdigest()


def is_version_mv3_compliant(version):
    # Split the version string by dots
    parts = version.split(".")

    # Check if there are 1 to 4 parts
    if len(parts) < 1 or len(parts) > 4:
        return False

    for part in parts:
        # Check if the part is a number
        if not part.isdigit():
            return False
        # Check that the part doesn't have leading zeros (unless it's "0")
        if part[0] == "0" and part != "0":
            return False
        # Convert part to integer to check the digit count
        num = int(part)
        # Check if the integer has more than 9 digits
        if num > 999999999:
            return False

    return True


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
                raise Exception(
                    f"{_key}.gecko.id {_id} must end with one of the following suffixes!\n{ID_ALLOWLIST}"
                )
            else:
                print(f"Add-on id {_id} matches the allowlist.")
        if manifest["version"] != buildid_version:
            raise Exception(
                f"{manifest['version']} doesn't match buildid version {buildid_version}!"
            )
        if manifest["manifest_version"] == 3 and not is_version_mv3_compliant(
            manifest["version"]
        ):
            raise Exception(
                (
                    f"The version in {manifest_name} is {manifest['version']}, which is not MV3 compliant. "
                    "The value must be a string with 1 to 4 numbers separated by dots (e.g., 1.2.3.4). "
                    "Each number can have up to 9 digits and leading zeros before another digit are not allowed "
                    "(e.g., 2.01 is forbidden, but 0.2, 2.0.1, and 2.1 are allowed)."
                )
            )
    if not _found:
        raise Exception("Can't find addon ID in manifest.json!")


def main():
    test_var_set(
        [
            "ARTIFACT_PREFIX",
            "XPI_NAME",
        ]
    )

    artifact_prefix = os.environ["ARTIFACT_PREFIX"]
    xpi_name = os.environ["XPI_NAME"]
    xpi_type = os.environ.get("XPI_TYPE")
    repo_prefix = os.environ.get("REPO_PREFIX", "xpi")
    head_repo_env_var = f"{repo_prefix.upper()}_HEAD_REPOSITORY"
    test_var_set([head_repo_env_var])

    artifact_dir = "/builds/worker/artifacts"
    base_src_dir = "/builds/worker/checkouts/src"

    revision = get_output(["git", "rev-parse", "HEAD"])

    # Make sure we update the version to include a buildid.
    buildid_version = get_and_update_version()

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

    if "XPI_ARTIFACTS" in os.environ:
        xpi_artifacts = os.environ["XPI_ARTIFACTS"].split(";")
    else:
        xpi_artifacts = glob.glob("*.xpi") + glob.glob("**/*.xpi")

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


__name__ == "__main__" and main()
