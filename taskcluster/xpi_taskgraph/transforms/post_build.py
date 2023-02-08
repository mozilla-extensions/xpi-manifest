# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Apply some defaults and minor modifications to the tasks defined in the build
kind.
"""

import os

from taskgraph.transforms.base import TransformSequence
from xpi_taskgraph.xpi_manifest import get_manifest

transforms = TransformSequence()


@transforms.add
def test_tasks_from_manifest(config, tasks):
    manifest = get_manifest()
    for task in tasks:
        dep = task.pop("primary-dependency")
        task["attributes"] = dep.attributes.copy()
        task["dependencies"] = {"build": dep.label}
        xpi_name = dep.task["extra"]["xpi-name"]
        xpi_revision = config.params.get("xpi_revision")
        task.setdefault("extra", {})["xpi-name"] = xpi_name
        xpi_config = manifest[xpi_name]
        if not xpi_config.get("active"):
            continue
        env = task.setdefault("worker", {}).setdefault("env", {})
        run = task.setdefault("run", {})
        checkout = run.setdefault("checkout", {})
        checkout_config = checkout.setdefault(xpi_config["repo-prefix"], {})
        env["REPO_PREFIX"] = xpi_config["repo-prefix"]
        checkout_config["path"] = "/builds/worker/checkouts/vcs"
        if "branch" in xpi_config:
            checkout_config["head_ref"] = xpi_config["branch"]
        if "directory" in xpi_config:
            run["cwd"] = "{checkout}/%s" % xpi_config["directory"]
        if xpi_revision:
            checkout_config["head_rev"] = xpi_revision
        if "docker-image" in xpi_config:
            task["worker"]["docker-image"]["in-tree"] = xpi_config["docker-image"]
        task["label"] = f"{config.kind}-{xpi_name}"
        if xpi_config.get("private-repo"):
            checkout_config["ssh_secret_name"] = config.graph_config[
                "github_clone_secret"
            ]
            artifact_prefix = "xpi/build"
            task["worker"]["taskcluster-proxy"] = True
        else:
            artifact_prefix = "public/build"
        env["ARTIFACT_PREFIX"] = artifact_prefix
        if xpi_config.get("install-type"):
            env["XPI_INSTALL_TYPE"] = xpi_config["install-type"]

        if task.get("only-for-formats"):
            if xpi_config.get("addon-type") not in task.pop("only-for-formats"):
                continue
            # This `xpis` dict is created in `transforms/build.py`.
            artifacts = list(task["attributes"]["xpis"].values())
            # We take the name of the XPI from the list of artifacts because
            # `xpi_name` might not be used for generated XPI filenames. Also,
            # we only support the first artifact.
            artifact = artifacts[0]
            xpi_file = os.path.basename(artifact)

            env["XPI_URL"] = {"artifact-reference": f"<build/{artifact}>"}
            run["command"] = run["command"].format(xpi_file=xpi_file)

        yield task
