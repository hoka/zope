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
"""This module tests the Gettext Export and Import funciotnality of the
Translation Service.

$Id: testGettextExportImport.py,v 1.2 2002/10/04 18:37:23 jim Exp $
"""
import unittest, time

from cStringIO import StringIO

from Zope.App.tests.PlacelessSetup import PlacelessSetup
from Zope.App.ComponentArchitecture.metaConfigure import \
     provideService, managerHandler
from Zope.App.ComponentArchitecture.metaConfigure import handler

from Zope.App.OFS.Services.TranslationService.MessageCatalog import \
     MessageCatalog 
from Zope.I18n.Negotiator import negotiator
from Zope.I18n.INegotiator import INegotiator
from Zope.I18n.IUserPreferredLanguages import IUserPreferredLanguages

from Zope.App.OFS.Services.TranslationService.TranslationService import \
     TranslationService
from Zope.App.OFS.Services.TranslationService.GettextImportFilter import \
     GettextImportFilter
from Zope.App.OFS.Services.TranslationService.GettextExportFilter import \
     GettextExportFilter



class Environment:

    __implements__ = IUserPreferredLanguages

    def __init__(self, langs=()):
        self.langs = langs

    def getPreferredLanguages(self):
        return self.langs


class TestGettextExportImport(PlacelessSetup, unittest.TestCase):


    _data = '''msgid ""
msgstr ""
"Project-Id-Version: Zope 3\\n"
"PO-Revision-Date: %s\\n"
"Last-Translator: Zope 3 Gettext Export Filter\\n"
"Zope-Language: de\\n"
"Zope-Domain: default\\n" 
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

msgid "Choose"
msgstr "Ausw\xc3\xa4hlen!"

msgid "greeting"
msgstr "hallo"
'''

    def setUp(self):
        PlacelessSetup.setUp(self)
        # Setup the negotiator service registry entry
        managerHandler('defineService', 'LanguageNegotiation', INegotiator) 
        provideService('LanguageNegotiation', negotiator, 'Zope.Public')
        self._service = TranslationService('default') 
        handler('Factories', 'provideFactory', 'Message Catalog',
                MessageCatalog)


    def testImportExport(self):
        service = self._service

        imp = GettextImportFilter(service)
        imp.importMessages(['default'], ['de'],
                           StringIO(self._data %'2002/02/02 02:02'))

        exp = GettextExportFilter(service)
        result = exp.exportMessages(['default'], ['de'])
        
        dt = time.time()
        dt = time.localtime(dt)
        dt = time.strftime('%Y/%m/%d %H:%M', dt)

        self.assertEqual(result.strip(), (self._data %dt).strip())


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestGettextExportImport)


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())

