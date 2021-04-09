# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.target_tasks import _target_task as target_task
from taskgraph.target_tasks import standard_filter


@target_task("ship_xpi")
def target_tasks_ship_xpi(full_task_graph, parameters, graph_config):
    """Select the set of tasks required for releasing a xpi."""

    def filter(task, parameters):
        return task.attributes.get('shipping-phase') in ('build', 'promote', 'ship')

    return [l for l, t in full_task_graph.tasks.iteritems() if filter(t, parameters)]


@target_task("promote_xpi")
def target_tasks_promote_xpi(full_task_graph, parameters, graph_config):
    """Select the set of tasks required for promoting a xpi."""

    def filter(task, parameters):
        return task.attributes.get('shipping-phase') in ('build', 'promote')

    return [l for l, t in full_task_graph.tasks.iteritems() if filter(t, parameters)]


@target_task("build_xpi")
def target_tasks_build_xpi(full_task_graph, parameters, graph_config):
    """Select the set of tasks required for promoting a xpi."""

    def filter(task, parameters):
        return task.attributes.get('shipping-phase') in ('build', )

    return [l for l, t in full_task_graph.tasks.iteritems() if filter(t, parameters)]
