# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import
from kombu import Exchange, Queue

hg_exchange = Exchange('hg', type='direct')
hg_queues = [Queue('hg', hg_exchange, routing_key='hg')]
