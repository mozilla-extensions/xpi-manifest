# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Add notifications via taskcluster-notify for release tasks
"""

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.keyed_by import evaluate_keyed_by
from taskgraph.util.schema import resolve_keyed_by

from xpi_taskgraph.xpi_manifest import get_xpi_config


transforms = TransformSequence()


@transforms.add
def add_notifications(config, jobs):
    xpi_name = config.params.get("xpi_name")
    xpi_revision = config.params.get("xpi_revision")
    shipping_phase = config.params.get("shipping_phase")
    if not all([xpi_name, xpi_revision, shipping_phase]):
        return

    for job in jobs:
        if "primary-dependency" in job:
            dep = job.pop("primary-dependency")
            if dep.task.get("extra", {}).get("xpi-name") != xpi_name:
                continue
            attributes = dep.attributes.copy()
            if job.get("attributes"):
                attributes.update(job["attributes"])
            job["attributes"] = attributes
            job.setdefault("dependencies", {}).update({"signing": dep.label})
        if job.get("attributes", {}).get("shipping-phase") != shipping_phase:
            continue
        job['label'] = '{}-{}'.format(config.kind, shipping_phase)
        xpi_config = get_xpi_config(xpi_name)
        xpi_type = xpi_config['addon-type']

        emails = evaluate_keyed_by(
            config.graph_config['release-promotion']['notifications'][xpi_type],
            'email', dict(phase=shipping_phase, )
        ) + xpi_config.get("additional-emails", [])
        notifications = evaluate_keyed_by(
            job.pop('notifications'),
            'notification config', dict(phase=shipping_phase, )
        )
        format_kwargs = dict(
            config=config.__dict__,
        )
        subject = notifications['subject'].format(**format_kwargs)
        message = notifications['message'].format(**format_kwargs)

        # We only send mail on success to avoid messages like 'blah is in the
        # candidates dir' when cancelling graphs, dummy job failure, etc
        job.setdefault('routes', []).extend(
            ['notify.email.{}.on-completed'.format(email) for email in emails]
        )

        job.setdefault('extra', {}).update(
            {
               'notify': {
                   'email': {
                        'subject': subject,
                    }
                }
            }
        )
        if message:
            job['extra']['notify']['email']['content'] = message

        yield job
