##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""/etc/passwd Authentication Plugin

This package defines a new authentication plugin, which can use textfiles to
authenticate users.

$Id: __init__.py,v 1.1 2004/02/15 03:21:05 srichter Exp $
"""
import os
from persistence import Persistent
from zope.app.container.contained import Contained
from zope.app.location import locate
from zope.app.services.pluggableauth import SimplePrincipal
from zope.app.interfaces.services.pluggableauth import \
     ILoginPasswordPrincipalSource
from zope.exceptions import NotFoundError
from zope.interface import implements
from interfaces import IFileBasedPrincipalSource

class PasswdPrincipalSource(Contained, Persistent):
    """A Principal Source for /etc/passwd-like files."""

    implements(ILoginPasswordPrincipalSource, IFileBasedPrincipalSource)

    def __init__(self, filename=''):
        self.filename = filename

    def readPrincipals(self):
        if not os.path.exists(self.filename):
            return []
        file = open(self.filename, 'r')
        principals = []
        for line in file.readlines():
            if line.strip() != '':
                user_info = line.strip().split(':', 3)
                p = SimplePrincipal(*user_info)
                locate(p, self, p.id)
                p.id = p.login
                principals.append(p)
        return principals

    def getPrincipal(self, id):
        """See IPrincipalSource."""
        earmark, source_name, id = id.split('\t')
        for p in self.readPrincipals():
            if p.id == id:
                return p
        raise NotFoundError, id

    def getPrincipals(self, name):
        """See IPrincipalSource."""
        return filter(lambda p: p.login.find(name) != -1,
                      self.readPrincipals())

    def authenticate(self, login, password):
        """See ILoginPasswordPrincipalSource. """
        for user in self.readPrincipals():
            if user.login == login and user.password == password:
                return user
