# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

from taskgraph.actions.registry import register_callback_action

from taskgraph.util.taskcluster import get_artifact
from taskgraph.taskgraph import TaskGraph
from taskgraph.decision import taskgraph_decision
from taskgraph.parameters import Parameters
from taskgraph.util.taskgraph import find_decision_task, find_existing_tasks_from_previous_kinds
from xpi_taskgraph.xpi_manifest import get_manifest

RELEASE_PROMOTION_PROJECTS = (
    "https://github.com/mozilla-extensions/xpi-manifest",
    "https://github.com/escapewindow/xpi-manifest",
)

XPI_MANIFEST = get_manifest()


def is_release_promotion_available(parameters):
    return parameters['head_repository'] in RELEASE_PROMOTION_PROJECTS


@register_callback_action(
    name='release-promotion',
    title='Promote a XPI',
    symbol='${input.release_promotion_flavor}_${input.xpi_name}',
    description="Promote a XPI.",
    generic=False,
    order=500,
    context=[],
    available=is_release_promotion_available,
    schema=lambda graph_config: {
        'type': 'object',
        'properties': {
            'build_number': {
                'type': 'integer',
                'default': 1,
                'minimum': 1,
                'title': 'The release build number',
                'description': ('The release build number. Starts at 1 per '
                                'release version, and increments on rebuild.'),
            },
            'do_not_optimize': {
                'type': 'array',
                'description': ('Optional: a list of labels to avoid optimizing out '
                                'of the graph (to force a rerun of, say, '
                                'funsize docker-image tasks).'),
                'items': {
                    'type': 'string',
                },
            },
            'xpi_name': {
                'type': 'string',
                'title': 'The XPI to promote',
                'default': 'FILLMEIN',
                'description': ('The XPI to promote.'),
                'enum': sorted(XPI_MANIFEST.keys()),
            },
            'revision': {
                'type': 'string',
                'title': 'Optional: revision to promote',
                'description': ('Optional: the revision to promote.'),
            },
            'release_promotion_flavor': {
                'type': 'string',
                'description': 'The flavor of release promotion to perform.',
                'default': 'build',
                'enum': sorted(graph_config['release-promotion']['flavors'].keys()),
            },
            'rebuild_kinds': {
                'type': 'array',
                'description': ('Optional: an array of kinds to ignore from the previous '
                                'graph(s).'),
                'items': {
                    'type': 'string',
                },
            },
            'previous_graph_ids': {
                'type': 'array',
                'description': ('Optional: an array of taskIds of decision or action '
                                'tasks from the previous graph(s) to use to populate '
                                'our `previous_graph_kinds`.'),
                'items': {
                    'type': 'string',
                },
            },
            'version': {
                'type': 'string',
                'description': ('The expected version to promote.'),
                'default': '',
            },
        },
        "required": ['release_promotion_flavor', 'xpi_name', 'build_number'],
    }
)
def release_promotion_action(parameters, graph_config, input, task_group_id, task_id):
    release_promotion_flavor = input['release_promotion_flavor']
    promotion_config = graph_config['release-promotion']['flavors'][release_promotion_flavor]

    target_tasks_method = promotion_config['target-tasks-method'].format(
        project=parameters['project']
    )
    rebuild_kinds = input.get('rebuild_kinds') or promotion_config.get('rebuild-kinds', [])
    do_not_optimize = input.get('do_not_optimize') or promotion_config.get('do-not-optimize', [])

    # make parameters read-write
    parameters = dict(parameters)
    # Build previous_graph_ids from ``previous_graph_ids`` or ``revision``.
    previous_graph_ids = input.get('previous_graph_ids')
    if not previous_graph_ids:
        previous_graph_ids = [find_decision_task(parameters, graph_config)]

    # Download parameters from the first decision task
    parameters = get_artifact(previous_graph_ids[0], "public/parameters.yml")
    # Download and combine full task graphs from each of the previous_graph_ids.
    # Sometimes previous relpro action tasks will add tasks, like partials,
    # that didn't exist in the first full_task_graph, so combining them is
    # important. The rightmost graph should take precedence in the case of
    # conflicts.
    combined_full_task_graph = {}
    for graph_id in previous_graph_ids:
        full_task_graph = get_artifact(graph_id, "public/full-task-graph.json")
        combined_full_task_graph.update(full_task_graph)
    _, combined_full_task_graph = TaskGraph.from_json(combined_full_task_graph)
    parameters['existing_tasks'] = find_existing_tasks_from_previous_kinds(
        combined_full_task_graph, previous_graph_ids, rebuild_kinds
    )
    parameters['do_not_optimize'] = do_not_optimize
    parameters['target_tasks_method'] = target_tasks_method
    parameters['build_number'] = int(input['build_number'])
    # When doing staging releases on try, we still want to re-use tasks from
    # previous graphs.
    parameters['optimize_target_tasks'] = True
    parameters['xpi_name'] = input['xpi_name']
    # TODO
    #  - require this is a specific revision
    #  - possibly also check that this is on a reviewed PR or merged into
    #    a trusted branch. this will require an oauth token
    parameters['xpi_revision'] = input.get('revision', 'master')
    parameters['shipping_phase'] = input['release_promotion_flavor']

    # We blow away `tasks_for` when we load the on-push decision task's
    # parameters.yml. Let's set this back to `action`.
    parameters['tasks_for'] = "action"

    if input.get('version'):
        parameters['version'] = input['version']

    # make parameters read-only
    parameters = Parameters(**parameters)

    taskgraph_decision({'root': graph_config.root_dir}, parameters=parameters)
