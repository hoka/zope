#
# This file is necessary to make this directory a package.


# XXX There's a circular import problem with the proxy package.
# The proxy framework needs some refactoring, but not today.
import zope.proxy

from zope.security.checker import CheckerPublic as _CheckerPublic
from zope.security.management import getSecurityManager as _getSecurityManager

def checkPermission(permission, object, interaction=None):
    """Return whether security policy allows permission on object.

    Arguments:
    permission -- A permission name
    object -- The object being accessed according to the permission
    interaction -- An interaction, which provides access to information
        such as authenticated principals.  If it is None, the current
        interaction is used.

    checkPermission is guaranteed to return True if permission is
    CheckerPublic or None.
    """
    if permission is None or permission is _CheckerPublic:
        return True
    if interaction is not None:
        # XXX: transition from contexts to interactions is not complete
        raise NotImplementedError
    sm = _getSecurityManager()
    return sm.checkPermission(permission, object)

