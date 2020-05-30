# Releasing a xpi

## Release phases

### Build

In the build phase, we generate a release build, a dep-signing (development signing) task, and a test task. Additionally, there's a notify task that runs at the start of the graph, and a second notify task that runs after the signing task runs.

We trigger the build graph to generate a release build for QA to test.

### Promote

In the promote phase, we release-sign the build generated in the build graph. Because we're release-signing the same binary generated in the build graph, we're shipping the bits that we've tested (as opposed to rebuilding and release-signing the new build). There are also `release-notify-started` and `release-notify-completed` tasks that notify via email.

The promote phase requires multiple signoffs to schedule in shipit. See [Signoffs](#Signoffs).

In the future, we could add additional tasks here, or additional phases, as needed. These could, for example, push to S3, push to XPIHub, push to bouncer, push to AMO, push to balrog, version bump the xpi.

## Configuring email notifications

These are configured per addon-type (privileged webextension vs system addon) and per phase (build or promote), in the `xpi-manifest` repository's [`taskcluster/ci/config.yml`](../taskcluster/ci/config.yml), under `release-promotion.notifications`.

LDAP-controlled mail lists are preferred over individual emails. You may want to add a +comment (e.g. `email+system-addon-release-builds@m.c` for easier filtering.

## Kicking off the release

We'll use ship-it for this. This isn't quite ready yet. You'll need LDAP perms and VPN to reach it.

### Starting the build phase

  - [Connect to VPN](https://mana.mozilla.org/wiki/display/IT/Mozilla+VPN)
  - Connect to ship-it
  - Look at the `XPI Releases` to see if the release is already configured.
  - If we want to configure a new release, choose `New XPI Release`.
  - Choose a `xpi-manifest` repository revision. You probably want the latest. We may make this default to the latest revision on `xpi-manifest/master` at some point.
  - Choose a xpi to build.
  - Choose a source repo revision. You probably want the latest. This revision currently needs to be a recent revision on the release branch (generally `master`).
  - Click `Start tracking it`.
  - Click `Doo Eet`. This will create the release, but not schedule it.
  - Click the `Build` on the progress bar for the appropriate row (this will be labeled with the XPI name, version, build number).
  - Once the build graph is scheduled, the `Build` will be a link to the build graph.
  - Once the build graph is created, the first half of the progress bar will be green, monitor the build graph for all the jobs to go green, or check email if you're getting notifications.
  - QA can then download the build from the build task (unsigned) or the dep-signing task (signed with the developer key).

At this point QA, developers, or project managers may request changes.

If we need a new release build:

  - Cancel the previous release
  - Repeat the above steps, but for a build `n+1`.

### Signoffs

  - Click on the `Promote` portion of the progress bar, and sign off as the appropriate user type. See below.
  - When we have the quorum of signoffs, we'll schedule the promote graph, and we'll get a release-signed xpi.
  - Again, the promote button becomes a link to the build graph, wait until they are all finished. The signed xpi can be found as an artifact on the `release-signing-...` task.

| Group name | Who | Type of xpi | Notes |
| ---------- | --- | ----------- | ----- |
Privileged webextension admin | product-delivery team (+releng as backups) | privileged | Two of these are required to sign off on `privileged` xpis.
System addon admin | `:rdalal` and `:mythmon` (+releng as backups) | system | Two of these are required to sign off on `system` xpis.
MozillaOnline privileged webextension team | mozilla-online team (+releng as backups) | mozillaonline-privileged | One of each (team and admin) need to sign off on `mozillaonline-privileged` xpis.
MozillaOnline privileged webextension admin | `:theone` and `:mkaply` (+releng as backups) | mozillaonline-privileged | One of each (team and admin) need to sign off on `mozillaonline-privileged` xpis.

Releng should only step in to expedite when requested, and only to unblock urgent requests. If releng signs off, that release should be audited by the appropriate team(s) later.
