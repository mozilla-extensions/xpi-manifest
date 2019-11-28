# Adding a new xpi

## Creating the repo

First, create a repository under the `mozilla-extensions` github organization. The template source repo is https://github.com/mozilla-extensions/xpi-template .

The files we need are:

    .cron.yml
    .taskcluster.yml
    CODE_OF_CONDUCT.md
    LICENSE
    taskcluster/*

though other files may be helpful as well, e.g. `README.md`, `.gitignore`, `eslintrc.js`.

### Private repos

To enable cloning private repos, uncomment the `github_clone_secret` line in the source repo's [taskcluster/ci/config.yml](https://github.com/mozilla-extensions/xpi-template/blob/f31e31ca2b2baaf9a60cf684c2bd463ce6c97473/taskcluster/ci/config.yml#L20-L21). This will move the artifact generated into `xpi/build/...` rather than `public/build/...`, and you will need Taskcluster scopes to be able to download the build. The logs will remain public for anyone viewing the task, however.

## Using taskcluster CI automation

Once Taskcluster CI automation is enabled, we'll generate a decision task and task graph on push or PR. This dynamically adds tasks using the following logic:

  - We find all `package.json` files in the repository. The directory that `package.json` lives in is the package directory.

    - We either find `yarn.lock` or `package-lock.json` in the directory. This determines whether the task will install dependencies via `yarn install --frozen-lockfile` or `npm install`.

    - The package directories must have unique names per repository. So a layout like

        ```
        ./xpis/one/package.json
        ./xpis/two/package.json
        ./three/package.json
        ./package.json
        ```

        works, while a layout like

        ```
        xpis/one/package.json
        more-xpis/one/package.json
        ```

        doesn't (duplicate `one` package directory names). A package directory at the root of the repository will be named `src`.

    - We create a build task per package directory. These will only be scheduled when `.taskcluster.yml`, a file under `taskcluster/`, or a file under the package directory have been changed since the previous build.

  - We read `package.json` and create a test task per entry in `scripts` that starts with either `test` or `lint`. (These test names must be either alphanumeric, or only include the special characters `:_-`).

    So for a `package.json` that looks like

    ```
    {
        "scripts": {
            "build": ...,
            "test": ...,
            "test:foo:": ...,
            "lint": ...
            "lint:foo": ...
        },
        ...
    }
    ```

    would have the test tasks `test`, `test:foo`, `lint`, and `lint:foo`.

    - The `test` script will be run in release build graphs. All test or lint scripts will be run on push or PR.

    - Similar to the builds, these tests will only be scheduled when `.taskcluster.yml`, a file under `taskcluster/`, or a file under the package directory have been changed since the previous test run.

## Enabling releases

To enable releases for your new repo, go to the xpi manifest repo (this one).

The source repository must be added to `taskgraph.repositories` in the xpi manifest repo's [taskcluster/ci/config.yml](../taskcluster/ci/config.yml). If this is the first xpi in your source repo, you need to add it.

Then, the xpi needs to be added to the [xpi manifest](../xpi-manifest.yml). The `repo-prefix` will refer to the repository key name under `taskgraph.repositories` in the xpi manifest repo's `taskcluster/ci/config.yml`.

The commit should run sanity checks on pull request and push; make sure the decision task goes green.

To run the release, see [Releasing a XPI](releasing-a-xpi.md).
