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
""" Generic three dimensional array type """

from Zope.App.Security.Grants.ILocalSecurityMap import ILocalSecurityMap

class LocalSecurityMap(object):

    __implements__ = ILocalSecurityMap

    def __init__(self):
        self._clear()

    def _clear(self):
        self._byrow = {}
        self._bycol = {}

    def addCell(self, rowentry, colentry, value):
        row = self._byrow.setdefault(rowentry, {})
        row[colentry] = value

        col = self._bycol.setdefault(colentry, {})
        col[rowentry] = value

    def delCell(self, rowentry, colentry):
        row = self._byrow.get(rowentry)
        if row and (colentry in row):
            del self._byrow[rowentry][colentry]
            del self._bycol[colentry][rowentry]

    def getCell(self, rowentry, colentry, default=None):
        " return the value of a cell by row, entry "
        row = self._byrow.get(rowentry)
        if row: return row.get(colentry, default)
        else: return default

    def getRow(self, rowentry):
        " return a list of (colentry, value) tuples from a row "
        row = self._byrow.get(rowentry)
        if row:
            return row.items()
        else: return []

    def getCol(self, colentry):
        " return a list of (rowentry, value) tuples from a col "
        col = self._bycol.get(colentry)
        if col:
            return col.items()
        else: return []

    def getAllCells(self):
        " return a list of (rowentry, colentry, value) "
        res = []
        for r in self._byrow.keys():
            for c in self._byrow[r].items():
                res.append((r,) + c)
        return res
