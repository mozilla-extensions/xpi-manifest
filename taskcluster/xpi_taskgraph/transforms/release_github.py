# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Apply some defaults and minor modifications to the jobs defined in the github_release
kind.

TODO: copied directly from fenix transforms (if we keep this it is easier to make generic)
"""

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import resolve_keyed_by


transforms = TransformSequence()


@transforms.add
def resolve_keys(config, jobs):
    for job in jobs:
        for key in ("worker.github-project", "worker.release-name"):
            resolve_keyed_by(
                job,
                key,
                item_name=job["name"],
                **{
                    'level': config.params["level"],
                }
            )
        yield job


@transforms.add
def build_worker_definition(config, jobs):
    for job in jobs:
        # TODO: this section taken from release_mark_as_shipped
        if not (
            config.params.get('version')
            and config.params.get('xpi_name')
            and config.params.get('build_number')
        ):
            continue
        resolve_keyed_by(
            job, 'scopes', item_name=job['name'],
            **{'level': config.params["level"]}
        )

        job['worker']['release-name'] = '{xpi_name}-{version}-build{build_number}'.format(
            xpi_name=config.params['xpi_name'],
            version=config.params['version'],
            build_number=config.params['build_number']
        )

        worker_definition = {
            "artifact-map": _build_artifact_map(job),
            "git-tag": config.params["head_tag"].decode("utf-8"),
            "git-revision": config.params["head_rev"].decode("utf-8"),
            "github-project": config.params["project"].decode("utf-8"),
        }
        # TODO: figure out how to specify a tag
        if worker_definition["git-tag"] == "":
            worker_definition["git-tag"] = "TODO"

        dep = job["primary-dependency"]
        if not dep.task["payload"]["env"]["ARTIFACT_PREFIX"].startswith("public"):
            scopes = job.setdefault('scopes', [])
            scopes.append(
                "queue:get-artifact:{}/*".format(dep.task["payload"]["env"]["ARTIFACT_PREFIX"].rstrip('/'))
            )

        job["worker"].update(worker_definition)
        del job["primary-dependency"]
        yield job

def _build_artifact_map(job):
    artifact_map = []
    dep = job["primary-dependency"]

    artifacts = {"paths": dep.attributes["xpis"].values(), "taskId": dep.task["extra"]["parent"]}
    artifact_map.append(artifacts)
    return artifact_map