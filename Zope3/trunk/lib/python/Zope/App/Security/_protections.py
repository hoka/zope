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
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""Register protection information for some standard low-level types

Revision information:
$Id: _protections.py,v 1.3 2002/11/19 23:25:14 jim Exp $
"""

def protect():
    from Zope.Security.Checker import \
         defineChecker, getCheckerForInstancesOf, NamesChecker
    import Persistence.BTrees


    def _protect(which):
        __import__('Persistence.BTrees.%sBTree' % which)
        module = getattr(Persistence.BTrees, "%sBTree" % which)
        
        defineChecker(getattr(module, '%sBTree' % which),
                      getCheckerForInstancesOf(dict))
        defineChecker(getattr(module, '%sBucket' % which),
                      getCheckerForInstancesOf(dict))
        defineChecker(getattr(module, '%sSet' % which),
                      NamesChecker(['__getitem__', '__len__', 'has_key',
                                    '__repr__', '__str__', "__contains__",
                                    'keys', 'maxKey', 'minKey']
                                   )
                      )
        defineChecker(getattr(module, '%sTreeSet' % which),
                      NamesChecker(['__len__', 'has_key', "__contains__",
                                   '__repr__', '__str__',
                                   'keys', 'maxKey', 'minKey']
                                   )
                      )
        items = getattr(module, '%sBTree' % which)().keys()
        defineChecker(type(items),
                      getCheckerForInstancesOf(tuple))
        
        
    for which in 'OO', 'II', 'OI', 'IO':
        _protect(which)

    from Persistence.PersistentList import PersistentList

    defineChecker(PersistentList,
                  NamesChecker(
                     ['__getitem__', '__getslice__', '__len__', '__iter__',
                      '__contains__', 'index', 'count'])
                  )

    from Persistence.PersistentDict import PersistentDict

    defineChecker(PersistentDict,
                  NamesChecker(['__getitem__', '__len__', '__iter__',
                        'get', 'has_key', '__copy__',
                        'keys', 'values', 'items',
                        'iterkeys', 'iteritems', 'itervalues', '__contains__',
                        ]
                     )
                  )
    
