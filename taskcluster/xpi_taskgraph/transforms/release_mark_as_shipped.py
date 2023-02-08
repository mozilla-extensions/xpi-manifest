# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import resolve_keyed_by

transforms = TransformSequence()


@transforms.add
def make_task_description(config, tasks):
    for task in tasks:
        if not (
            config.params.get("version")
            and config.params.get("xpi_name")
            and config.params.get("build_number")
        ):
            continue
        if "primary-dependency" in task:
            task.pop("primary-dependency")
        resolve_keyed_by(
            task, "scopes", item_name=task["name"], **{"level": config.params["level"]}
        )
        task["worker"][
            "release-name"
        ] = "{xpi_name}-{version}-build{build_number}".format(
            xpi_name=config.params["xpi_name"],
            version=config.params["version"],
            build_number=config.params["build_number"],
        )
        yield task
