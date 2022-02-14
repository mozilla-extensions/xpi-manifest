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
        Required("run-on-tasks-for"): [str],
        Required("balrog"): dict,
        Required("only-for-addon-types"): [str],
    },
)
transforms = TransformSequence()
transforms.add_validate(schema)


@transforms.add
def add_balrog_worker_config(config, tasks):
    if (
        config.params.get("version")
        and config.params.get("xpi_name")
        and config.params.get("head_ref")
        and config.params.get("build_number")
        and config.params.get("level")
    ):
        manifest = get_manifest()
        xpi_name = config.params["xpi_name"]
        xpi_manifest = manifest[xpi_name]
        xpi_addon_type = xpi_manifest["addon-type"]
        xpi_version = config.params["version"]
        build_number = config.params["build_number"]
        release_name = (
            "{xpi_name}-{xpi_version}-build{build_number}"
        ).format(
            xpi_name=xpi_name,
            xpi_version=xpi_version,
            build_number=build_number,
        )
        task_label = f"balrog-{xpi_name}"
        task_description = (
            "Create a Balrog release for the signed "
            "XPI artifacts uploaded to "
            "pub/system-addons/{xpi_name}/{release_name}/"
        ).format(xpi_name=xpi_name, release_name=release_name)
        for task in tasks:
            if xpi_addon_type not in task["only-for-addon-types"]:
                continue
            dep = task["primary-dependency"]
            task_ref = {"task-reference": "<beetmover>"}
            paths = [
                "public/manifest.json",
                "public/target.checksums",
            ]
            worker = {
                "action": "submit-system-addons",
                "server": task["balrog"]["server"],
                "channel": task["balrog"]["channel"],
                "upstream-artifacts": [
                    {
                        "taskId": task_ref,
                        "taskType": "beetmover",
                        "paths": paths,
                    },
                ],
            }
            resolve_keyed_by(
                worker,
                "server",
                item_name=task_label,
                **{"level": config.params["level"]},
            )
            task = {
                "label": task_label,
                "name": task_label,
                "description": task_description,
                "dependencies": {"beetmover": dep.label},
                "worker-type": task["worker-type"],
                "worker": worker,
                "attributes": task["attributes"],
                "run-on-tasks-for": task["run-on-tasks-for"],
            }
            yield task
