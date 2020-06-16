# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Apply some defaults and minor modifications to the jobs defined in the build
kind.
"""

from __future__ import absolute_import, print_function, unicode_literals
from copy import deepcopy
import os

from taskgraph.transforms.base import TransformSequence
from xpi_taskgraph.xpi_manifest import get_manifest


transforms = TransformSequence()


@transforms.add
def tasks_from_manifest(config, jobs):
    manifest = get_manifest()
    xpi_name = config.params.get("xpi_name")
    xpi_revision = None
    if xpi_name:
        xpi_revision = config.params.get("xpi_revision")
    for job in jobs:
        for xpi_config in manifest.values():
            if not xpi_config.get("active"):
                continue
            if xpi_name and xpi_config["manifest_name"] != xpi_name:
                continue
            task = deepcopy(job)
            env = task.setdefault("worker", {}).setdefault("env", {})
            run = task.setdefault("run", {})
            checkout = run.setdefault("checkout", {})
            checkout_config = checkout.setdefault(xpi_config['repo-prefix'], {})
            env['REPO_PREFIX'] = xpi_config['repo-prefix']
            checkout_config['path'] = '/builds/worker/checkouts/src'
            if 'branch' in xpi_config:
                checkout_config['head_ref'] = xpi_config['branch']
            if 'directory' in xpi_config:
                run['cwd'] = '{checkout}/%s' % xpi_config['directory']
            if xpi_revision:
                checkout_config['head_rev'] = xpi_revision
            task["label"] = "{}-{}".format(config.kind, xpi_config["manifest_name"])
            env["XPI_NAME"] = xpi_config["manifest_name"]
            task.setdefault("extra", {})["xpi-name"] = xpi_config["manifest_name"]
            env["XPI_TYPE"] = xpi_config["addon-type"]
            if xpi_config.get("private-repo"):
                checkout_config['ssh_secret_name'] = config.graph_config["github_clone_secret"]
                artifact_prefix = "xpi/build"
            else:
                artifact_prefix = "public/build"
            env["ARTIFACT_PREFIX"] = artifact_prefix
            if xpi_config.get("install-type"):
                env["XPI_INSTALL_TYPE"] = xpi_config["install-type"]
            task.setdefault("attributes", {})["addon-type"] = xpi_config["addon-type"]
            task.setdefault("attributes", {})["xpis"] = {}
            artifacts = task.setdefault("worker", {}).setdefault("artifacts", [])
            for artifact in xpi_config["artifacts"]:
                artifact_name = "{}/{}".format(
                    artifact_prefix, os.path.basename(artifact)
                )
                artifacts.append({
                    "type": "directory",
                    "name": artifact_prefix,
                    "path": "/builds/worker/artifacts",
                })
                task["attributes"]["xpis"][artifact] = artifact_name
            env["XPI_ARTIFACTS"] = ";".join(xpi_config["artifacts"])

            yield task
