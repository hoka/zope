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

$Id: File.py,v 1.7 2002/07/24 23:15:46 jeremy Exp $
"""
from types import StringType, UnicodeType, NoneType

from Persistence import Persistent
from Transaction import get_transaction

from Zope.App.OFS.Content.File.FileChunk import FileChunk
from Zope.App.OFS.Content.File.IFile import IFile
from Zope.Publisher.Browser.BrowserRequest import FileUpload

from Zope.App.OFS.Annotation.IAnnotatable import IAnnotatable
from Zope.App.OFS.Content.File.SFile import SFile
from Zope.App.OFS.Content.File.IFile import IFile

# set the size of the chunks
MAXCHUNKSIZE = 1 << 16

class File(Persistent):
    __implements__ = SFile, IFile, IAnnotatable

    def __init__(self, data='', contentType=''):
        self.data = data
        self.contentType = contentType


    def __len__(self):
        return self.size


    def setContentType(self, contentType):
        '''See interface Zope.App.OFS.Content.File.IFile.IFile'''
        self._contentType = contentType

        
    def getContentType(self):
        '''See interface Zope.App.OFS.Content.File.IFile.IFile'''
        return self._contentType

        
    def edit(self, data, contentType=None):
        '''See interface Zope.App.OFS.Content.File.IFile.IFile'''
        # XXX This seems broken to me, as setData can override the
        # content type explicitly passed in.
        
        if contentType is not None:
            self._contentType = contentType
        if hasattr(data, '__class__') and data.__class__ is FileUpload \
           and not data.filename:
           data = None          # Ignore empty files
        if data is not None:
            self.data = data


    def getData(self):
        '''See interface Zope.App.OFS.Content.File.IFile.IFile'''
        if hasattr(self._data, '__class__') and \
           self._data.__class__ is FileChunk:
            return str(self._data)
        else:
            return self._data


    def setData(self, data):
        '''See interface Zope.App.OFS.Content.File.IFile.IFile'''
        # Handle case when data is a string
        if isinstance(data, UnicodeType):
            data = data.encode('UTF-8')

        if isinstance(data, StringType):
            size = len(data)
            if size < MAXCHUNKSIZE:
                self._data, self._size = FileChunk(data), size
                return None
            self._data, self._size = FileChunk(data), size
            return None

        # Handle case when data is None
        if isinstance(data, NoneType):
            self._data, self._size = None, 0
            return None

        # Handle case when data is already a FileChunk
        if hasattr(data, '__class__') and data.__class__ is FileChunk:
            size = len(data)
            self._data, self._size = data, size
            return None

        # Handle case when data is a file object
        seek = data.seek
        read = data.read
        
        seek(0, 2)
        size = end = data.tell()

        if size <= 2*MAXCHUNKSIZE:
            seek(0)
            if size < MAXCHUNKSIZE:
                self._data, self._size = read(size), size
                return None
            self._data, self._size = FileChunk(read(size)), size
            return None

        # Make sure we have an _p_jar, even if we are a new object, by
        # doing a sub-transaction commit.
        get_transaction().savepoint()
        
        jar = self._p_jar
        
        if jar is None:
            # Ugh
            seek(0)
            self._data, self._size = FileChunk(read(size)), size
            return None

        # Now we're going to build a linked list from back
        # to front to minimize the number of database updates
        # and to allow us to get things out of memory as soon as
        # possible.
        next = None
        while end > 0:
            pos = end - MAXCHUNKSIZE
            if pos < MAXCHUNKSIZE:
                pos = 0 # we always want at least MAXCHUNKSIZE bytes
            seek(pos)
            data = FileChunk(read(end - pos))
            
            # Woooop Woooop Woooop! This is a trick.
            # We stuff the data directly into our jar to reduce the
            # number of updates necessary.
            data._p_jar = jar

            # This is needed and has side benefit of getting
            # the thing registered:
            data.next = next
            
            # Now make it get saved in a sub-transaction!
            get_transaction().savepoint()

            # Now make it a ghost to free the memory.  We
            # don't need it anymore!
            data._p_changed = None
            
            next = data
            end = pos
        
        self._data, self._size = next, size
        return None


    def getSize(self):
        '''See interface Zope.App.OFS.Content.File.IFile.IFile'''
        return self._size


    # See schema Zope.App.OFS.File.SFile.SFile
    data = property(getData, setData, None,
                    """Contains the data of the file.""")

    contentType = property(getContentType, setContentType, None,
                           """Specifies the content type of the data.""")

    size = property(getSize, None, None,
                    """Specifies the size of the file in bytes. Read only.""")
