# Adding a new xpi

## Creating the repo

First, create a repository under the `mozilla-extensions` github organization. Next, copy in the `.taskcluster.yml` from https://github.com/mozilla-extensions/xpi-template/blob/master/.taskcluster.yml .

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

To enable signing on push, set the [`xpiSigningType` in `.taskcluster.yml`](https://github.com/mozilla-extensions/xpi-template/blob/7dbfdd814e67d8f92508052073db468438fdd5b1/.taskcluster.yml#L10-L13) to the appropriate addon type.

This currently assumes that the xpi will be named `{name}.xpi`, where `{name}` is the `name` in `package.json`.

We [may move this setting to `package.json`](https://github.com/mozilla-extensions/xpi-manifest/issues/33) in the future.

### Private repos

To enable cloning private repos, set the `privateRepo` line in the source repo's [.taskcluster.yml](https://github.com/mozilla-extensions/xpi-template/blob/7dbfdd814e67d8f92508052073db468438fdd5b1/.taskcluster.yml#L9) to `true`. This will move the artifact generated into `xpi/build/...` rather than `public/build/...` You will need to log in to taskcluster as a MoCo user to download those artifacts. The logs will remain public for anyone viewing the task, however.

Please also invite `mozilla-extensions/private-repo` to be a read-only collaborator in the repo, so ship-it can access the revision information.

## Using taskcluster CI automation

Once Taskcluster CI automation is enabled, we'll generate a decision task and task graph on push or PR. This dynamically adds tasks using the following logic:

  - We find all `package.json` files in the repository. The directory that `package.json` lives in is the package directory.

    - We either find `yarn.lock` or `package-lock.json` in the directory. This determines whether the task will install dependencies via `yarn install --frozen-lockfile` or `npm install`.

    - The package directories must have unique names per repository. So a layout like

        ```
        ./xpis/one/package.json
        ./xpis/two/package.json
        ./three/package.json
        ./not-an-addon/package.json
        ./package.json
        ```

        works, while a layout like

        ```
        xpis/one/package.json
        more-xpis/one/package.json
        ```

        doesn't (duplicate `one` package directory names). A package directory at the root of the repository will be named `src`.

    - We create a build task per package directory. These will only be scheduled when `.taskcluster.yml`, a file under `taskcluster/`, or a file under the package directory have been changed since the previous build. Note that if the directory containing the `package.json` also contains a `dontbuild` file, then no task is generated for that package directory (to support repository having a `package.json` file that is not related to an addon).

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

## Enabling releases

To enable releases for your new repo, go to the [`xpi-manifest`](https://github.com/mozilla-extensions/xpi-manifest) repository.

1. Add the source repository to [`taskgraph.repositories`](https://github.com/mozilla-extensions/xpi-manifest/blob/master/taskcluster/ci/config.yml#L8-L23) in the `xpi-manifest` repository's [taskcluster/ci/config.yml](../taskcluster/ci/config.yml). If this is the first xpi in your source repo, you need to add it. Public repos will look like this:

    ```yaml
        normandydevtools:  # This needs to not have any _ or -
            name: "Normandy Devtools"
            project-regex: normandy-devtools$
            # https url
            default-repository: https://github.com/mozilla-extensions/normandy-devtools
            # this may be `master` on older repos
            default-ref: main
            type: git
    ```

    Private repos will look like this:

    ```yaml
    loginstudy:  # This needs to not have any _ or -
        name: "Login Study"
        project-regex: login-study$
        # ssh repo url
        default-repository: git@github.com:mozilla-extensions/login-study
        # this may be `main` on newer repos
        default-ref: master
        type: git
    ```

2. Add the xpi to the [xpi manifest directory](../manifests/). Copy [manifests/template-example.yml.template](https://github.com/mozilla-extensions/xpi-manifest/blob/master/manifests/template-example.yml.template) to `manifests/{name}.yml`, where `{name}` is the name of your addon. Then edit: the `repo-prefix` will refer to the repository key name under `taskgraph.repositories` in the `xpi-manifest` repository's `taskcluster/ci/config.yml`.

The PR should run sanity checks on pull request and push; make sure the decision task and the build for your addon goes green.

Taskcluster will automatically generate a build for you signed with the
staging root, see [Testing a XPI](testing-a-xpi.md) for details on how
to QA.

After you are satisfied with your testing, see [Releasing a XPI](releasing-a-xpi.md) to learn how to produce the final production build.
