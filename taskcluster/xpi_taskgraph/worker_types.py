# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import datetime
from os.path import basename

from taskgraph.transforms.task import payload_builder
from taskgraph.util.schema import taskref_or_string
from voluptuous import Any, Optional, Required


@payload_builder(
    "scriptworker-signing",
    schema={
        # the maximum time to run, in seconds
        Required("max-run-time"): int,
        Required("signing-type"): str,
        # list of artifact URLs for the artifacts that should be signed
        Required("upstream-artifacts"): [
            {
                # taskId of the task with the artifact
                Required("taskId"): taskref_or_string,
                # type of signing task (for CoT)
                Required("taskType"): str,
                # Paths to the artifacts to sign
                Required("paths"): [str],
                # Signing formats to use on each of the paths
                Required("formats"): [str],
            }
        ],
    },
)
def build_scriptworker_signing_payload(config, task, task_def):
    worker = task["worker"]

    task_def["tags"]["worker-implementation"] = "scriptworker"

    task_def["payload"] = {
        "maxRunTime": worker["max-run-time"],
        "upstreamArtifacts": worker["upstream-artifacts"],
    }

    formats = set()
    for artifacts in worker["upstream-artifacts"]:
        formats.update(artifacts["formats"])

    scope_prefix = config.graph_config["scriptworker"]["scope-prefix"]
    task_def["scopes"].append(
        "{}:signing:cert:{}".format(scope_prefix, worker["signing-type"])
    )


@payload_builder("shipit-shipped", schema={Required("release-name"): str})
def build_push_apk_payload(config, task, task_def):
    worker = task["worker"]

    task_def["payload"] = {"release_name": worker["release-name"]}


# NOTE: copied scriptworker-github from fenix w/few modifications
@payload_builder(
    "scriptworker-github",
    schema={
        Required("upstream-artifacts"): [
            {
                Required("taskId"): taskref_or_string,
                Required("taskType"): str,
                Required("paths"): [str],
            }
        ],
        Required("artifact-map"): [object],
        Required("action"): str,
        Required("git-tag"): str,
        Required("git-revision"): str,
        Required("github-project"): str,
        Required("is-prerelease"): bool,
        Required("release-name"): str,
    },
)
def build_github_release_payload(config, task, task_def):
    worker = task["worker"]

    task_def["tags"]["worker-implementation"] = "scriptworker"

    owner, repo_name = worker["github-project"].split("/")
    task_def["payload"] = {
        "artifactMap": worker["artifact-map"],
        "gitTag": worker["git-tag"],
        "gitRevision": worker["git-revision"],
        "releaseName": worker["release-name"],
        "isPrerelease": worker["is-prerelease"],
        "githubOwner": owner,
        "githubRepoName": repo_name,
        "upstreamArtifacts": worker["upstream-artifacts"],
    }

    scope_prefix = config.graph_config["scriptworker"]["scope-prefix"]
    task_def["scopes"].extend(
        [
            "{}:github:project:{}".format(scope_prefix, worker["github-project"]),
            "{}:github:action:{}".format(scope_prefix, worker["action"]),
        ]
    )


@payload_builder(
    "scriptworker-beetmover",
    schema={
        Required("action-scope"): str,
        Required("bucket-scope"): str,
        Required("artifact-map"): [
            {
                Required("paths"): {
                    Any(str): {
                        Required("destinations"): [str],
                    },
                },
                Required("taskId"): taskref_or_string,
            }
        ],
        Required("release-properties"): {
            Required("app-name"): str,
            Required("app-version"): str,
            Required("branch"): str,
            Required("build-id"): str,
            Optional("hash-type"): str,
            Optional("platform"): str,
        },
        Required("upstream-artifacts"): [
            {
                Required("locale"): str,
                Required("taskId"): taskref_or_string,
                Required("taskType"): str,
                Required("paths"): [str],
            }
        ],
    },
)
def build_scriptworker_beetmover_payload(config, task, task_def):
    worker = task["worker"]
    task_def["tags"]["worker-implementation"] = "scriptworker"
    artifact_map = worker["artifact-map"]
    for map_ in artifact_map:
        map_["locale"] = "multi"
        for path_config in map_["paths"].values():
            for destination in path_config["destinations"]:
                path_config["checksums_path"] = basename(destination)
    if worker["release-properties"].get("hash-type"):
        hash_type = worker["release-properties"]["hash-type"]
    else:
        hash_type = "sha512"
    if worker["release-properties"].get("platform"):
        platform = worker["release-properties"]["platform"]
    else:
        platform = "xpi"
    release_properties = {
        "appName": worker["release-properties"]["app-name"],
        "appVersion": worker["release-properties"]["app-version"],
        "branch": worker["release-properties"]["branch"],
        "buildid": worker["release-properties"]["build-id"],
        "hashType": hash_type,
        "platform": platform,
    }
    prefix = "project:xpi:beetmover:"
    task_def["scopes"] = [
        "{prefix}bucket:{bucket_scope}".format(
            prefix=prefix, bucket_scope=worker["bucket-scope"]
        ),
        "{prefix}action:{action_scope}".format(
            prefix=prefix, action_scope=worker["action-scope"]
        ),
    ]
    task_def["payload"] = {
        "maxRunTime": 600,
        "artifactMap": artifact_map,
        "releaseProperties": release_properties,
        "upstreamArtifacts": worker["upstream-artifacts"],
        "upload_date": int(datetime.now().timestamp()),
    }


@payload_builder(
    "scriptworker-balrog",
    schema={
        Required("action"): str,
        Required("channel"): str,
        Required("server"): str,
        Required("upstream-artifacts"): [
            {
                Required("taskId"): taskref_or_string,
                Required("taskType"): str,
                Required("paths"): [str],
            }
        ], 
    }
)
def build_scriptworker_balrog_payload(config, task, task_def):
    worker = task["worker"]
    task_def["tags"]["worker-implementation"] = "scriptworker"
    task_def["payload"] = {
        "maxRunTime": 600,
        "upstreamArtifacts": worker["upstream-artifacts"],
    }
    prefix = "project:xpi:balrog:"
    task_def["scopes"] = [
        "{prefix}action:{action}".format(
            prefix=prefix, action=worker["action"]
        ),
        "{prefix}server:{server}".format(
            prefix=prefix, server=worker["server"]
        ),
    ]
