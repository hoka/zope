#############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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

$Id: date.py 2041 2005-06-16 18:34:44Z fred $
"""

import datetime
import pytz
from zope.interface.common.idatetime import ITZInfo

def now(request):
    return datetime.datetime.now(ITZInfo(request))

def format(request, dt=None):
    if dt is None:
        dt = now(request)
    formatter = request.locale.dates.getFormatter(
        'dateTime', 'medium')
    return formatter.format(dt)

def normalize(request, dt):

    """this method normalizes datetime instances by converting them to
    utc, daylight saving times are also taken into account. This
    method requires an adapter to get the tzinfo from the request.

    >>> from zope import component, interface
    >>> import pytz
    >>> from zope.interface.common.idatetime import ITZInfo
    >>> from zope.publisher.interfaces.browser import IBrowserRequest
    >>> from zope.publisher.browser import TestRequest
    >>> @interface.implementer(ITZInfo)
    ... @component.adapter(IBrowserRequest)
    ... def tzinfo(request):
    ...     return pytz.timezone('Europe/Vienna')
    >>> component.provideAdapter(tzinfo)
    >>> dt = datetime.datetime(2006,5,1,12)
    >>> request = TestRequest()

    The Vienna timezone has a 2 hour offset to utc at this date.
    >>> normalize(request,dt)
    datetime.datetime(2006, 5, 1, 10, 0, tzinfo=<UTC>)

    At this date the timezone has only a one hour offset.
    >>> dt = datetime.datetime(2006,2,1,12)    
    >>> normalize(request,dt)
    datetime.datetime(2006, 2, 1, 11, 0, tzinfo=<UTC>)
    """

    
    if dt.tzinfo is None:
        tzinfo = ITZInfo(request)
    else:
        tzinfo = dt.tzinfo
        
    # we have to do this because, pytz does currently not take the
    # datetime argument into account in its dst() and utcoffset()
    # methods
    
    tzu = tzinfo.fromutc(dt).tzinfo
    dt = dt.replace(tzinfo=tzu)
    return dt.astimezone(pytz.utc)
