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


<svg xmlns="http://www.w3.org/2000/svg" xmlns:xl="http://www.w3.org/1999/xlink" version="1.1" viewBox="8 12 494 439" width="494pt" height="439pt"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:date>2013-06-13 16:17Z</dc:date><!-- Produced by OmniGraffle Professional 5.4.3 --></metadata><defs><filter id="Shadow" filterUnits="userSpaceOnUse"><feGaussianBlur in="SourceAlpha" result="blur" stdDeviation="3.488"/><feOffset in="blur" result="offset" dx="0" dy="4"/><feFlood flood-color="black" flood-opacity=".75" result="flood"/><feComposite in="flood" in2="offset" operator="in"/></filter><filter id="Shadow_2" filterUnits="userSpaceOnUse"><feGaussianBlur in="SourceAlpha" result="blur" stdDeviation="3.488"/><feOffset in="blur" result="offset" dx="0" dy="4"/><feFlood flood-color="gray" flood-opacity=".75" result="flood"/><feComposite in="flood" in2="offset" operator="in"/></filter><filter id="Shadow_3" filterUnits="userSpaceOnUse"><feGaussianBlur in="SourceAlpha" result="blur" stdDeviation="3.488"/><feOffset in="blur" result="offset" dx="0" dy="4"/><feFlood flood-color="#7d7d7d" flood-opacity=".75" result="flood"/><feComposite in="flood" in2="offset" operator="in"/></filter><font-face font-family="Helvetica" font-size="13" units-per-em="1000" underline-position="-75.683594" underline-thickness="49.31641" slope="0" x-height="522.94922" cap-height="717.2852" ascent="770.0196" descent="-229.98048" font-weight="500"><font-face-src><font-face-name name="Helvetica"/></font-face-src></font-face><font-face font-family="Helvetica" font-size="14" units-per-em="1000" underline-position="-75.683594" underline-thickness="49.316406" slope="0" x-height="522.94922" cap-height="717.28516" ascent="770.01953" descent="-229.98047" font-weight="500"><font-face-src><font-face-name name="Helvetica"/></font-face-src></font-face><marker orient="auto" overflow="visible" markerUnits="strokeWidth" id="FilledArrow_Marker" viewBox="-1 -4 10 8" markerWidth="10" markerHeight="8" color="black"><g><path d="M 8 0 L 0 -3 L 0 3 Z" fill="currentColor" stroke="currentColor" stroke-width="1"/></g></marker><marker orient="auto" overflow="visible" markerUnits="strokeWidth" id="FilledArrow_Marker_2" viewBox="-1 -4 10 8" markerWidth="10" markerHeight="8" color="#7e7e7e"><g><path d="M 8 0 L 0 -3 L 0 3 Z" fill="currentColor" stroke="currentColor" stroke-width="1"/></g></marker><font-face font-family="Helvetica" font-size="10" units-per-em="1000" underline-position="-75.683594" underline-thickness="49.316406" slope="0" x-height="522.94922" cap-height="717.28516" ascent="770.01953" descent="-229.98047" font-weight="500"><font-face-src><font-face-name name="Helvetica"/></font-face-src></font-face><marker orient="auto" overflow="visible" markerUnits="strokeWidth" id="FilledArrow_Marker_3" viewBox="-1 -4 10 8" markerWidth="10" markerHeight="8" color="#7e7e7e"><g><path d="M 8 0 L 0 -3 L 0 3 Z" fill="currentColor" stroke="currentColor" stroke-width="1"/></g></marker></defs><g stroke="none" stroke-opacity="1" stroke-dasharray="none" fill="none" fill-opacity="1"><title>Canvas 1</title><rect fill="white" width="576" height="733"/><g><title>Layer 1</title><g><use xl:href="#id1_Graphic" filter="url(#Shadow)"/><use xl:href="#id35_Graphic" filter="url(#Shadow_2)"/><use xl:href="#id19_Graphic" filter="url(#Shadow)"/><use xl:href="#id37_Graphic" filter="url(#Shadow_2)"/><use xl:href="#id38_Graphic" filter="url(#Shadow_2)"/><use xl:href="#id11_Graphic" filter="url(#Shadow)"/><use xl:href="#id40_Graphic" filter="url(#Shadow_2)"/><use xl:href="#id41_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id42_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id43_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id44_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id46_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id47_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id48_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id49_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id50_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id53_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id54_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id55_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id57_Graphic" filter="url(#Shadow_3)"/><use xl:href="#id58_Graphic" filter="url(#Shadow_3)"/></g><g id="id1_Graphic"><path d="M 45.35433 28.346457 L 124.72441 28.346457 C 134.112755 28.346457 141.73228 41.04567 141.73228 56.692913 C 141.73228 72.340157 134.112755 85.03937 124.72441 85.03937 L 45.35433 85.03937 C 35.965984 85.03937 28.346457 72.340157 28.346457 56.692913 C 28.346457 41.04567 35.965984 28.346457 45.35433 28.346457" fill="white"/><path d="M 45.35433 28.346457 L 124.72441 28.346457 C 134.112755 28.346457 141.73228 41.04567 141.73228 56.692913 C 141.73228 72.340157 134.112755 85.03937 124.72441 85.03937 L 45.35433 85.03937 C 35.965984 85.03937 28.346457 72.340157 28.346457 56.692913 C 28.346457 41.04567 35.965984 28.346457 45.35433 28.346457" stroke="black" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(44.68504 48.692913)" fill="black"><tspan font-family="Helvetica" font-size="13" font-weight="500" x="15.420737" y="13" textLength="49.867188">hg poller</tspan></text></g><g id="id35_Graphic"><path d="M 357.16534 28.346457 L 436.53542 28.346457 C 445.92377 28.346457 453.5433 41.04567 453.5433 56.692913 C 453.5433 72.340157 445.92377 85.03937 436.53542 85.03937 L 357.16534 85.03937 C 347.777 85.03937 340.15747 72.340157 340.15747 56.692913 C 340.15747 41.04567 347.777 28.346457 357.16534 28.346457" fill="white"/><path d="M 357.16534 28.346457 L 436.53542 28.346457 C 445.92377 28.346457 453.5433 41.04567 453.5433 56.692913 C 453.5433 72.340157 445.92377 85.03937 436.53542 85.03937 L 357.16534 85.03937 C 347.777 85.03937 340.15747 72.340157 340.15747 56.692913 C 340.15747 41.04567 347.777 28.346457 357.16534 28.346457" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(356.49605 48.692913)" fill="#7e7e7e"><tspan font-family="Helvetica" font-size="13" font-weight="500" fill="#7e7e7e" x="12.1739105" y="13" textLength="56.36084">git source</tspan></text></g><g id="id19_Graphic"><rect x="28.346457" y="141.732285" width="113.385826" height="42.519684" fill="white"/><rect x="28.346457" y="141.732285" width="113.385826" height="42.519684" stroke="black" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(33.346457 154.49213)" fill="black"><tspan font-family="Helvetica" font-size="14" font-weight="500" x="24.84135" y="14" textLength="53.703125">hg_elmo</tspan></text></g><line x1="85.03937" y1="85.03937" x2="85.03937" y2="131.832285" marker-end="url(#FilledArrow_Marker)" stroke="black" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><g id="id37_Graphic"><rect x="340.15747" y="141.732285" width="113.385826" height="42.519684" fill="white"/><rect x="340.15747" y="141.732285" width="113.385826" height="42.519684" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(345.15747 154.49213)" fill="#7e7e7e"><tspan font-family="Helvetica" font-size="14" font-weight="500" fill="#7e7e7e" x="40.013714" y="14" textLength="23.358398">???</tspan></text></g><g id="id38_Graphic"><line x1="396.85038" y1="85.03937" x2="396.85038" y2="131.832285" marker-end="url(#FilledArrow_Marker_2)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id11_Graphic"><rect x="212.59842" y="141.732285" width="56.692913" height="42.519684" fill="white"/><path d="M 212.59842 141.732285 L 269.29133 141.732285 M 269.29133 184.25197 L 212.59842 184.25197" stroke="black" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(217.59842 156.99213)" fill="black"><tspan font-family="Helvetica" font-size="10" font-weight="500" x="12.509054" y="10" textLength="21.674805">elmo</tspan></text></g><line x1="141.73228" y1="162.99213" x2="202.69842" y2="162.99213" marker-end="url(#FilledArrow_Marker)" stroke="black" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><g id="id40_Graphic"><line x1="340.15747" y1="162.99213" x2="279.19133" y2="162.99213" marker-end="url(#FilledArrow_Marker_2)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id41_Graphic"><rect x="184.25197" y="283.46457" width="113.385826" height="42.519684" fill="white"/><rect x="184.25197" y="283.46457" width="113.385826" height="42.519684" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(189.25197 296.22441)" fill="#7d7d7d"><tspan font-family="Helvetica" font-size="14" font-weight="500" fill="#7d7d7d" x="20.172405" y="14" textLength="63.041016">Scheduler</tspan></text></g><g id="id42_Graphic"><path d="M 85.03937 184.25197 L 85.03937 196.15197 L 85.03937 234.15197 L 240.94488 234.15197 L 240.94488 271.56457 L 240.94488 273.56457" marker-end="url(#FilledArrow_Marker_3)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id43_Graphic"><rect x="340.15747" y="240.94489" width="56.692913" height="42.519684" fill="white"/><rect x="340.15747" y="240.94489" width="56.692913" height="42.519684" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(345.15747 250.20473)" fill="#7d7d7d"><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="14.730734" y="10" textLength="17.231445">tree</tspan><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="10.0041714" y="22" textLength="21.123047">confi</tspan><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="31.127218" y="22" textLength="5.5615234">g</tspan></text></g><g id="id44_Graphic"><rect x="425.19684" y="240.94489" width="56.692913" height="42.519684" fill="white"/><rect x="425.19684" y="240.94489" width="56.692913" height="42.519684" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(430.19684 250.20473)" fill="#7d7d7d"><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="14.730734" y="10" textLength="17.231445">tree</tspan><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="10.0041714" y="22" textLength="21.123047">confi</tspan><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="31.127218" y="22" textLength="5.5615234">g</tspan></text></g><g id="id46_Graphic"><path d="M 297.6378 304.72441 L 309.5378 304.72441 L 368.50393 304.72441 L 368.50393 295.36457 L 368.50393 293.36457" marker-end="url(#FilledArrow_Marker_3)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id47_Graphic"><path d="M 297.6378 304.72441 L 309.5378 304.72441 L 453.5433 304.72441 L 453.5433 295.36457 L 453.5433 293.36457" marker-end="url(#FilledArrow_Marker_3)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id48_Graphic"><path d="M 368.50393 240.94489 L 368.50393 229.04489 L 240.94488 229.04489 L 240.94488 271.56457 L 240.94488 273.56457" marker-end="url(#FilledArrow_Marker_3)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id49_Graphic"><path d="M 453.5433 240.94489 L 453.5433 229.04489 L 240.94488 229.04489 L 240.94488 271.56457 L 240.94488 273.56457" marker-end="url(#FilledArrow_Marker_3)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id50_Graphic"><rect x="85.03937" y="384" width="85.03937" height="42.519684" fill="white"/><rect x="85.03937" y="384" width="85.03937" height="42.519684" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(90.03937 399.25984)" fill="#7d7d7d"><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="16.955719" y="10" textLength="41.12793">Compare</tspan></text></g><g id="id53_Graphic"><rect x="198.42519" y="384.00003" width="85.03937" height="42.519684" fill="white"/><rect x="198.42519" y="384.00003" width="85.03937" height="42.519684" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(203.42519 399.25987)" fill="#7d7d7d"><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="16.955719" y="10" textLength="41.12793">Compare</tspan></text></g><g id="id54_Graphic"><rect x="311.811" y="384.00003" width="85.03937" height="42.519684" fill="white"/><rect x="311.811" y="384.00003" width="85.03937" height="42.519684" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/><text transform="translate(316.811 399.25987)" fill="#7d7d7d"><tspan font-family="Helvetica" font-size="10" font-weight="500" fill="#7d7d7d" x="16.955719" y="10" textLength="41.12793">Compare</tspan></text></g><g id="id55_Graphic"><path d="M 240.94488 354.88425 L 240.94487 372.10003 L 240.94487 374.10003" marker-end="url(#FilledArrow_Marker_3)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id57_Graphic"><path d="M 240.94488 354.88425 L 127.55905 354.88425 L 127.55905 372.1 L 127.55905 374.1" marker-end="url(#FilledArrow_Marker_3)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g><g id="id58_Graphic"><path d="M 240.94488 325.98425 L 240.94488 337.88425 L 240.94488 354.88425 L 354.33069 354.88425 L 354.33069 372.10003 L 354.33069 374.10003" marker-end="url(#FilledArrow_Marker_3)" stroke="#7e7e7e" stroke-linecap="round" stroke-linejoin="round" stroke-width="1"/></g></g></g></svg>


Implementation
--------------

The implementation of a10n is in python. We're using kombu as
low-level queue API, and rabbitmq as queue implementation. Redis as
queue backend doesn't seem to support `requeue`, so even if we use
redis for other aspects, the queue itself should be rabbitmq.


Configuration
-------------

The configuration is held in `a10n/settings`, a python module
suitable to configure `django`. Local configurations go into
`a10n/local.py`, an adaptation of `a10n/local.py-dist`.


<h1 id="entrypoints" class="well">Entrypoints</h1>

The entrypoints to the queues are the version control systems. We're starting
off with a poller on http://hg.mozilla.org/, which is ported over from
master-ball.


Hg Poller
---------

The hg poller is based on `twisted` (13.0.0 at this point). It's feeding
`hg-push` events into the `hg` queue. These events have the following
structure:

```json
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
```

<h1 id="workers" class="well">Workers</h1>

Workers may be singletons or parallelized tasks. Singletons are mere
`kombu` workers with `Consumer`s, whereas parallized tasks are
implemented on top of `celery`.

Mercurial
---------

The mercurial worker listens to the `hg-push` messages on the `hg`
queue. It pulls local clones and updates the elmo database by
forwarding the data from the message on to 'elmo's
`pushes.utils.handlePushes`.

The worker implements a simple error recovery, and retries on failures
inside `handlePushes`, for `autosettings.MAX_HG_RETRIES` tries. If
configured, it forwards the failures to a sentry installation.
