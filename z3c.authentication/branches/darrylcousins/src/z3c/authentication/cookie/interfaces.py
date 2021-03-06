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
$Id$
"""
__docformat__ = "reStructuredText"

import zope.interface
import zope.schema
from zope.session.interfaces import ISessionDataContainer
from zope.session.interfaces import ISession
from zope.session.interfaces import IClientId
from zope.app.authentication import interfaces
from zope.app.authentication import session

from z3c.i18n import MessageFactory as _

SESSION_KEY = 'z3c.authentication.cookie.ICookieCredentialSessionDataContainer'

# The BROWSER_SESSION_KEY is a optional session key on which you can register 
# a own ISessionDataContainer, if there is no such named utility, the default 
# unnamed ISessionDataContainer is used. This fallback pattern is provided in
# ISession._sdc
BROWSER_SESSION_KEY = 'z3c.authentication.cookie.IBrowserSession-DataContainer'


class ILifeTimeClientId(IClientId):
    """Life time session client id."""


class ILifeTimeSession(ISession):
    """Session valid over a long time.
    
    Note this session requires a IClientIdManager configured with a 
    ``cookieLifetime = 0`` registered as a named utility with a 
    ``name = LifeTimeSessionClientIdManager``.
    """


class ICookieCredentialSessionDataContainer(ISessionDataContainer):
    """A persistent cookie credential container."""

    timeout = zope.schema.Int(
            title=_(u"Timeout"),
            description=_(
                "Number of seconds before session data becomes stale and may "
                "be removed. A value of '0' means no expiration."),
            default=0,
            required=True,
            min=0,
            )


class ICookieCredentialsPlugin(interfaces.ICredentialsPlugin, 
    session.IBrowserFormChallenger):
    """A cookie credential plugin."""


class ICookieCredentials(zope.interface.Interface):
    """ Interface for storing and accessing credentials in a session.

        We use a real class with interface here to prevent unauthorized
        access to the credentials.
    """

    def __init__(login, password):
        pass

    def getLogin():
        """Return login name."""

    def getPassword():
        """Return password."""

    autologin = zope.schema.Bool(
        title=u'Autologin',
        description=u"Auto login via cookie if set to true.",
        default=False)
