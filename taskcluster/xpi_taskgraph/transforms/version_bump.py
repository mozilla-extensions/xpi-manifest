# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from taskgraph.task import Task
from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import Schema, resolve_keyed_by
from voluptuous import Required
from xpi_taskgraph.xpi_manifest import get_manifest

transforms = TransformSequence()
schema = Schema(
    {
        Required("primary-dependency"): Task,
        Required("worker-type"): str,
        Required("attributes"): dict,
        Required("run-on-tasks-for"): [str],
        Required("lando-repo"): dict,
    },
)
transforms.add_validate(schema)


@transforms.add
def add_version_bump_task(config, tasks):
    manifest = get_manifest()
    for task in tasks:
        if not (config.params.get("xpi_name") and config.params.get("level")):
            continue

        xpi_name = config.params["xpi_name"]
        xpi_manifest = manifest[xpi_name]

        if not xpi_manifest.get("enable-version-bump"):
            continue

        resolve_keyed_by(
            task,
            "lando-repo",
            item_name=f"version-bump-{xpi_name}",
            level=config.params["level"],
        )

        dep = task.pop("primary-dependency")
        lando_repo = task.pop("lando-repo")
        manifest_file = f"{xpi_manifest['directory']}/manifest.json"

        # Compute next_version at graph-generation time from the release version.
        # config.params["version"] is the XPI version just released (e.g. "150.0.0"),
        # which matches the current value in the manifest, so bumping minor gives
        # the correct next value (e.g. "150.1.0").
        major, minor, _patch = config.params["version"].split(".")
        next_version = f"{major}.{int(minor) + 1}.0"

        task["label"] = f"version-bump-{xpi_name}"
        task["description"] = (
            f"Bump {manifest_file} minor version after XPI release"
        )
        task["dependencies"] = {"beetmover": dep.label}
        task["worker"] = {
            "implementation": "scriptworker-lando",
            "lando-repo": lando_repo,
            "actions": [
                {
                    "version-bump": {
                        "file": manifest_file,
                        "next-version": next_version,
                    },
                }
            ],
        }
        # Inherit addon-type from the primary dep so multi_dep grouping works
        # when release-mark-as-shipped depends on this kind.
        task["attributes"] = {
            **dep.attributes,
            **task["attributes"],
        }

        yield task
