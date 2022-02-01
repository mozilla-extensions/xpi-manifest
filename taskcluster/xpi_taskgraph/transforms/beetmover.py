# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from os.path import basename

from taskgraph.task import Task
from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import resolve_keyed_by
from voluptuous import Required, Schema
from xpi_taskgraph.xpi_manifest import get_manifest

transforms = TransformSequence()
schema = Schema(
    {
        Required("primary-dependency"): Task,
        Required("worker-type"): str,
        Required("attributes"): dict,
        Required("bucket-scope"): dict,
        Required("run-on-tasks-for"): [str],
    },
)
transforms = TransformSequence()
transforms.add_validate(schema)


@transforms.add
def add_beetmover_worker_config(config, tasks):
    if (
        config.params.get("version")
        and config.params.get("xpi_name")
        and config.params.get("head_ref")
        and config.params.get("moz_build_date")
        and config.params.get("level")
    ):
        manifest = get_manifest()
        xpi_name = config.params["xpi_name"]
        xpi_manifest = manifest[xpi_name]
        xpi_addon_type = xpi_manifest["addon-type"]
        if xpi_addon_type == "system":
            xpi_version = config.params["version"]
            xpi_destination = (
                "pub/system-addons/{xpi_name}/"
                "{xpi_name}%mozilla.org-{xpi_version}-{build_id}.xpi"
            ).format(
                xpi_name=xpi_name,
                xpi_version=xpi_version,
                build_id=config.params["moz_build_date"],
            )
            xpi_destinations = [xpi_destination]
            task_label = f"beetmover-{xpi_name}"
            task_description = (
                "Upload the signed {xpi_name} XPI package to {xpi_destination}"
            ).format(xpi_name=xpi_name, xpi_destination=xpi_destination)
            for task in tasks:
                resolve_keyed_by(
                    task,
                    "bucket-scope",
                    item_name=task_label,
                    **{"level": config.params["level"]},
                )
                dep = task["primary-dependency"]
                task_ref = {"task-reference": "<release-signing>"}
                branch = basename(config.params["head_ref"])
                paths = list(dep.attributes["xpis"].values())
                artifact_map_paths = {
                    path: {"destinations": xpi_destinations} for path in paths
                }
                worker = {
                    "upstream-artifacts": [
                        {
                            "taskId": task_ref,
                            "taskType": "signing",
                            "paths": paths,
                            "locale": "multi",
                        },
                    ],
                    "action-scope": "push-to-nightly",
                    "bucket-scope": task["bucket-scope"],
                    "release-properties": {
                        "app-name": "xpi",
                        "app-version": xpi_version,
                        "branch": branch,
                        "build-id": config.params["moz_build_date"],
                    },
                    "artifact-map": [
                        {
                            "taskId": task_ref,
                            "paths": artifact_map_paths,
                        },
                    ],
                }
                task = {
                    "label": task_label,
                    "name": task_label,
                    "description": task_description,
                    "dependencies": {"release-signing": dep.label},
                    "worker-type": task["worker-type"],
                    "worker": worker,
                    "attributes": task["attributes"],
                    "run-on-tasks-for": task["run-on-tasks-for"],
                }
                yield task
