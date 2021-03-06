##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Sources for IContentTypeInterface providers and codecs.

"""
__docformat__ = "reStructuredText"

import sys

import zope.app.form.browser.interfaces
import zope.component
import zope.mimetype.interfaces
import zope.publisher.interfaces.browser


# Base classes

class UtilitySource(object):
    """Source of utilities providing a specific interface."""

    def __init__(self):
        self._length = None

    def __contains__(self, value):
        ok = self._interface.providedBy(value)
        if ok:
            for name, interface in zope.component.getUtilitiesFor(
                self._interface):
                if interface is value:
                    return True
        return False

    def __iter__(self):
        length = 0
        seen = set()

        # haven't been iterated over all the way yet, go ahead and
        # build the cached results list
        for name, interface in zope.component.getUtilitiesFor(
            self._interface):
            if interface not in seen:
                seen.add(interface)
                yield interface
        self._length = length

    def __len__(self):
        if self._length is None:
            self._length = len(list(iter(self)))
        return self._length


class Terms(object):
    """Utility to provide terms for content type interfaces."""

    zope.interface.implements(
        zope.app.form.browser.interfaces.ITerms)

    def __init__(self, source, request):
        self.context = source
        self.request = request

    def getTerm(self, value):
        if value in self.context:
            return self._createTerm(value)
        raise LookupError("value is not an element in the source")


# Source & vocabulary for `IContentTypeInterface` providers

class ContentTypeSource(UtilitySource):
    """Source of IContentTypeInterface providers."""

    zope.interface.implements(
        zope.mimetype.interfaces.IContentTypeSource)

    _interface = zope.mimetype.interfaces.IContentTypeInterface


class ContentTypeTerms(Terms):
    """Utility to provide terms for content type interfaces."""

    zope.component.adapts(
        zope.mimetype.interfaces.IContentTypeSource,
        zope.publisher.interfaces.browser.IBrowserRequest)

    def getValue(self, token):
        module, name = token.rsplit(".", 1)
        if module not in sys.modules:
            try:
                __import__(module)
            except ImportError:
                raise LookupError("could not import module for token")
        interface = getattr(sys.modules[module], name)
        if interface in self.context:
            return interface
        raise LookupError("token does not represent an element in the source")

    def _createTerm(self, value):
        return ContentTypeTerm(value)


class ContentTypeTerm(object):

    zope.interface.implements(
        zope.mimetype.interfaces.IContentTypeTerm)

    def __init__(self, interface):
        self.value = interface

    @property
    def token(self):
        return "%s.%s" % (self.value.__module__, self.value.__name__)

    @property
    def title(self):
        return self.value.getTaggedValue("title")

    @property
    def mimeTypes(self):
        return self.value.getTaggedValue("mimeTypes")

    @property
    def extensions(self):
        return self.value.getTaggedValue("extensions")


contentTypeSource = ContentTypeSource()


# Source & vocabulary for `IContentTypeInterface` providers

class CodecSource(UtilitySource):
    """Source of ICodec providers."""

    zope.interface.implements(
        zope.mimetype.interfaces.ICodecSource)

    _interface = zope.mimetype.interfaces.ICodec


class CodecTerms(Terms):
    """Utility to provide terms for codecs."""

    zope.component.adapts(
        zope.mimetype.interfaces.ICodecSource,
        zope.publisher.interfaces.browser.IBrowserRequest)

    def getValue(self, token):
        codec = zope.component.queryUtility(
            zope.mimetype.interfaces.ICodec, token)
        if codec is None:
            raise LookupError("no matching code: %r" % token)
        if codec not in self.context:
            raise LookupError("codec not in source: %r" % token)
        return codec

    def _createTerm(self, value):
        return CodecTerm(value)


class CodecTerm(object):
    zope.interface.implements(
        zope.mimetype.interfaces.ICodecTerm)

    def __init__(self, codec):
        self.value = codec

    @property
    def token(self):
        return self.value.name

    @property
    def title(self):
        return self.value.title

    @property
    def preferredCharset(self):
        charset = zope.component.queryUtility(
            zope.mimetype.interfaces.ICodecPreferredCharset,
            name=self.value.name)
        if codec is None:
            available = [(name, charset)
                         for (charset, name) in zope.component.getUtilitiesFor(
                             zope.mimetype.interfaces.ICharset)
                         if charset.encoding == self.value.name]
            if not available:
                # no charsets are available; should not happen in practice
                return None
            # no charset marked preferred; pick one
            available.sort()
            charset = available[0][1]
        return charset.name


codecSource = CodecSource()
