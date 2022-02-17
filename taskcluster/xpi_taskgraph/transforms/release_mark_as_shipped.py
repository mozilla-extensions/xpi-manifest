# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import resolve_keyed_by

transforms = TransformSequence()


@transforms.add
def make_task_description(config, jobs):
    for job in jobs:
        if not (
            config.params.get("version")
            and config.params.get("xpi_name")
            and config.params.get("build_number")
        ):
            continue
        resolve_keyed_by(
            job, "scopes", item_name=job["name"], **{"level": config.params["level"]}
        )
        primary_dep = job.pop("primary-dependency")
        deps = job.pop("dependent-tasks")
        job["dependencies"] = {
            dep_key: dep.label
            for dep_key, dep in deps.items()
        }
        copy_of_attributes = primary_dep.attributes.copy()
        job.setdefault("attributes", {}).update(copy_of_attributes)
        job.setdefault("run-on-tasks-for", copy_of_attributes['run_on_tasks_for'])
        job["worker"][
            "release-name"
        ] = "{xpi_name}-{version}-build{build_number}".format(
            xpi_name=config.params["xpi_name"],
            version=config.params["version"],
            build_number=config.params["build_number"],
        )

        yield job
