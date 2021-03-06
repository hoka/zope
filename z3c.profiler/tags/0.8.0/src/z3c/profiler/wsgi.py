##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id: __init__.py 72087 2007-01-18 01:03:33Z rogerineichen $
"""

import time
import profile
import pstats
from threading import RLock

from zope.app.wsgi import WSGIPublisherApplication

_lock = RLock()
_calls = 1
_stats = {}


def monkey_call(self, environ, start_response):
    if (environ.get('HTTP_REFERER', '').endswith('doProfile') or
        environ.get('REQUEST_URI', '').endswith('doProfile')):
        return orig_call(self, environ, start_response)

    prof = profile.Profile(time.time)
    response = prof.runcall(orig_call, self, environ, start_response)
    
    lock= _lock

    lock.acquire()
    try:
        global _stats

        uri = environ.get('REQUEST_URI', '')
        
        if _stats.has_key(uri):
            _stats[uri][0].add(prof)
            _stats[uri][2] = _stats[uri][2] + 1
        else:
            _stats[uri] = ([pstats.Stats(prof), environ, 1])
    finally:
        global _calls
        if _calls > 0:
            _calls = _calls - 1

        if _calls <= 0:
            WSGIPublisherApplication.__call__ = orig_call

        lock.release()

    return response


orig_call = WSGIPublisherApplication.__call__


def getStats():
    return _stats


def listStats():
    stats = []
    for uri, info in getStats().items():
        stats.append({'uri': uri, 'calls': info[2]})
    return stats


def installProfiler(calls):
    global _calls, _stats

    _calls = calls
    _stats = {}

    WSGIPublisherApplication.__call__ = monkey_call


def uninstallProfiler(calls):
    WSGIPublisherApplication.__call__ = orig_call
