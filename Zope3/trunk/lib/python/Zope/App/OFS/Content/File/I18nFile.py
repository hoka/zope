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

$Id: I18nFile.py,v 1.4 2002/11/11 18:24:47 jim Exp $
"""

import Persistence
from IFile import IFile
from Zope.I18n.II18nAware import II18nAware
from File import File
from Zope.Publisher.Browser.BrowserRequest import FileUpload


class II18nFile(IFile, II18nAware):
    """I18n aware file interface."""

    def removeLanguage(language):
        '''Remove translated content for a given language.'''


class I18nFile(Persistence.Persistent):
    """I18n aware file object.  It contains a number of File objects --
    one for each language.
    """

    __implements__ = II18nFile

    def __init__(self, data='', contentType=None, defaultLanguage='en'):
        """ """

        self._data = {}
        self.defaultLanguage = defaultLanguage
        self.setData(data, language=defaultLanguage)

        if contentType is None:
            self.setContentType('')
        else:
            self.setContentType(contentType)


    def __len__(self):
        return self.getSize()


    def _create(self, data):
        """Create a new subobject of the appropriate type.  Should be
        overriden in subclasses.
        """
        return File(data)


    def _get(self, language):
        """Helper function -- return a subobject for a given language,
        and if it does not exist, return a subobject for the default
        language.
        """
        file = self._data.get(language)
        if not file:
            file = self._data[self.defaultLanguage]
        return file


    def _get_or_add(self, language, data=''):
        """Helper function -- return a subobject for a given language,
        and if it does not exist, create and return a new subobject.
        """
        if language is None:
            language = self.defaultLanguage
        file = self._data.get(language)
        if not file:
            self._data[language] = file = self._create(data)
            self._p_changed = 1
        return file


    ############################################################
    # Implementation methods for interface
    # Zope.App.OFS.IFile.IFile

    def setContentType(self, contentType):
        '''See interface IFile'''
        self._contentType = contentType


    def getContentType(self):
        '''See interface IFile'''
        return self._contentType


    contentType = property(getContentType, setContentType)

    def edit(self, data, contentType=None, language=None):
        '''See interface IFile'''

        # XXX This seems broken to me, as setData can override the
        # content type explicitly passed in.

        if contentType is not None:
            self.setContentType(contentType)
        if hasattr(data, '__class__') and data.__class__ is FileUpload \
           and not data.filename:
           data = None          # Ignore empty files
        if data is not None:
            self.setData(data, language)


    def getData(self, language=None):
        '''See interface IFile'''
        return self._get(language).getData()


    def setData(self, data, language=None):
        '''See interface IFile'''
        self._get_or_add(language).setData(data)

    data = property(getData, setData)

    def getSize(self, language=None):
        '''See interface IFile'''
        return self._get(language).getSize()

    #
    ############################################################

    ############################################################
    # Implementation methods for interface
    # II18nAware.py

    def getDefaultLanguage(self):
        'See Zope.I18n.II18nAware.II18nAware'
        return self.defaultLanguage

    def setDefaultLanguage(self, language):
        'See Zope.I18n.II18nAware.II18nAware'
        if not self._data.has_key(language):
            raise ValueError, \
                  'cannot set nonexistent language (%s) as default' % language
        self.defaultLanguage = language

    def getAvailableLanguages(self):
        'See Zope.I18n.II18nAware.II18nAware'
        return self._data.keys()

    #
    ############################################################


    ############################################################
    # Implementation methods for interface
    # II18nFile.py
    def removeLanguage(self, language):
        '''See interface II18nFile'''

        if language == self.defaultLanguage:
            raise ValueError, 'cannot remove default language (%s)' % language
        if self._data.has_key(language):
            del self._data[language]
            self._p_changed = 1


