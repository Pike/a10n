# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''Twisted plugin to scrape pushlog json hooks of the upstream repos.
'''

from __future__ import absolute_import
from zope.interface import implements

from twisted.python import usage, log
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.internet import task, defer, reactor
from twisted.web.client import getPage, HTTPClientFactory
from twisted.web.error import Error as WebError

from datetime import datetime
import os
import json

import site
import six
from six.moves import map
site.addsitedir('vendor-local')

from kombu import Connection
from kombu.common import maybe_declare
from kombu.pools import producers
from a10n.hg_elmo.queues import hg_exchange


class Options(usage.Options):
    optParameters = [["settings", "s", None,
                      "Django settings module. DEFAULT: a10n.settings"],
                     ["time", "t", "1", "Poll every n seconds."],
                     ["limit", "l", "200", "Limit pushes to n at a time."]
                     ]


class pushback_iter(object):
    '''Utility iterator that can deal with pushed back elements.

    This behaves like a regular iterable, just that you can call
        iter.pushback(item)
    to get the givem item as next item in the iteration.
    '''
    def __init__(self, iterable):
        self.it = iter(iterable)
        self.pushed_back = []

    def __iter__(self):
        return self

    def __nonzero__(self):
        if self.pushed_back:
            return True

        try:
            self.pushed_back.insert(0, next(self.it))
        except StopIteration:
            return False
        else:
            return True

    def next(self):
        if self.pushed_back:
            return self.pushed_back.pop()
        return next(self.it)

    def pushback(self, item):
        self.pushed_back.append(item)


def getPoller(options):
    os.environ["DJANGO_SETTINGS_MODULE"] = (options["settings"] or
                                            "a10n.settings")
    from django.conf import settings
    from life.models import Repository, Forest, Locale
    import django
    django.setup()
    from django.db import connection as db_connection
    from django.db.models import Max

    class PushPoller(object):
        '''PushPoller stores the state of our coopertive iterator.

        The actual worker is poll().
        '''

        debug = False

        def __init__(self, opts):
            self.limit = int(opts.get('limit', 200))
            self.timeout = 10
            self.repos = []
            self.cache = {}
            self.moredata = {}
            self.latest_push = {}
            self.start_cycle = None
            self.sentry = None
            if hasattr(settings, 'RAVEN_CONFIG'):
                from raven import Client
                self.sentry = Client(**settings.RAVEN_CONFIG)
            pass

        def getURL(self, repo, limit):
            # If we haven't seen this repo yet
            # only store last-known-push if there
            # are existing pushes.
            # Otherwise, let's keep this unset
            # and use that to trigger the initial clone
            # after loading the initial json-pushes.
            # That will then set latest_push to something,
            # maybe even just 0 for an empty/unpushed repo.
            if repo.id not in self.latest_push:
                lkp = repo.last_known_push()
                if lkp:
                    self.latest_push[repo.id] = lkp
            else:
                lkp = self.latest_push[repo.id]
            return '%sjson-pushes?startID=%d&endID=%d' % \
                (repo.url, lkp, lkp + limit)

        def handlePushes(self, repo_id, submits):
            if submits:
                self.latest_push[repo_id] = submits[-1]['id']
            else:
                # empty/unpushed repo, use 0 as last push id.
                self.latest_push[repo_id] = 0
            connection = Connection(settings.TRANSPORT)
            with producers[connection].acquire(block=True) as producer:
                maybe_declare(hg_exchange, producer.channel)
                msg = {'type': 'hg-push',
                       'repository_id': repo_id,
                       'pushes': submits}
                try:
                    producer.publish(msg, exchange=hg_exchange,
                                     routing_key='hg')
                except KeyboardInterrupt:
                    raise
                except Exception:
                    if self.sentry:
                        self.sentry.captureException()
                    raise

        def poll(self):
            '''poll iterates over the repos and updates the local database.

            The actual updates are done in processPushes.

            The iterator stores the latest json from the upstream repos,
            and submits those on the next round. That way, we can add
            all pushes in that timewindow in order, which helps when
            actually polling the db to get the changes in
            chronological order.

            For repos that have more pushes than the current limit, we
            poll them again immediately to get further data.

            This iterator doesn't terminate, but gets killed together
            with the service.
            '''
            # get our last-known push IDs for all non-archived repos
            self.latest_push.update(
                Repository.objects
                .filter(archived=False, push__isnull=False)
                .annotate(last_push=Max('push__push_id'))
                .values_list('id', 'last_push'))
            while True:
                n = datetime.now()
                if self.start_cycle is not None:
                    lag = n - self.start_cycle
                    log.msg("Cycle took %d seconds" % lag.seconds)
                self.start_cycle = n
                db_connection.close()
                repos = list(Repository.objects.filter(forest__isnull=True,
                                                       archived=False))
                nonarchived_forests = (Forest.objects
                                       .filter(archived=False))
                self.forests = pushback_iter(nonarchived_forests)
                for forest in self.forests:
                    url = str(forest.url + '?style=json')
                    d = getPage(url, timeout=self.timeout)
                    d.addCallback(self.gotForest, forest, repos)
                    d.addErrback(self.failedForest, forest)
                    yield d
                self.repos = pushback_iter(repos)
                for repo in self.repos:
                    d = None
                    if repo.id in self.cache:
                        pushes = self.cache.pop(repo.id)
                        self.processPushes(pushes, repo)
                        if pushes:
                            if self.debug:
                                log.msg("Still have %s left for %s" %
                                        (", ".join(map(str, pushes)),
                                         repo.name))
                            self.cache[repo.id] = pushes
                            d = defer.succeed(None)
                    if d is None:
                        jsonurl = self.getURL(repo, self.limit)
                        if self.debug:
                            log.msg(jsonurl)
                        d = getPage(str(jsonurl), timeout=self.timeout)
                        d.addCallback(self.loadJSON, repo)
                        d.addErrback(self.jsonErr, repo)
                    yield d

        def loadJSON(self, page, repo):
            pushes = json.loads(page)
            if not pushes and repo.id in self.latest_push:
                # No new pushes to an existing repo
                return
            log.msg("%s got %d pushes" % (repo.name, len(pushes)))
            # convert pushes to sorted list
            if repo.id not in self.cache:
                self.cache[repo.id] = []
            # pushes maps string keys to pushes, we want to order by number
            push_blobs = [dict(list(pushes[id].items()) + [('id', int(id))])
                          for id in six.iterkeys(pushes)]
            push_blobs.sort(key=lambda blob: blob['id'])
            self.cache[repo.id] += push_blobs
            # signal to load more data if this push hit the limits
            if len(pushes) == self.limit:
                self.moredata[repo.id] = True

        def processPushes(self, pushes, repo):
            '''process the pushes for the given repository.

            This code also adds all pushes that are older than the
            newest push on this repo, in order. If the amount of pushes
            exceeds the limit, pushback the current repo to get more changes.
            If we're emptying another's repo push cache, re-poll???.
            '''
            if len(pushes) == self.limit:
                self.repos.pushback(repo)
            if self.debug:
                log.msg("submitting %s to %s" % (', '.join(map(str, pushes)),
                                                 repo.name))

            tips = sorted(((id, p[0]['date'])
                           for id, p in six.iteritems(self.cache) if p),
                          key=lambda t: t[1])
            if not pushes:
                # This is a new repository, let's notify the hg worker
                # to get us a clone
                self.handlePushes(repo.id, [])
            while pushes:
                if tips and pushes[0]['date'] > tips[0][1]:
                    # other repos come first, get them done
                    other = self.cache[tips[0][0]]
                    if len(tips) > 1:
                        stopdate = min(pushes[0]['date'],
                                       self.cache[tips[1][0]][0]['date'])
                    else:
                        stopdate = pushes[0]['date']
                    i = 0
                    while i < len(other) and \
                            other[i]['date'] <= stopdate:
                        i += 1
                    submits = other[:i]
                    if self.debug:
                        log.msg("pushing %s to %d" %
                                (", ".join(map(str, submits)),
                                 tips[0][0]))
                    self.handlePushes(tips[0][0], submits)
                    del other[:i]
                    if not other:
                        # other repo is empty
                        # let's see if we need to load more
                        if tips[0][0] in self.moredata:
                            self.moredata.pop(tips[0][0])
                            other_repo = Repository.objects.get(id=tips[0][0])
                            self.repos.pushback(other_repo)
                            return
                    tips = sorted(((id, p[0]['date'])
                                   for id, p in six.iteritems(self.cache) if p),
                                  key=lambda t: t[1])
                else:
                    i = 0
                    if tips:
                        stopdate = self.cache[tips[0][0]][0]['date']
                        while i < len(pushes) and \
                                pushes[i]['date'] <= stopdate:
                            i += 1
                    else:
                        i = len(pushes)
                    submits = pushes[:i]
                    if self.debug:
                        log.msg("pushing %s to %d" %
                                (", ".join(map(str, submits)),
                                 repo.id))
                    self.handlePushes(repo.id, submits)
                    del pushes[:i]

        def gotForest(self, page, forest, repos):
            entries = json.loads(page)['entries']
            locale_codes = [entry['name'] for entry in entries]
            q = forest.repositories.filter(locale__code__in=locale_codes)
            repos += list(q.filter(archived=False))
            known_locales = set(q.values_list('locale__code', flat=True))
            new_locales = set(locale_codes) - known_locales
            for locale in new_locales:
                locale, _ = Locale.objects.get_or_create(code=locale)
                name = forest.name + u'/' + locale.code
                url = u'%s%s/' % (forest.url, locale.code)
                if self.debug:
                    log.msg(u"adding %s: %s" % (name, url))
                # Forests are holding l10n repos, set locale
                r = Repository.objects.create(name=name, url=url,
                                              locale=locale,
                                              forest=forest)
                repos.append(r)
            # if there's a repo in the forest that's removed upstream,
            # it should be archived
            cnt = (forest.repositories
                   .exclude(locale__code__in=locale_codes)
                   .exclude(archived=True)
                   .update(archived=True))
            if cnt:
                log.msg(u"Archived %s repos in %s" % (cnt, forest.name))

        def failedForest(self, failure, forest):
            if failure.check(task.SchedulerStopped):
                failure.raiseException()
            log.err(failure, "failed to load %s" % forest.name)
            self.forests.pushback(forest)
            return self.backoff()

        def jsonErr(self, failure, repo):
            if failure.check(task.SchedulerStopped):
                failure.raiseException()
            if failure.check(WebError) and failure.value.status == '404':
                repo.archived = True
                repo.save()
                log.msg('Archived %s, it is not available upstream no more' %
                        repo.name)
                return
            log.err(failure,
                    "failed to load json for %s, adding back" % repo.name)
            self.repos.pushback(repo)
            return self.backoff()

        def backoff(self):
            # back off a little
            d = defer.Deferred()
            reactor.callLater(5, lambda: d.callback(None))
            return d

    pp = PushPoller(options)
    return pp.poll()


class PacedCooperator(internet.CooperatorService):
    def __init__(self, wait):
        self.wait = wait
        self.coop = task.Cooperator(started=False,
                                    scheduler=self.sched)

    def sched(self, x):
        return reactor.callLater(self.wait, x)


class MyServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "get-pushes"
    description = "Gotcha grabbin' repos."
    options = Options

    def makeService(self, options):
        """
        Construct a TCPServer from a factory defined in myproject.
        """
        # set umask back to public reading against twistd daemonize
        os.umask(18)
        HTTPClientFactory.noisy = False
        poller = getPoller(options)
        timer = float(options['time'])
        s = PacedCooperator(timer)
        s.coiterate(poller)
        return s


# Now construct an object which *provides* the relevant interfaces
# The name of this variable is irrelevant, as long as there is *some*
# name bound to a provider of IPlugin and IServiceMaker.

serviceMaker = MyServiceMaker()
