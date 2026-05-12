# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from typing import Literal, Optional

from mozilla_version.version import BaseVersion
from taskgraph.parameters import extend_parameters_schema
from taskgraph.util.schema import Schema


# Please keep this list sorted
class XpiParameters(Schema, rename=None, forbid_unknown_fields=False, kw_only=True):
    additional_shipit_emails: Optional[list[str]] = None
    app_version: Optional[str] = None
    next_version: Optional[str] = None
    shipping_phase: Optional[Literal["build", "promote", "ship"]] = None
    xpi_name: Optional[str] = None
    xpi_revision: Optional[str] = None


extend_parameters_schema(XpiParameters)


def decision_parameters(graph_config, parameters):
    # Change this to only build a specific xpi during testing.
    parameters["xpi_name"] = None
    if version := parameters.get("version"):
        parameters["app_version"] = version
        parameters["next_version"] = str(
            BaseVersion.parse(version).bump("minor_number")
        )
    else:
        parameters["app_version"] = None
        parameters["next_version"] = None
