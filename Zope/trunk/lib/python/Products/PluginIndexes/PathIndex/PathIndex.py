##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

__version__ = '$Id: PathIndex.py,v 1.25 2002/08/14 22:19:31 mj Exp $'

from Products.PluginIndexes import PluggableIndex
from Products.PluginIndexes.common.util import parseIndexRequest

from Globals import Persistent, DTMLFile
from Acquisition import Implicit

from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from BTrees.IIBTree import IISet, intersection, union
from OFS.SimpleItem import SimpleItem
from types import StringType, ListType, TupleType
import re, warnings

_marker = []

class PathIndex(Persistent, Implicit, SimpleItem):
    """ A path index stores all path components of the physical
    path of an object:

    Internal datastructure:

    - a physical path of an object is split into its components

    - every component is kept as a  key of a OOBTree in self._indexes

    - the value is a mapping 'level of the path component' to
      'all documentIds with this path component on this level'

    """

    __implements__ = (PluggableIndex.PluggableIndexInterface,)

    meta_type="PathIndex"

    manage_options= (
        {'label': 'Settings',
         'action': 'manage_main',
         'help': ('PathIndex','PathIndex_Settings.stx')},
    )

    query_options = ["query","level","operator"]


    def __init__(self,id,caller=None):
        self.id = id

        # experimental code for specifing the operator
        self.operators = ['or','and']
        self.useOperator = 'or'

        self.clear()


    def getId(self): return self.id

    def clear(self):
        """ clear everything """

        self._depth   = 0
        self._index   = OOBTree()
        self._unindex = IOBTree()


    def insertEntry(self,comp,id,level):
        """
        k is a path component (generated by splitPath() )
        v is the documentId
        level is the level of the component inside the path
        """

        if self._index.has_key(comp)==0:
            self._index[comp] = IOBTree()

        if self._index[comp].has_key(level)==0:
            self._index[comp][level] = IISet()

        self._index[comp][level].insert(id)

        if level > self._depth: self._depth = level



    def index_object(self, documentId, obj ,threshold=100):
        """ hook for (Z)Catalog """

        # first we check if the object provide an attribute or
        # method to be used as hook for the PathIndex

        if hasattr(obj,self.id):
            f = getattr(obj,self.id)

            try:
                if callable(f): path = f()
                else:           path = f
            except:
                return 0

            if not (isinstance(path,StringType) or
                    isinstance(path,TupleType)):
                raise TypeError, "attribute/method must be/return string or tuple"

        else:

            try:
                path = obj.getPhysicalPath()
            except:
                return 0

        if type(path) in (ListType,TupleType):
            path = '/'+ '/'.join(path[1:])

        comps = self.splitPath(path,obj)

        if obj.meta_type != 'Folder':
            comps = comps[:-1]

        for i in range(len(comps)):
            self.insertEntry( comps[i],documentId,i)

        self._unindex[documentId] = path

        return 1


    def unindex_object(self,documentId):
        """ hook for (Z)Catalog """

        if not self._unindex.has_key(documentId):
            return

        path = self._unindex[documentId]
        comps = path.split('/')

        for level in range(len(comps[1:])-1):
            comp = comps[level+1]

            self._index[comp][level].remove(documentId)

            if len(self._index[comp][level])==0:
                del self._index[comp][level]

            if len(self._index[comp])==0:
                del self._index[comp]

        del self._unindex[documentId]


    def printIndex(self):
        for k,v in self._index.items():
            print "-"*78
            print k
            for k1,v1 in v.items():
                print k1,v1,

            print


    def splitPath(self,path,obj=None):
        """ split physical path of object. If the object has
        as function splitPath() we use this user-defined function
        to split the path
        """

        if hasattr(obj,"splitPath"):
            comps = obj.splitPath(path)
        else:
            comps = filter(lambda x: x , re.split("/",path))

        return comps


    def search(self,path,default_level=0):
        """
        path is either a string representing a
        relative URL or a part of a relative URL or
        a tuple (path,level).

        level>=0  starts searching at the given level
        level<0   not implemented yet
        """

        if isinstance(path,StringType):
            level = default_level
        else:
            level = int(path[1])
            path  = path[0]

        comps = self.splitPath(path)


        if level >=0:

            results = []
            for i in range(len(comps)):

                comp = comps[i]

                if not self._index.has_key(comp): return IISet()
                if not self._index[comp].has_key(level+i): return IISet()

                results.append( self._index[comp][level+i] )

            res = results[0]

            for i in range(1,len(results)):
                res = intersection(res,results[i])

            return res

        else:

            results = IISet()

            for level in range(0,self._depth):

                ids = None
                error = 0

                for cn in range(0,len(comps)):
                    comp = comps[cn]

                    try:
                        ids = intersection(ids,self._index[comp][level+cn])
                    except:
                        error = 1

                if error==0:
                    results = union(results,ids)

            return results



    def __len__(self):
        """ len """
        return len(self._index)


    def numObjects(self):
        """ return the number of indexed objects"""
        return len(self._unindex)


    def keys(self):
        """ return list of all path components """
        keys = []
        for k in self._index.keys(): keys.append(k)
        return keys


    def values(self):
        values = []
        for k in self._index.values(): values.append(k)
        return values


    def items(self):
        """ mapping path components : documentIds """

        items = []
        for k in self._index.items(): items.append(k)
        return items


    def _apply_index(self, request, cid=''):
        """ hook for (Z)Catalog
        request   mapping type (usually {"path": "..." }
                  additionaly a parameter "path_level" might be passed
                  to specify the level (see search())

        cid      ???
        """

        record = parseIndexRequest(request,self.id,self.query_options)
        if record.keys==None: return None

        if request.has_key('%s_level' % cid):
            warnings.warn("The usage of the '%s_level' "
                          "is no longer recommended.\n"
                          "Please use a mapping object and the "
                          "'level' key to specify the operator." % cid)


        # get the level parameter
        level    = record.get("level",0)

        # experimental code for specifing the operator
        operator = record.get('operator',self.useOperator).lower()

        # depending on the operator we use intersection of union
        if operator=="or":  set_func = union
        else:               set_func = intersection

        res = None

        for k in record.keys:
            rows = self.search(k,level)
            res = set_func(res,rows)

        if res:
            return res, (self.id,)
        else:
            return IISet(), (self.id,)


    def uniqueValues(self,name=None,withLength=0):
        """ needed to be consistent with the interface """

        return self._index.keys()


    def getEntryForObject(self,documentId,default=_marker):
        """ Takes a document ID and returns all the information we have
        on that specific object. """

        try:
            return self._unindex[documentId]
        except:
            return None


    index_html = DTMLFile('dtml/index', globals())
    manage_workspace = DTMLFile('dtml/managePathIndex', globals())


manage_addPathIndexForm = DTMLFile('dtml/addPathIndex', globals())

def manage_addPathIndex(self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a path index"""
    return self.manage_addIndex(id, 'PathIndex', extra=None, \
                REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
