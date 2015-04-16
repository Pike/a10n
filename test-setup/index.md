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

You'll need

* mercurial and git
* [rabbitmq](http://www.rabbitmq.com/)
* [elasticsearch 1.2.1](https://www.elastic.co/downloads/past-releases/elasticsearch-1-2-1)
* python and virtualenv (2.6 for now) (including headers)
* MySQL (including headers)

If you want to enable error
logging, you'll also need a setup for
[sentry](https://getsentry.com/welcome/). A local install works fine
for testing.

Please check their corresponding documentation for installation notes.

Also make sure that you're having a `~/.hgrc` that specifies your username,

     [ui]
     username = ...


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

    python scripts/create-test-env.py $HOME/stage

This is going to create

* `env`, the virtualenv you'll want to activate, unless noted otherwise
* a staging environment for your hg repositories
  * `$HOME/stage/repos`, with the `mozilla` and `l10n/*` upstream repositories
  * `$HOME/stage/workdir`, with the `mozilla` and `l10n/*` working copies<br>
*You'll edit, commit and push in these repositories.*
  * `$HOME/stage/webdir.conf`, to use to run the webserver

There are a few **configurations** you want to do in *a10n*, the file to edit is `a10n/settings/local.py`. The following should work with a local sqlite database.

    from base import *
    
    SECRET_KEY = 'Do Not Tell Me'
    
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


Use the same configuration here as you do when to setting up **elmo**.
Please check on the elmo wiki on howto
[run elmo locally](https://github.com/mozilla/elmo/wiki/Running-locally).

You'll want to use the same settings for `DATABASES` and `REPOSITORY_BASE` as in *a10n*.

Make sure you did create the database, and ran the initial migrations when
setting up elmo at this point.

In the *elmo* env, you want to load our test fixture next,

    ./manage.py loaddata localhost

This will add the `mozilla` repository and the `l10n` forest to your database,
and thus get them picked up by the automation infrastucture. This fixture
assumes that the hg server is localhost, and `hg serve` runs on port `8001`.
If you tweak either in your local setup, you need to tweak the entries in the
database, too.

<h1 id="running" class="well">Running</h1>

Now that we're through with preparations, it's time to start things
up. The suggested path is to start bots up in the following order, and
shut them down in the reverse order.

1. rabbitmq
1. hg server:
   <pre><code>. env/bin/activate
   cd $HOME/stage/
   hg serve --webdir-conf=webdir.conf -p 8001</code></pre>
1. sentry, if you want to
   <pre><code>sentry runserver 9000</code></pre>
1. a10n hg worker
   <pre><code>. env/bin/activate
   ./scripts/a10n hg</code></pre>
1. the twistd hg poller
   <pre><code>. env/bin/activate
   twistd -n get-pushes</code></pre>

You can start and stop the elmo webserver independently of the
automation pieces.


Doing stuff
-----------

Now that everything is running, let's do something. Whenever you want to
interact with the repositories, you should have the `virtualenv` for a10n
activated:

    . env/bin/activate

Let's push the changes the script prepared in 'mozilla':

    cd $HOME/stage/workdir/mozilla
    hg push

and all our localizations:

    cd ../l10n
    for r in *; do hg -R $r push; done

You should see the new pushes being recognized in the log of the twisted
poller, and then in the a10n worker. You can verify them being added to the
elmo database by looking at
[http://localhost:8000/source/pushes/](http://localhost:8000/source/pushes/).

Running buildbot
----------------

If you're interested in running the buildbot automation to create statistics
in elmo, now is a good time to head over to
[test-master setup](http://pike.github.io/master-ball/test-master/).
