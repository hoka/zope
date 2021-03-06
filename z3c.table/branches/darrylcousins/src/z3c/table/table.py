##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
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
$Id:$
"""
__docformat__ = "reStructuredText"

from xml.sax.saxutils import quoteattr

import zope.interface
import zope.component
import zope.location

from z3c.batching.interfaces import IBatch
from z3c.batching.batch import Batch
from z3c.table import interfaces
from z3c.table import column


def getWeight(column):
    try:
        return int(column.weight)
    except AttributeError:
        return 0


def getSortMethod(idx):
    def getSortKey(item):
        sublist = item[idx]
        def getCloumnSortKey(sublist):
            return sublist[1].getSortKey(sublist[0])
        return getCloumnSortKey(sublist)
    return getSortKey


def nameColumn(column, name):
    """Give a column a __name__."""
    column.__name__ = name
    return column


class Table(zope.location.Location):
    """Generic usable table implementation."""

    zope.interface.implements(interfaces.ITable)

    # private variables will be set in update call
    batchProvider = None
    columnCounter = 0
    columnIndexById = {}
    columnByName = {}
    columns = None
    rows = None
    selectedItems = []

    # customize this part if needed
    prefix = 'table'

    # css classes
    cssClasses = {}
    # additional (row) css
    cssClassEven = u''
    cssClassOdd = u''
    cssClassSelected = u''

    # sort attributes
    sortOn = 0
    sortOrder = u'ascending'
    reverseSortOrderNames = [u'descending', u'reverse', u'down']

    # batch attributes
    batchProviderName = 'batch'
    batchStart = 0
    batchSize = 50
    startBatchingAt = 50

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.__parent__ = context

    def getCSSClass(self, element, cssClass=None):
        klass = self.cssClasses.get(element)
        if klass and cssClass:
            klass = '%s %s' % (cssClass, klass)
        elif cssClass:
            klass = cssClass
        return klass and ' class=%s' % quoteattr(klass) or ''

    @property
    def values(self):
        return self.context.values()

# setup

    def setUpColumns(self):
        cols = list(zope.component.getAdapters((self.context, self.request, self),
            interfaces.IColumn))
        # use the adapter name as column name
        return [nameColumn(col, name) for name, col in cols]

    def updateColumns(self):
        for col in self.columns:
            col.update()

    def orderColumns(self):
        self.columns = sorted(self.columns, key=getWeight)
        for col in self.columns:
            self.columnByName[col.__name__] = col
            idx = self.columnCounter
            col.id = '%s-%s-%s' % (self.prefix, col.__name__, idx)
            self.columnIndexById[col.id] = idx
            self.columnCounter += 1

    def setUpRow(self, item):
        cols = []
        append = cols.append
        colspanCounter = 0
        countdown = len(self.columns)
        counter = 0
        for col in self.columns:
            countdown -= 1
            colspan = 0
            if colspanCounter == 0:
                colspan = colspanCounter = col.getColspan(item)
                # adjust colspan because we define 0, 2, 3, etc.
                if colspanCounter > 0:
                    colspanCounter -=1

            if colspan == 0 and colspanCounter > 0:
                # override col if colspan is 0 and colspan coutner not 0
                colspanCounter -=1
                colspan = 0
                # now we are ready to setup dummy colspan cells
                col = column.NoneCell(self.context, self.request, self)

            # we reached the end of the table and have still colspan
            if (countdown - colspan) < 0:
                raise ValueError(
                    "Colspan for column '%s' larger then table." % col)

            append((item, col, colspan))
        return cols

    def setUpRows(self):
        return [self.setUpRow(item) for item in self.values]

# sort

    def getSortOn(self):
        """Returns sort on column id."""
        return self.request.get(self.prefix +'-sortOn', self.sortOn)

    def getSortOrder(self):
        """Returns sort order criteria."""
        return self.request.get(self.prefix +'-sortOrder',
            self.sortOrder)

    def sortRows(self):
        if self.sortOn is not None and self.rows and self.columns:
            sortOnIdx = self.columnIndexById.get(self.sortOn, 0)
            sortKeyGetter = getSortMethod(sortOnIdx)
            rows = sorted(self.rows, key=sortKeyGetter)
            if self.sortOrder in self.reverseSortOrderNames:
                rows.reverse()
            self.rows = rows

# batch

    def getBatchSize(self):
        return int(self.request.get(self.prefix +'-batchSize',
            self.batchSize))

    def getBatchStart(self):
        return int(self.request.get(self.prefix +'-batchStart',
            self.batchStart))

    def batchRows(self):
        if len(self.rows) > self.startBatchingAt:
            self.rows = Batch(self.rows, start=self.batchStart,
                size=self.batchSize)

    def updateBatch(self):
        if IBatch.providedBy(self.rows):
            self.batchProvider = zope.component.getMultiAdapter((self.context,
                self.request, self), interfaces.IBatchProvider,
                name=self.batchProviderName)
            self.batchProvider.update()

    def isSelectedRow(self, row):
        item, col, colspan = row[0]
        if item in self.selectedItems:
            return True
        return False

# render

    def renderBatch(self):
        if self.batchProvider is None:
            return u''
        return self.batchProvider.render()

    def renderTable(self):
        if self.columns:
            cssClass = self.getCSSClass('table')
            head = self.renderHead()
            body = self.renderBody()
            return '<table%s>%s%s\n</table>' % (cssClass, head, body)
        return u''

    def renderHead(self):
        cssClass = self.getCSSClass('thead')
        rStr = self.renderHeadRow()
        return '\n  <thead%s>%s\n  </thead>' % (cssClass, rStr)

    def renderHeadRow(self):
        cssClass = self.getCSSClass('tr')
        cells = [self.renderHeadCell(col) for col in self.columns]
        return u'\n    <tr%s>%s\n    </tr>' % (cssClass, u''.join(cells))

    def renderHeadCell(self, column):
        cssClass = column.cssClasses.get('th')
        cssClass = self.getCSSClass('th', cssClass)
        return u'\n      <th%s>%s</th>' % (cssClass, column.renderHeadCell())

    def renderBody(self):
        cssClass = self.getCSSClass('tbody')
        rStr = self.renderRows()
        return '\n  <tbody%s>%s\n  </tbody>' % (cssClass, rStr)

    def renderRows(self):
        counter = 0
        rows = []
        cssClasses = (self.cssClassEven, self.cssClassOdd)
        append = rows.append
        for row in self.rows:
            append(self.renderRow(row, cssClasses[counter % 2]))
            counter +=1
        return u''.join(rows)

    def renderRow(self, row, cssClass=None):
        isSelected = self.isSelectedRow(row)
        if isSelected and self.cssClassSelected and cssClass:
            cssClass = '%s %s' % (self.cssClassSelected, cssClass)
        elif isSelected and self.cssClassSelected:
            cssClass = self.cssClassSelected
        cssClass = self.getCSSClass('tr', cssClass)
        cells = [self.renderCell(item, col, colspan)
                 for item, col, colspan in row]
        return u'\n    <tr%s>%s\n    </tr>' % (cssClass, u''.join(cells))

    def renderCell(self, item, column, colspan=0):
        if interfaces.INoneCell.providedBy(column):
            return u''
        cssClass = column.cssClasses.get('td')
        cssClass = self.getCSSClass('td', cssClass)
        colspanStr = colspan and ' colspan="%s"' % colspan or ''
        return u'\n      <td%s%s>%s</td>' % (cssClass, colspanStr,
            column.renderCell(item))

    def update(self):
        # reset values
        self.columnCounter = 0
        self.columnByIndex = {}
        self.selectedItems = []

        # use batch values from request or the existing ones
        self.batchSize = self.getBatchSize()
        self.batchStart = self.getBatchStart()
        # use srting values from request or the existing ones
        self.sortOn = self.getSortOn()
        self.sortOrder = self.getSortOrder()

        # setup columns
        self.columns = self.setUpColumns()

        # order columns
        self.orderColumns()

        # update columns
        self.updateColumns()

        # setup headers bsaed on columns
        self.rows = self.setUpRows()

        # sort items on columns
        self.sortRows()

        # batch sorted rows
        self.batchRows()

        self.updateBatch()

    def render(self):
        
        # allow to use a template for rendering the table, this will allow
        # to position the batch before and after the table
        
        return self.renderTable()

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.__name__)


class SequenceTable(Table):
    """Sequence table adapts a sequence as context.
    
    This table can be used for adapting a z3c.indexer.search.ResultSet or
    z3c.batching.batch.Batch instance as context. Batch which wraps a 
    ResultSet sequence.
    """

    zope.interface.implements(interfaces.ISequenceTable)

    @property
    def values(self):
        return self.context
