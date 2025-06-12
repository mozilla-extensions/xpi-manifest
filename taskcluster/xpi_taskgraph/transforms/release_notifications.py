# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Add notifications via taskcluster-notify for release tasks
"""


from taskgraph.transforms.base import TransformSequence
from taskgraph.util.keyed_by import evaluate_keyed_by
from xpi_taskgraph.xpi_manifest import get_manifest

transforms = TransformSequence()


@transforms.add
def add_notifications(config, tasks):
    xpi_name = config.params.get("xpi_name")
    xpi_revision = config.params.get("xpi_revision")
    shipping_phase = config.params.get("shipping_phase")
    additional_shipit_emails = config.params.get("additional_shipit_emails", [])

    if not all([xpi_name, xpi_revision, shipping_phase]):
        return
    manifest = get_manifest()

    for task in tasks:
        if "primary-dependency" in task:
            dep = task.pop("primary-dependency")
            if dep.task.get("extra", {}).get("xpi-name") != xpi_name:
                continue
            attributes = dep.attributes.copy()
            if task.get("attributes"):
                attributes.update(task["attributes"])
            task["attributes"] = attributes
            task.setdefault("dependencies", {}).update({"signing": dep.label})
        if task.get("attributes", {}).get("shipping-phase") != shipping_phase:
            continue
        task["label"] = f"{config.kind}-{shipping_phase}"
        xpi_config = manifest[xpi_name]
        xpi_type = xpi_config["addon-type"]

        emails = evaluate_keyed_by(
            config.graph_config["release-promotion"]["notifications"][xpi_type],
            "email",
            dict(phase=shipping_phase, level=config.params["level"]),
        )
        if not emails:
            continue
        emails = set(
            emails + additional_shipit_emails + xpi_config.get("additional-emails", [])
        )
        notifications = evaluate_keyed_by(
            task.pop("notifications"), "notification config", dict(phase=shipping_phase)
        )
        format_kwargs = dict(config=config.__dict__)
        subject = notifications["subject"].format(**format_kwargs)
        message = notifications["message"].format(**format_kwargs)

        # We only send mail on success to avoid messages like 'blah is in the
        # candidates dir' when cancelling graphs, dummy task failure, etc
        task.setdefault("routes", []).extend(
            sorted(f"notify.email.{email}.on-completed" for email in emails)
        )

        task.setdefault("extra", {}).update({"notify": {"email": {"subject": subject}}})
        if message:
            task["extra"]["notify"]["email"]["content"] = message

        yield task
