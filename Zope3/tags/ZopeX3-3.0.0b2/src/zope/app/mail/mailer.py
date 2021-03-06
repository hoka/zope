##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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

"""These are classes which abstract different channels an email
message could be sent out by.

$Id$
"""
from os import popen
from smtplib import SMTP

from zope.interface import implements
from zope.app.mail.interfaces import ISendmailMailer, ISMTPMailer


class SendmailMailer(object):

    implements(ISendmailMailer)

    # A hook for unit tests
    popen = popen

    def __init__(self, command="/usr/lib/sendmail -oem -oi -f %(from)s %(to)s"):
        self.command = command

    def send(self, fromaddr, toaddrs, message):
        command = self.command % {'from': fromaddr, 'to': " ".join(toaddrs)}
        f = self.popen(command, "w")
        f.write(message)
        f.close()

class SMTPMailer(object):

    implements(ISMTPMailer)

    smtp = SMTP

    def __init__(self, hostname='localhost', port=25,
                 username=None, password=None):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password

    def send(self, fromaddr, toaddrs, message):
        connection = self.smtp(self.hostname, str(self.port))
        if self.username is not None and self.password is not None:
            connection.login(self.username, self.password)
        connection.sendmail(fromaddr, toaddrs, message)
        connection.quit()
