# Adding a new xpi

First, create a repository under the `mozilla-extensions` github organization.

## Creating a public repo

The template source repo is https://github.com/mozilla-extensions/xpi-template .

Copy in the `.taskcluster.yml` from https://github.com/mozilla-extensions/xpi-template/blob/master/.taskcluster.yml .

Other files we need are

    CODE_OF_CONDUCT.md
    LICENSE

though other files may be helpful as well, e.g. `README.md`, `.gitignore`, `eslintrc.js`.

### Existing repos

If your repo is already existing, let's move it to the `mozilla-extensions` Github organization (`Settings -> Options -> Transfer Ownership`).
Then copy over the above files into your repo. You can either do this by cloning the `xpi-template` repo and copying the files over and `git add`ing them, or by adding a new git remote and merging the two heads:

```
# in your repo clone
git remote add template https://github.com/mozilla-extensions/xpi-template
git fetch template
git merge --allow-unrelated-histories template/master
# fix conflicts, commit result
```

### Branch protection

We will use the `master` branch as the main branch for releasing XPIs. It's important to set branch protection for the `master` branch, and get code review for the source. Foxsec will be auditing the repositories in the `mozilla-extensions` organization for compliance.

The github repository rules are [here](https://wiki.mozilla.org/GitHub/Repository_Security).

When creating the repository, email [secops+github@mozilla.com](mailto:secops+github@mozilla.com) about adding the new repository to its checks.

### Enable signing on push

To enable signing on push, find the `xpiSigningType` in `.taskcluster.yml`, and set it to the appropriate addon type.

We [may move this setting to `package.json`](https://github.com/mozilla-extensions/xpi-manifest/issues/33) in the future.

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

  - We read `package.json` and create a test task per entry in `scripts` that starts with `test`. It will also create a test task for the `lint` target, if it exists. (These test names must be either alphanumeric, or only include the special characters `:_-`).

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

    would have the test tasks `test`, `test:foo`, and `lint`.

    - The `test` script will be run in release build graphs. All test or lint scripts will be run on push or PR.

    - Similar to the builds, these tests will only be scheduled when `.taskcluster.yml`, a file under `taskcluster/`, or a file under the package directory have been changed since the previous test run.

## Private repos

Please invite `moz-releng-automation` to be a read-only collaborator in the repo, so ship-it can access the revision information.

**NOTE**: CI doesn't work on private repos! Builds will happen in release builds.

Branch protection won't work either. We'll essentially use the limited access to the repository as a security measure.

## Enabling releases

To enable releases for your new repo, go to the `xpi-manifest` repository (this one).

The source repository must be added to `taskgraph.repositories` in the `xpi-manifest` repository's [taskcluster/ci/config.yml](../taskcluster/ci/config.yml). If this is the first xpi in your source repo, you need to add it.

Then, the xpi needs to be added to the [xpi manifest](../xpi-manifest.yml). The `repo-prefix` will refer to the repository key name under `taskgraph.repositories` in the `xpi-manifest` repository's `taskcluster/ci/config.yml`.

The commit should run sanity checks on pull request and push; make sure the decision task goes green.

To run the release, see [Releasing a XPI](releasing-a-xpi.md).
