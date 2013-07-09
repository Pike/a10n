---
depth: ../
layout: default
title: a10n &mdash; Test Setup
navigation:
  - header: Test Setup
  - items:
      - Environment
      - Requirements
      - Initial setup
      - Running
      - Doing stuff
---

<div class="alert">This document will evolve as the implementations do.</div>


<h1 id="environment" class="well">Environment</h1>

To test *a10n*, you want a test environment. We're providing a script
to set one up, including

* **virtualenv** with all dependencies
* **hg server** with dummy repositories for `l10n`, and `mozilla` for en-US
* **working clones** of the upstream hg repos, with example content, ready to push
* a matching configuration for an **hg webserver**


Requirements
------------

You'll need mercurial, git, and
[rabbitmq](http://www.rabbitmq.com/). If you want to enable error
logging, you'll also need a setup for
[sentry](https://getsentry.com/welcome/). A local install works fine
for testing.

Please check their corresponding documentation for installation notes.


Initial setup
-------------

First, you need **a10n**

    git clone git@github.com:Pike/a10n.git
    cd a10n

and then you get the submodules. You only want the first level of
submodules, not recursive.

    git submodule init
    git submodule update

Next, run the setup script,

    python scripts/create-test-env.py $(HOME)/stage

This is going to create

* `@env`, the virtualenv you'll want to activate, unless noted otherwise
* `$(HOME)/stage/repos`, with the `mozilla` and `l10n/*` upstream repositories
* `$(HOME)/stage/workdir`, with the `mozilla` and `l10n/*` working clones
* `$(HOME)/stage/webdir.conf`, to use to run the webserver

There are a few **configurations** you want to do in *a10n*, the file to edit is `a10n/settings/local.py`. The following should work with a local sqlite database.

    from base import *
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/my/home/a10n/a10n/settings/db.sql',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': ''
        },
    }
    REPOSITORY_BASE = '/my/home/stage/repos/'
    
    TRANSPORT = 'amqp://guest:guest@localhost:5672//'
    
    # if you want to test the Sentry
    #RAVEN_CONFIG = {
    #    'dsn': 'http://user:pw@localhost:9000/2'  # see api keys on your local sentry install
    #}


Onwards to setting up **elmo**. Please check on the elmo wiki on how
to [run elmo
locally](https://github.com/mozilla/elmo/wiki/Running-locally).

You'll want to use the same settings for `DATABASES` and `REPOSITORY_BASE` as in *a10n*.

In the *elmo* env, you want to load our test fixture next,

    ./manage.py loaddata localhost


<h1 id="running" class="well">Running</h1>

Now that we're through with preparations, it's time to start things
up. The suggested path is to start bots up in the following order, and
shut them down in the reverse order.

1. rabbitmq
1. hg server:
   <pre><code>. @env/bin/activate
   cd $(HOME)/stage/
   hg serve --webdir-conf=webdir.conf -p 8001</code></pre>
1. sentry, if you want to
   <pre><code>sentry runserver 9000</code></pre>
1. a10n hg worker
   <pre><code>. @env/bin/activate
   ./scripts/a10n hg</code></pre>
1. the twistd hg poller
   <pre><code>. @env/bin/activate
   twistd -n get-pushes</code></pre>

You can start and stop the elmo webserver independently of the
automation pieces.


Doing stuff
-----------

Now that everything is running, let's do something.

    . @env/bin/activate
    cd $(HOME)/stage/workdir/mozilla
    hg push
    cd ../l10n
    for r in *; do hg -R $r push; done

You should see the new pushes being recognized in the log of the twisted poller, and then in the a10n worker. You can verify them being added to the elmo database by looking at [http://localhost:8000/source/pushes/](http://localhost:8000/source/pushes/).