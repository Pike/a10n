---
depth: ../
layout: default
title: a10n &mdash; Design
navigation:
  - header: Design
  - items:
      - Queues
      - Implementation
      - Configuration
      - Entrypoints
      - Hg Poller
      - Workers
      - Mercurial
---

<div class="alert">This document will evolve as the implementations do.</div>


<h1 id="queues" class="well">Queues</h1>

The backbone of the a10n l10n automation is **queues**. Queues enable
us to run changes through the system, modify them, and fork
them. Queues enable some processing steps to be monolithic and state
heavy, while other processing steps are lightweight on status and can
be parallized.


Implementation
--------------

The implementation of a10n is in python. We're using kombu as
low-level queue API, and rabbitmq as queue implementation. Redis as
queue backend doesn't seem to support `requeue`, so even if we use


Configuration
-------------

The configuration is held in `a10n/autosettings`, a python module
suitable to configure `django`. Local configurations go into
`a10n/local.py`, an adaptation of `a10n/local.py-dist`.
redis for other aspects, the queue itself should be rabbitmq.


<h1 id="entrypoints" class="well">Entrypoints</h1>

The entrypoints to the queues are the version control systems. We're starting off with a poller on http://hg.mozilla.org/, which is ported over from master-ball.


Hg Poller
---------

The hg poller is based on `twisted` (13.0.0 at this point). It's feeding `hg-push` events into the `hg` queue. These events have the following structure:

{% highlight json %}
{
    "type": "hg-push",
    "repository_id": int,
    "pushes":
    [
        {
            "id": int,
            "date": int,
            "user": str,
            "changesets": [str]
        }
    ]
}
{% endhighlight %}


<h1 id="workers" class="well">Workers</h1>

Workers may be singletons or parallelized tasks. Singletons are mere
`kombu` workers with `Consumer`s, whereas parallized tasks are
implemented on top of `celery`.

Mercurial
---------

The mercurial worker listens to the `hg-push` messages on the `hg`
queue. It pull local clones and updates the elmo database by
forwarding the data from the message on to 'elmo's
`pushes.utils.handlePushes`.

The worker implements a simple error recovery, and retries on failures
inside `handlePushes`, for `autosettings.MAX_HG_RETRIES` tries. If
configured, it forwards the failures to a sentry installation.
