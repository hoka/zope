##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id: CommonHitLogger.py,v 1.2 2002/06/10 23:29:35 jim Exp $
"""

import time
import sys

from http_date import monthname
from Zope.Server.Logger.FileLogger import FileLogger
from Zope.Server.Logger.ResolvingLogger import ResolvingLogger
from Zope.Server.Logger.UnresolvingLogger import UnresolvingLogger


class CommonHitLogger:
    """Outputs hits in common HTTP log format.
    """

    def __init__(self, logger_object=None, resolver=None):
        if logger_object is None:
            logger_object = FileLogger(sys.stdout)

        if resolver is not None:
            self.output = ResolvingLogger(resolver, logger_object)
        else:
            self.output = UnresolvingLogger(logger_object)

    def compute_timezone_for_log(self, tz):
        if tz > 0:
            neg = 1
        else:
            neg = 0
            tz = -tz
        h, rem = divmod (tz, 3600)
        m, rem = divmod (rem, 60)
        if neg:
            return '-%02d%02d' % (h, m)
        else:
            return '+%02d%02d' % (h, m)

    tz_for_log = None
    tz_for_log_alt = None

    def log_date_string(self, when):
        logtime = time.localtime(when)
        Y, M, D, h, m, s = logtime[:6]

        if not time.daylight:
            tz = self.tz_for_log
            if tz is None:
                tz = self.compute_timezone_for_log(time.timezone)
                self.tz_for_log = tz
        else:
            tz = self.tz_for_log_alt
            if tz is None:
                tz = self.compute_timezone_for_log(time.altzone)
                self.tz_for_log_alt = tz

        return '%d/%s/%02d:%02d:%02d:%02d %s' % (
            Y, monthname[M], D, h, m, s, tz)


    def log(self, task):
        """
        Receives a completed task and logs it in the
        common log format.
        """
        now = time.time()
        request_data = task.request_data
        req_headers = request_data.headers

        user_name = task.auth_user_name or 'anonymous'
        user_agent = req_headers.get('USER_AGENT', '')
        referer = req_headers.get('REFERER', '')

        self.output.log(
            task.channel.addr[0],
            ' - %s [%s] "%s" %s %d "%s" "%s"\n' % (
                user_name,
                self.log_date_string(now),
                request_data.first_line,
                task.status,
                task.bytes_written,
                referer,
                user_agent
                )
            )

