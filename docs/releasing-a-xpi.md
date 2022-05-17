# Releasing a xpi

## Release phases

### Build

In the build phase, we generate a release build, a dep-signing (development signing) task, and a test task. Additionally, there are  `release-notify-started` and `release-notify-completed` tasks that notify via email.

We trigger the build graph to generate a release build for QA to test.

### Promote

In the promote phase, we release-sign the build generated in the build graph. Because we're release-signing the same binary generated in the build graph, we're shipping the bits that we've tested (as opposed to rebuilding and release-signing the new build). There are also `release-notify-started` and `release-notify-completed` tasks that notify via email.

The promote phase requires multiple signoffs to schedule in shipit. See [Signoffs](#Signoffs).

In the future, we could add additional tasks here, or additional phases, as needed. These could, for example, push to S3, push to XPIHub, push to bouncer, push to AMO, push to balrog, version bump the xpi.

## Ship

In the ship phase, we mark the release as shipped.  If `enable-github-release` is True in the manifest we will upload a new release to the projects github page with the signed .xpi file as part of the release.

Similar to the promote phase, the ship phase requires a signoff to schedule in shipit. See [Signoffs](#Signoffs).

Just like the Build and Promote phases, there are also `release-notify-started` and `release-notify-completed` tasks that notify via email.

## Configuring email notifications

These are configured per addon-type (privileged webextension vs system addon) and per phase (build or promote), in the `xpi-manifest` repository's [`taskcluster/ci/config.yml`](../taskcluster/ci/config.yml), under `release-promotion.notifications`.

LDAP-controlled mail lists are preferred over individual emails. You may want to add a +comment (e.g. `email+system-addon-release-builds@m.c` for easier filtering.

## Kicking off the release

We'll use ship-it for this. This isn't quite ready yet. You'll need LDAP perms and VPN to reach it.

### Starting the build phase

  - [Connect to VPN](https://mana.mozilla.org/wiki/display/IT/Mozilla+Corporate+VPN)
  - [Connect to ship-it](https://shipit.mozilla-releng.net/)
    - If ship-it website says that you are not using the VPN, try a different VPN endpoint.
      - Berlin's endpoint has not been added yet, [Bug 1651234](https://bugzilla.mozilla.org/show_bug.cgi?id=1651234)
    - If you are unable to open the ship-it website, check if you have the "vpn_cloudops_shipit" permission in your [LDAP account](https://firefox-ci-tc.services.mozilla.com/profile). In case you don't have this permission, file a bugzilla bug like this: [Bug 1651095](https://bugzilla.mozilla.org/show_bug.cgi?id=1651095). When that permission is set, disconnect and reconnect to the VPN.
  - Look at the `XPI Releases` to see if the release is already configured.
  - If we want to configure a new release, choose `New XPI Release`.
    - If your extension is privileged, you must be added to the XPI_PRIVILEGED_BUILD_GROUP user list. Contact the addon-pipeline team.
    - If you don't see your extension listed, you probably skipped [this section of the "adding a new xpi" docs](https://github.com/mozilla-extensions/xpi-manifest/blob/main/docs/adding-a-new-xpi.md#enabling-releases).
  - Choose a `xpi-manifest` repository revision. You probably want the latest. We may make this default to the latest revision on `xpi-manifest/main` at some point.
  - Choose a xpi to build.
  - Choose a source repo revision. You probably want the latest. This revision currently needs to be a recent revision on the release branch (generally `main`).
  - Click `Create Release`.
  - Click `Submit`. This will create the release, but not schedule it.
  - Click the `Build` on the progress bar for the appropriate row (this will be labeled with the XPI name, version, build number).
  - Once the build graph is scheduled, the `Build` will be a link to the build graph.
  - Once the build graph is created, the first half of the progress bar will be green, monitor the build graph for all the jobs to go green, or check email if you're getting notifications.
  - QA can then download the build from the build task (unsigned) or the dep-signing task (signed with the developer key).

At this point QA, developers, or project managers may request changes.

If we need a new release build:

  - Cancel the previous release
  - Repeat the above steps, but for a build `n+1`.

### Signoffs

  - Once the build is complete, it will need to be signed off by two of the groups listed below; via the Promote button.
  - The relevant groups are automatically notified.
    - You will be also notified if you are listed in the additional-emails section for your xpi in the [xpi manifest](https://github.com/mozilla-extensions/xpi-manifest/blob/main/manifests/)
  - When we have the quorum of signoffs, we'll schedule the promote graph, and we'll get a release-signed xpi.
  - Again, the promote button becomes a link to the build graph, wait until they are all finished. The signed xpi can be found as an artifact on the `release-signing-...` task.
  - Once the promote phase is complete, the next phase is to Ship which will need to be signed off by one of two of the groups listed below; via the Ship button.
  - The relevant groups are automatically notified.
    - You will be also notified if you are listed in the additional-emails section for your xpi in the [xpi manifest](https://github.com/mozilla-extensions/xpi-manifest/blob/main/manifests/)
  - When we have the quorum of signoffs, we'll schedule the ship graph, and we'll upload the release-signed xpi to github.
  - Again, the ship button becomes a link to the build graph, wait until they are all finished.
If you need to expedite the release:

  - Try pinging the relevant teams via the #addons-pipeline channel on Slack.
  - Releng should only step in to expedite when requested, and only to unblock urgent requests. If releng signs off, that release should be audited by the appropriate team(s) later.

| Group name | Who | Type of xpi | Notes |
| ---------- | --- | ----------- | ----- |
Add-on Review Team | Add-on Review team | privileged | One of each (Add-on Review Team and Privileged webextension admin) is required to sign off on `privileged` xpis.
Privileged webextension admin | Add-on Review team (+releng as backups) | privileged | One of each (Add-on Review Team and Privileged webextension admin) is required to sign off on `privileged` xpis.
System addon admin | Add-on Review team (+releng as backups) | system | Two of these are required to sign off on `system` xpis.
MozillaOnline privileged webextension team | mozilla-online team (+releng as backups) | mozillaonline-privileged | One of each (team and admin) need to sign off on `mozillaonline-privileged` xpis.
MozillaOnline privileged webextension admin | `:theone` and `:mkaply` (+releng as backups) | mozillaonline-privileged | One of each (team and admin) need to sign off on `mozillaonline-privileged` xpis.
Normandy privileged signoff | (currently only releng) | normandy-privileged | Two are required to sign off on `normandy-privileged` xpis. `normandy-privileged` is deprecated.
