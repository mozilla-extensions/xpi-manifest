# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Apply some defaults and minor modifications to the jobs defined in the build
kind.
"""

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import resolve_keyed_by
from taskgraph.util.keyed_by import evaluate_keyed_by


transforms = TransformSequence()

KNOWN_FORMATS = ("privileged_webextension", "system_addon")


@transforms.add
def define_signing_flags(config, tasks):
    for task in tasks:
        dep = task["primary-dependency"]
        # Current kind will be prepended later in the transform chain.
        task["name"] = _get_dependent_job_name_without_its_kind(dep)
        attributes = dep.attributes.copy()
        if task.get("attributes"):
            attributes.update(task["attributes"])
        task["attributes"] = attributes
        task["attributes"]["signed"] = True
        if "run_on_tasks_for" in task["attributes"]:
            task.setdefault("run-on-tasks-for", task["attributes"]["run_on_tasks_for"])

        for key in ("worker-type", "worker.signing-type"):
            resolve_keyed_by(
                task, key, item_name=task["name"], level=config.params["level"]
            )
        yield task


@transforms.add
def build_signing_task(config, tasks):
    for task in tasks:
        dep = task["primary-dependency"]
        task["dependencies"] = {"build": dep.label}
        if not dep.task["payload"]["env"]["ARTIFACT_PREFIX"].startswith("public"):
            scopes = task.setdefault("scopes", [])
            scopes.append(
                "queue:get-artifact:{}/*".format(
                    dep.task["payload"]["env"]["ARTIFACT_PREFIX"].rstrip("/")
                )
            )

        paths = list(dep.attributes["xpis"].values())
        format = evaluate_keyed_by(
            config.graph_config["scriptworker"]["signing-format"],
            "signing-format",
            {
                "xpi-type": task["attributes"]["addon-type"],
                "kind": config.kind,
                "level": config.params["level"],
            },
        )
        assert format in KNOWN_FORMATS
        task["worker"]["upstream-artifacts"] = [
            {
                "taskId": {"task-reference": "<build>"},
                "taskType": "build",
                "paths": paths,
                "formats": [format],
            }
        ]
        task.setdefault("extra", {})["xpi-name"] = dep.task["extra"]["xpi-name"]
        task["extra"]["artifact_prefix"] = dep.task["payload"]["env"]["ARTIFACT_PREFIX"]
        del task["primary-dependency"]
        yield task


def _get_dependent_job_name_without_its_kind(dependent_job):
    return dependent_job.label[len(dependent_job.kind) + 1 :]
