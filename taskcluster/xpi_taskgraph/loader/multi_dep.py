# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import copy

from taskgraph.task import Task
from taskgraph.util.schema import Schema
from voluptuous import Required

schema = Schema(
    {
        Required("primary-dependency"): Task,
        Required("dependent-tasks"): {str: Task},
    },
)

GROUP_BY_MAP = {}


def group_by(name):
    def wrapper(func):
        GROUP_BY_MAP[name] = func
        return func

    return wrapper


@group_by("addon-type")
def group_by_addon_type(config, tasks):
    groups = {}
    kind_dependencies = config.get("kind-dependencies")
    only_addon_types = config.get("only-for-addon-types")
    for task in tasks:
        if task.kind not in kind_dependencies:
            continue
        if only_addon_types:
            addon_type = task.attributes.get("addon-type")
            if not addon_type in only_addon_types:
                continue
        addon_type = task.attributes.get("addon-type")
        groups.setdefault(addon_type, []).append(task)
    return groups


@group_by("xpi-name")
def group_by_xpi_name(config, tasks):
    groups = {}
    kind_dependencies = config.get("kind-dependencies")
    for task in tasks:
        if task.kind not in kind_dependencies:
            continue
        xpi_name = task.task.get("extra").get("xpi-name")
        groups.setdefault(xpi_name, []).append(task)
    return groups


def group_tasks(config, tasks):
    group_by_fn = GROUP_BY_MAP[config["group-by"]]
    groups = group_by_fn(config, tasks)
    for combinations in groups.values():
        dependencies = [copy.deepcopy(t) for t in combinations]
        yield dependencies


def loader(kind, path, config, params, loaded_tasks):
    task_template = config.get("task-template")
    for dep_tasks in group_tasks(config, loaded_tasks):
        kinds = [dep.kind for dep in dep_tasks]
        kinds_occurrences = {kind: kinds.count(kind) for kind in kinds}
        dep_tasks_per_unique_key = {
            dep.kind if kinds_occurrences[dep.kind] == 1 else dep.label: dep
            for dep in dep_tasks
        }

        primary_dep = get_primary_dep(config, dep_tasks_per_unique_key)

        task = {"primary-dependency": primary_dep}
        if task_template:
            task.update(copy.deepcopy(task_template))
        task["dependencies"] = {
            dep_key: dep.label for dep_key, dep in dep_tasks_per_unique_key.items()
        }
        copy_of_attributes = primary_dep.attributes.copy()
        task["attributes"] = {
            **copy_of_attributes,
            **task["attributes"],
            **{"kind": kind},
        }
        task.setdefault("run-on-tasks-for", copy_of_attributes["run_on_tasks_for"])

        yield task


def get_primary_dep(config, dep_tasks):
    primary_dependencies = config.get("primary-dependency")
    if isinstance(primary_dependencies, str):
        primary_dependencies = [primary_dependencies]
    if not primary_dependencies:
        assert len(dep_tasks) == 1, "Must define a primary-dependency!"
        return list(dep_tasks.values())[0]
    primary_dep = None
    for primary_kind in primary_dependencies:
        for dep_kind in dep_tasks:
            if dep_kind == primary_kind:
                assert (
                    primary_dep is None
                ), "Too many primary dependent tasks in dep_tasks: {}!".format(
                    [dep_tasks[key].label for key in dep_tasks],
                )
                primary_dep = dep_tasks[dep_kind]
    if primary_dep is None:
        raise Exception(
            "Can't find dependency of {}: {}".format(
                config["primary-dependency"],
                config,
            ),
        )
    return primary_dep
