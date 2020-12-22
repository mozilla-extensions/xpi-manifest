# Testing a xpi

After [adding a new xpi](adding-a-new-xpi.md), you almost certainly want to test it locally before moving on to the final release step.

## Local development and testing

For local development and testing, you can use `about:debugging` to side-load an unsigned extension. To enable privileged code to run,
you must first set the `extensions.experiments.enabled` pref to `true`
in `about:config`.

Once you are happy with your changes and push to the
github.com/mozilla-extensions repo, taskcluster will run any
`build` and `test` targets specified in your `package.json`.

Additionally, taskcluster will create a ["dep-signed"](https://wiki.mozilla.org/Add-ons/Extension_Signing) (development signed) build, which
uses the staging root.

## QA the XPI signed with the staging root

This is the final step before sign-off and contains the same content
(other than the signature files) as your production release build.

The [Extension signing docs](https://wiki.mozilla.org/Add-ons/Extension_Signing) go into some detail on extension signing, here are the relevant parts
you need to know:

- the "dep-signed" task generates a XPI artifact signed with the staging root.
- _There is no way to load this build in Firefox Release_. You must use Firefox Nightly or an [unbranded Firefox release build](https://wiki.mozilla.org/Add-ons/Extension_Signing#Unbranded_Builds).
- To allow the XPIs signed with the staging root, create the pref `xpinstall.signatures.dev-root` in `about:config` and set it to `true`.

### Next step: Releasing a XPI

Now that your add-on is tested, the next step is to [release the XPI](releasing-a-xpi.md)
