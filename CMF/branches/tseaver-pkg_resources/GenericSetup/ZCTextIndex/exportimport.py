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
"""ZCTextIndex export / import support.

$Id$
"""

from BTrees.IOBTree import IOBTree
from BTrees.Length import Length
from BTrees.OIBTree import OIBTree

from Products.GenericSetup.interfaces import PURGE
from Products.GenericSetup.utils import NodeAdapterBase

from Products.ZCTextIndex.interfaces import IZCLexicon
from Products.ZCTextIndex.interfaces import IZCTextIndex
from Products.ZCTextIndex.PipelineFactory import element_factory


class ZCLexiconNodeAdapter(NodeAdapterBase):

    """Node im- and exporter for ZCTextIndex Lexicon.
    """

    __used_for__ = IZCLexicon

    def exportNode(self, doc):
        """Export the object as a DOM node.
        """
        self._doc = doc
        node = self._getObjectNode('object')
        for element in self.context._pipeline:
            group, name = self._getKeys(element)
            child = self._doc.createElement('element')
            child.setAttribute('group', group)
            child.setAttribute('name', name)
            node.appendChild(child)
        return node

    def importNode(self, node, mode=PURGE):
        """Import the object from the DOM node.
        """
        pipeline = []
        for child in node.childNodes:
            if child.nodeName == 'element':
                element = element_factory.instantiate(
                      child.getAttribute('group'), child.getAttribute('name'))
                pipeline.append(element)
        self.context._pipeline = tuple(pipeline)
        #clear lexicon
        self.context._wids = OIBTree()
        self.context._words = IOBTree()
        self.context.length = Length()

    def _getKeys(self, element):
        for group in element_factory.getFactoryGroups():
            for name, factory in element_factory._groups[group].items():
                if factory == element.__class__:
                    return group, name


class ZCTextIndexNodeAdapter(NodeAdapterBase):

    """Node im- and exporter for ZCTextIndex.
    """

    __used_for__ = IZCTextIndex

    def exportNode(self, doc):
        """Export the object as a DOM node.
        """
        self._doc = doc
        node = self._getObjectNode('index')

        for value in self.context.getIndexSourceNames():
            child = self._doc.createElement('indexed_attr')
            child.setAttribute('value', value)
            node.appendChild(child)

        child = self._doc.createElement('extra')
        child.setAttribute('name', 'index_type')
        child.setAttribute('value', self.context.getIndexType())
        node.appendChild(child)

        child = self._doc.createElement('extra')
        child.setAttribute('name', 'lexicon_id')
        child.setAttribute('value', self.context.lexicon_id)
        node.appendChild(child)

        return node

    def importNode(self, node, mode=PURGE):
        """Import the object from the DOM node.
        """
        indexed_attrs = []
        for child in node.childNodes:
            if child.nodeName == 'indexed_attr':
                indexed_attrs.append(child.getAttribute('value'))
        self.context.indexed_attrs = indexed_attrs
        self.context.clear()
