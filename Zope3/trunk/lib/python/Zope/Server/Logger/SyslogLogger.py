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

$Id: SyslogLogger.py,v 1.2 2002/06/10 23:29:36 jim Exp $
"""

import os
import m_syslog

from ILogger import ILogger


class SyslogLogger(m_syslog.syslog_client):
    """syslog is a line-oriented log protocol - this class would be
       appropriate for FTP or HTTP logs, but not for dumping stderr
       to.

       XXX: a simple safety wrapper that will ensure that the line
       sent to syslog is reasonable.

       XXX: async version of syslog_client: now, log entries use
       blocking send()
    """

    __implements__ = ILogger

    svc_name = 'zope'
    pid_str  = str(os.getpid())

    def __init__ (self, address, facility='user'):
        m_syslog.syslog_client.__init__ (self, address)
        self.facility = m_syslog.facility_names[facility]
        self.address=address


    def __repr__ (self):
        return '<syslog logger address=%s>' % (repr(self.address))


    ############################################################
    # Implementation methods for interface
    # Zope.Server.Logger.ILogger

    def log(self, message):
        'See Zope.Server.Logger.ILogger.ILogger'
        m_syslog.syslog_client.log (
            self,
            '%s[%s]: %s' % (self.svc_name, self.pid_str, message),
            facility=self.facility,
            priority=m_syslog.LOG_INFO
            )

    #
    ############################################################
