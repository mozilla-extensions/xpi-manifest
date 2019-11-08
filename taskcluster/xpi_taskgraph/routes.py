# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

import time

from taskgraph.transforms.task import index_builder

SIGNING_ROUTE_TEMPLATES = [
    "index.{trust-domain}.{project}.v3.{name}.{variant}.{build_date}.revision.{head_rev}",
    "index.{trust-domain}.{project}.v3.{name}.{variant}.{build_date}.latest",
    "index.{trust-domain}.{project}.v3.{name}.{variant}.latest",
]


def add_signing_indexes(config, task, variant):
    routes = task.setdefault("routes", [])

    if config.params["level"] != "3":
        return task

    subs = config.params.copy()
    subs["build_date"] = time.strftime(
        "%Y.%m.%d", time.gmtime(config.params["build_date"])
    )
    subs["trust-domain"] = config.graph_config["trust-domain"]
    subs["variant"] = variant
    xpi_name =  task.get("payload", {}).get("env", {}).get("XPI_NAME")
    if xpi_name:
        subs["name"] = xpi_name
        for tpl in SIGNING_ROUTE_TEMPLATES:
            routes.append(tpl.format(**subs))
    return task


@index_builder("release-signing")
def add_release_signing_indexes(config, task):
    return add_signing_indexes(config, task, "release-signing")
