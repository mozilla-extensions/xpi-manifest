# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from copy import deepcopy
import glob
import os
from functools import lru_cache

from taskgraph.config import load_graph_config
from taskgraph.util.schema import validate_schema
from taskgraph.util import yaml
from taskgraph.util.readonlydict import ReadOnlyDict
from voluptuous import Optional, Required, Schema, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ROOT = os.path.join(BASE_DIR, "taskcluster")
MANIFEST_DIR = os.path.join(BASE_DIR, "manifests")


base_schema = Schema(
    {
        Required("manifest_name"): str,
        Optional("description"): str,
        Required("repo-prefix"): str,
        Optional("directory"): str,
        Optional("active"): bool,
        Optional("additional-emails"): [str],
        Optional("private-repo"): bool,
        Optional("branch"): str,
        Optional("docker-image"): str,
        Required("artifacts"): [str],
        # normandy-privileged is deprecated
        Required("addon-type"): Any(
            "mozillaonline-privileged", "normandy-privileged", "privileged", "system"
        ),
        Optional("install-type"): Any("npm", "yarn"),
        Optional("enable-github-release"): bool,
        Optional("release-tag"): str,
        Optional("release-name"): str,
    }
)


def check_manifest(xpi_config, graph_config):
    if xpi_config["repo-prefix"] not in graph_config["taskgraph"]["repositories"]:
        raise Exception(
            "{} repo-prefix not in graph_config!".format(xpi_config["manifest_name"])
        )
    # No '-' allowed in repo-prefixes
    if "-" in xpi_config["repo-prefix"]:
        raise Exception(
            "{} repo-prefix contains a '-': {}".format(
                xpi_config["manifest_name"], xpi_config["repo-prefix"]
            )
        )


@lru_cache(maxsize=None)
def get_manifest():
    manifest_paths = glob.glob(os.path.join(MANIFEST_DIR, "*.yml"))
    all_manifests = {}
    graph_config = load_graph_config(ROOT)
    for path in manifest_paths:
        rw_manifest = yaml.load_yaml(path)
        manifest_name = os.path.basename(path).replace(".yml", "")
        rw_manifest["manifest_name"] = manifest_name
        validate_schema(base_schema, deepcopy(rw_manifest), "Invalid manifest:")
        check_manifest(deepcopy(rw_manifest), graph_config)
        rw_manifest["artifacts"] = tuple(rw_manifest["artifacts"])
        assert manifest_name not in all_manifests
        all_manifests[manifest_name] = ReadOnlyDict(rw_manifest)
    return ReadOnlyDict(all_manifests)
