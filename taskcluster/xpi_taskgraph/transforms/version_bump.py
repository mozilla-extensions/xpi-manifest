# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.dependencies import get_primary_dependency
from taskgraph.util.schema import Schema, resolve_keyed_by
from xpi_taskgraph.xpi_manifest import get_manifest


class VersionBumpSchema(Schema, forbid_unknown_fields=False, kw_only=True):
    worker_type: str
    attributes: dict
    run_on_tasks_for: list[str]
    lando_repo: dict


transforms = TransformSequence()
transforms.add_validate(VersionBumpSchema)


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

        dep = get_primary_dependency(config, task)
        lando_repo = task.pop("lando-repo")
        manifest_file = f"{xpi_manifest['directory']}/manifest.json"

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
                        "bump-files": [manifest_file],
                    },
                }
            ],
        }

        yield task
