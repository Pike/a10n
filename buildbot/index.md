---
depth: ../
layout: default
title: a10n &mdash; Buildbot
navigation:
  - header: Buildbot
  - items:
      - Buildbot
      - Repositories
      - Modules
      - Buildbot 0.7.x
      - Poller
      - Changesource
      - Scheduler
      - tree-builder
      - Build Factories
      - compare-locales
---


<h1 id="buildbot" class="well">Buildbot</h1>

The current automation for elmo is built on top of buildbot 0.7.12
plus patches. It's a combination of six different repositories:

Repositories
============

<dl class="dl-horizontal">
<dt>master-ball</dt>
<dd>Configuration of production and test master. Contains a drop of
django, and submodules for buildbot, elmo, locale-inspector. Also
contains the source of the get-pushes twisted daemon.</dd>
<dt>slave-ball</dt>
<dd>Configuration for buildbot slaves, shared between production and
test. Contains submodules for buildbot, compare-locales,
locale-inspector</dd>
<dt>buildbot</dt>
<dd>The <em>l10n-dashboard</em> branch is based on 0.7.12, but
contains a few fixes that were never upstreamed. Technically, Axel may
even be the maintainer of 0.7.x, but never did anything.</dd>
<dt>elmo</dt>
<dd>We're using elmo without submodules to pick up the data models,
and the buildbot-to-elmo status bridge, <code>bb2mbdb</code>.</dd>
<dt>locale-inspector</dt>
<dd>This repo holds the buildbot custom logic, as well as unit and
integration tests. You find changesource, scheduler, build factories,
master steps and slave steps here.</dd>
<dt>compare-locales</dt>
<dd>The actual source comparison code. This is shared with the command
line applications, but called as python module, and produces the json
tree used by elmo.</dd>
<dt></dt>
<dd></dd>
</dl>


Modules
=======

The modules in the buildbot setup match those in the [Overview
page](../). We'll detail a bit the implentations here.

Buildbot 0.7.x
--------------
Buildbot 0.7.x only works against twisted 8.2.0. Tests don't run
against 13.0.0 to start with. Development in buildbot after 0.7 is
moving further away from what elmo needs automation wise, and has
competing concepts. Starting with 0.8, it requires a database, but is
incompatible with the elmo database scheme, and [django in
general](http://trac.buildbot.net/ticket/1053). The separation between
master and slave packages left no blazed path to run integration
tests, too.

Poller
------

A twisted plugin. This is written and run against twisted 8.2.0, which
doesn't support current macs. It's unclear what's needed to run this
against current twisted, 13.0.0 at the time of writing.

The poller queries the elmo database for all singleton repositories,
and all forests. It then queries all forests for their repositories,
and then iterates over all those to find new pushes.

If it finds a push, it caches that, and on the next cycle, inserts all
cached pushes up to that push into the elmo database. This ensures
that we're not missing out on pushes that happened earlier to other
repositories, and thus makes the `push_date` be incremental by row
id. It's doing one http request to the hg server at a time, and has a
mechanism to throttle. That's nice for local setups, but for
production, we're not making use of that. The cycles take some 10
minutes already, waiting longer is just not great.

The http requests are done in an iterator supporting push-back, so
errors during these requests are easily recovered from. An exception
here are 404 errors if a repository is removed upstream. Those [hang
the poller](https://bugzilla.mozilla.org/show_bug.cgi?id=779043).

This piece of code also updates the local clones, and the elmo
database. This is done by a blocking call to elmo's
`pushes.utils.handlePushes`. We're failing to [recover from hg
errors](https://bugzilla.mozilla.org/show_bug.cgi?id=868811) here.

Changesource
------------

The buildbot changesource is implemented in locale-inspector's
`l10ninsp.changes`. It polls the elmo database for new pushes created
by the poller.

The branch of the change is set to the name of the forest of the
repository of the push, if it exists, or just the name of the
repo. That is, a push to `l10n-central/de` sets the branch to
`l10n-central`. It also adds a `locale` attribute to the change
object.

The changesource supports an additional operation called `replay`,
which allows one to replay all changes in the past. That was useful
when we started the production website, and I only had local data. We
could re-build the history of the localizations, including log files
etc.

Scheduler
---------

The schedulers are implemented in locale-inspector's
`l10ninsp.scheduler`. There are two variants, one for apps like
**Firefox**, one for directories like we're using for **gaia**.

The app scheduler is using asynchronous `twisted.web.client.getPage`
requests to load data from the hg server to read configuration via
`l10n.ini` and `all-locales` files. It triggers the initial
configuration by scheduling a `tree-builder` build for each of the
trees it's picking up from `l10nbuilds.ini` in *master-ball*.

tree-builder
------------

The `tree-builder` builder is currently using
`twisted.web.client.getPage` on the master to load `l10n.ini` and
`all-locales` from the hg server. It's parsing the returned data, and
calls back into the app scheduler to configure that.

Build Factories
---------------

*locale-inspector* comes with two build factories,
`l10ninsp.process.Factory` and `.DirFactory`. The special utility of
those factories is that they dynamically add steps to update the
checkouts of the repositories the comparisons need to the version
specified in the build requests.

The dynamic number of steps is another thing where we're breaking
implied contracts of Buildbot.


compare-locales
---------------

`compare-locales` is a combination of a master- and slave-side step
implementation, in `l10ninsp.steps` and `l10ninsp.slave`, resp. The
slave side makes a blocking call into
`Mozilla.CompareLocales.compareApp`, and sends a stdout log and the
detailed json data back to the master. The master-side of the step
adds the stdout blob to the log, and serializes the json data to the
log channel 5. It also updates elmo with creating a new `Run` object
with the summary information, and marks that run as active.

`compare-dirs` is the same thing in green, as the Germans say. It's
merely using a different entry point to compare-locales,
`Mozilla.CompareLocales.compareDirs`.