##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
$Id: ntests.py 3330 2005-09-09 23:05:34Z jim $
"""
from StringIO import StringIO
from zc.resourcelibrary import publication
from zc.resourcelibrary import tal
from zope.app.testing import functional
from zope.configuration import xmlconfig
from zope.pagetemplate import pagetemplate
import doctest
import os
import unittest
import zope.security.management

#### testing framework ####

def zcml(s, execute=True):
    from zope.app.appsetup.appsetup import __config_context as context
    try:
        xmlconfig.string(s, context, execute=execute)
    except:
        context.end()
        raise


class TestPageTemplate(pagetemplate.PageTemplate):
    def __init__(self, view):
        self.view = view
        super(TestPageTemplate, self).__init__()

    def pt_getContext(self, *args, **kws):
        context = super(TestPageTemplate, self).pt_getContext(*args, **kws)
        context['view'] = self.view
        return context


def zpt(s, view=None, content_type=None):
    request = publication.Request(body_instream=StringIO(''), environ={})
    zope.security.management.newInteraction(request)
    pt = TestPageTemplate(view)

    # if the resource library expression hasn't been registered, do so
    engine = pt.pt_getEngine()
    type_name = 'resource_library'
    if type_name not in engine.types:
        engine.registerType(type_name, tal.ResourceLibraryExpression)

    pt.write(s)
    html = pt()
    zope.security.management.endInteraction()

    if content_type:
        request.response.setHeader("Content-Type", content_type)

    if html:
        request.response.setResult(html)
        return request.response.consumeBody()

#### test setup ####

ResourceLibraryFunctionalLayer = functional.ZCMLLayer(
    os.path.join(os.path.split(__file__)[0], 'ftesting.zcml'),
    __name__, 'ResourceLibraryFunctionalLayer')

def test_suite():
    suite = functional.FunctionalDocFileSuite(
        '../README.txt',
        globs={'zcml': zcml, 'zpt': zpt},
        optionflags=doctest.NORMALIZE_WHITESPACE+doctest.ELLIPSIS,
        )
    suite.layer = ResourceLibraryFunctionalLayer
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
