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
from Interface import Interface
from Interface.Common.Mapping import IEnumerableMapping

class IReadContainer(IEnumerableMapping):
    """Readable content containers

       For all methods that return a sequence of values, the return
       value is guaranteed to support the read-only semantics of a
       Python sequence (indexing, slicing, len). The return value is
       not, however, required to be an actual native sequence type
       (list or tuple).

       Note that the IReadContainer interface implies a collection of
       objects that are exposed via various publishing mechanisms.
       Collections of object that *do not* want to be traversed should
       not implement this.

       """

class IWriteContainer(Interface):
    """An interface for the write aspects of a container."""

    def setObject(key, object):
        """Add the given object to the container under the given key.

        Raises a ValueError if key is an empty string.

        Returns the key used, which might be different than the given key
        """

    def __delitem__(key):
        """Delete the keyd object from the container.

        Raises a KeyError if the object is not found.

        """

class IContainer(IReadContainer, IWriteContainer):
    """Readable and writable content container."""

class IHomogenousContainer(Interface):

    # XXX this needs to be rethought a bit.
    def isAddable(interfaces):
        """Test for interface compatability for container and factory

        Tells you whether something that implements the given
        interfaces may be added to this container.

        The argument may be a single interface, a tuple of interfaces,
        or None, if the thing you're considering adding declares no
        interfaces.

        Returns a true value if an object that implements absolutely all
        of the given interfaces may be added to this container.
        Otherwise, returns false."""

