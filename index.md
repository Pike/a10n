---
layout: default
title: a10n &mdash; L10n Automation
navigation:
  - header: Overview
    items:
      - Purpose
      - l10n.ini
      - Directories
  - header: Infrastructure
    items:
      - Infrastructure
      - Poller
      - Repository Handling
      - Changesource
      - Scheduler
      - Trees
      - comparisons
      - en-US
      - l10n
      - Compare jobs
      - compare-locales
      - compare-dirs
      - Collapsing Builds
  - header: Resources
    items:
       - Resources
  - header: Design
    items:
       - Design
---


<h1 id="purpose" class="well">Purpose</h1>

The a10n project feeds elmo with source comparisons between en-US and
localizations. It also gathers data from mozilla's version control
systems (currently hg.mo), and updates the data for those in elmo.

The generated data is stored as a **summary** in the elmo database,
and as a **detailed json**. The latter is currently part of the
buildbot logs, but targeted to [migrate to
elasticsearch](https://bugzilla.mozilla.org/show_bug.cgi?id=857107).

Currently, there are two schemes of comparisons supported:

l10n.ini
--------
*compare-locales* uses **l10n.ini** files to find out what to
do. These configuration files are included in the main mozilla code
bases, and are used for **Firefox**, **Firefox for Android** and
**Thunderbird**. They're mapping one or more repositories with the
upstream code including en-US to one repository per locale. The
fullest example would be `tb_aurora`. It's comparing `mail` etc from
`releases/comm-aurora`, `toolkit` etc from `releases/mozilla-aurora`
with `releases/l10n/mozilla-aurora/ab-CD`.

<table class="table table-bordered small">
<tr>
<th>en-US repo</th><th>dir</th>
<th>l10n repo</th><th>dir</th>
</tr>
<tr>
<td>releases/comm-aurora</td><td>mail/locales/en-US/**</td>
<td>releases/l10n/mozilla-aurora/<em>ab-CD</em></td><td>mail/**</td>
</tr>
<tr>
<td>releases/mozilla-aurora</td><td>toolkit/locales/en-US/**</td>
<td>releases/l10n/mozilla-aurora/<em>ab-CD</em></td><td>toolkit/**</td>
</tr>
<tr>
<td>releases/mozilla-aurora</td><td>security/manager/locales/en-US/**</td>
<td>releases/l10n/mozilla-aurora/<em>ab-CD</em></td><td>security/manager/**</td>
</tr>
</table>

<div class="alert alert-error">This is rather tightly integrated to
the use of different mercurial repositories for different branches. If
we'd switch to git, the split between repositories would likely stay,
but we'd reference different branches inside of a single mozilla
repository for aurora and beta.</div>

Directories
-----------
Projects that don't use the directory structure of Firefox, but need support on the l10n dashboard are supported via a helper repository. The prominent example today is **gaia**, the UI part of **Firefox OS**. For those, a pure en-US repository is created, and compared against a repository per localization next to it. There are some features of *compare-locales* like filtering of entries that are not supported in *compare-dirs*.

<table class="table table-bordered small">
<tr>
<th>en-US repo</th><th>dir</th>
<th>l10n repo</th><th>dir</th>
</tr>
<tr>
<td>gaia-l10n/en-US</td><td>**</td>
<td>gaia-l10n/<em>ab-CD</em></td><td>**</td>
</tr>
</table>

<h1 id="infrastructure" class="well">Infrastructure</h1>

The tasks can be grouped into three buckets:

+ hg poller
+ hg local update, repository and pushes db maintenance.
+ comparisons

These tasks have different concurrency and load characteristics.

Poller
------
The hg poller is mostly waiting for network responses from hg, and is thus well
suited for single-threaded asynchronous callback code. It should be able to
throttle the load on the server, but also able to scale to parallel requests.

<div class="alert"><strong>Constraints:</strong> The current code ensures that
push data and push id are providing the same order. This constraint needs
review, and can likely be dropped.</div>

Repository handling
-------------------
This code segment updates the local clones that are shared among the elmo
hardware, and updates the database to be in-line with that state.

<div class="alert"><strong>Constraints:</strong> There should only
ever be one task per repo here. The tasks do not touch the working
directory, though.</div>

Changesource
------------
The Changesource observes new pushes to repositories, extracts the
files for those changes and submits them to the schedulers.

<div class="alert alert-error">This is very bound to mercurial, and
it's notion of having files as part of the changeset info right
now. In a git-world, this would need to know the previous ref of the
updated branch, and use a diff algorithm to find affected files.</div>

Scheduler
---------
The scheduler observes changes coming from the changesource, and
decides for which of those to run which automation. It's schematically
composed of three decision makers, triggering three automation tasks.

The scheduler is configured by <strong>Trees</strong>, which associate
repositories, directories, and a group of l10n repositories (forest) with a
compare-locales (or -dirs) setup.

### Trees
The first decision is whether to reconfigure the scheduler. This
happens if the l10n.ini files change, or if the set of affected
locales change.

If the l10n.inis change, 
1. the schedulers stop taking new changes
2. the l10n.inis for the affected trees are reloaded
3. if the changes affected the configuration
    + trigger a rebuild of all locales for that tree with their latest revision

If the all-locales change,
1. load the changed file, and parse it
2. if there are new locales
    + trigger a rebuild of that locale against their latest revision
3. if there are locales dropped
    + update elmo to deactivate that locale's latest `Run`

### comparisons
The **compare-locales** jobs are triggered either by changes to one of
the repositories holding the en-US files, or to one of the
repositories in the forest.

#### en-US
Each tree is associated with a list of repositories, and a list of directories. The configuration process gathers and resorts those. Thus, the scheduler algorithm can work the opposite way around.

1. For the repository of this change, find all affecting directories
2. For each file in the change, see if it affects the subdirectory `locales/en-US` of any of our directories above. If so, note the tree.
3. For each affected tree:
    1. find the latest revisions of the other en-US repos that are not changed
    2. for each affected locale:
        1. find the latest revision of the l10n repo
        2. trigger a comparison, specifying all revisions of the repos, the tree, the locale,
           the source time (push_date of the change), and a reference back to the change

### l10n
Each tree is associated with exactly one forest, with a repository for each locale.

1. For the repository of this change, check if it belongs to an l10n forest. If so, deduce locale code from repository name, otherwise abort.
2. For the forest, figure out which trees it affects, both compare-locales and compare-dirs
3. If it's a compare-dirs tree, skip below
4. For each compare-locales tree, go through all files and see if it's
touching a file in one of the directories for that tree. Note that
tree.
5. For each affected tree:
    1. check if the locale is enable, if not, skip
    2. find all revisions for the en-US repositories
    3. trigger a comparison, specifying all revisions of the repos, the tree, the locale,
       the source time (push_date of the change), and a reference back to the change
6. For each compare-dirs tree:
    1. if the locale is en-US, do the following for all enabled locales instead of the locale of the change.
    2. otherwise check if the locale is enable for this tree. if not, skip
    3. find the revision of the en-US or l10n repository
    4. trigger a compare-dirs job, specifying both en-US and l10n revision, the tree, the locale,
       the source time, and a reference back to the change

Compare jobs
------------
The comparison jobs are two-fold, *compare-locales* and
*compare-dirs*. They do share some characteristics, though.

The comparisons are done on disk, on checked out files. For all
repositories included in the comparison, the repositories need to be
checked out with the given revisions, in the same directory structure
as they're on the upstream server. I.e.,
http://hg.mozilla.org/l10n-central/de/ is checked out to
`l10n-central/de`. After the check-out, version control isn't needed,
thus doing this on `hg shares` or `git clone -s` is fine.

If multiple comparisons run on the same machine, there shouldn't be
conflicting check-outs. In most scenarios where jobs are running in
parallel, you're seeing many jobs on the same revision of en-US, thus
sharing the working dir makes the comparisons benefit from OS disk
caches. Thus we should be careful about synchronizing jobs on the same
hardware.

### compare-locales
This job requires a revision for each repository, and the data to get
to the entry point l10n.ini, as well as the locale to compare to.

### compare-dirs
This job requires a revision for both en-US and the locale, the
locale, and the forest in which the two repositories reside.

### Collapsing Builds
Every now and then, you get more than one change that trigger the same
locale for the same tree. Merge days are a perfect example, where we
change both en-US and l10n, all around the same time. In those cases,
it's a fair optimization to only compare the latest revisions against
each other.

This is fairly trivial as long as all changes are globally ordered,
just update the existing request to take a new revision. If you don't
know that the order of the changes is given, things are more tricky,
i.e., you need to find out which of the available revisions is newer
than the other.


<h1 id="resources" class="well">Resources</h1>

Let's wrap this up by summarizing the jobs and the affected resources.

<table class="table table-bordered">
<tr>
<td></td>
<td>upstream repo</td><td>elmo db</td><td>local clones</td><td>workdir</td><td>ES</td>
</tr>
<tr>
<td>poller</td>
<td>R</td><td>R</td><td></td><td></td><td></td>
</tr>
<tr>
<td>repo</td>
<td>R</td><td>W</td><td>W</td><td></td><td></td>
</tr>
<tr>
<td>changesource</td>
<td></td><td>?</td><td>R</td><td></td><td></td>
</tr>
<tr>
<td>scheduler</td>
<td>R</td><td>R</td><td></td><td></td><td></td>
</tr>
<tr>
<td>compare</td>
<td></td><td>W</td><td></td><td>RW</td><td>W</td>
</tr>
<tr class="info">
<td>elmo</td>
<td></td><td>RW</td><td>R</td><td></td><td>R</td>
</tr>
</table>


<h1 id="design" class="well">Design</h1>

This automation is currently implemented based on [buildbot 0.7.12+](buildbot).

The a10n repo will hold an implementation based on [queues and celery](design).