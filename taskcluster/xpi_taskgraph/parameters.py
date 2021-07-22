# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.parameters import extend_parameters_schema
from voluptuous import Any, Optional, Required


# Please keep this list sorted
xpi_schema = {
    Optional("additional_shipit_emails"): Any([str], None),
    Optional("shipping_phase"): Any("build", "promote", "ship", None),
    Optional("xpi_name"): Any(str, None),
    Optional("xpi_revision"): Any(str, None),
}

extend_parameters_schema(xpi_schema)
