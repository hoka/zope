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

Revision information:
$Id: undo.py,v 1.5 2003/06/25 15:24:20 fdrake Exp $
"""
from zope.interface import implements
from zope.component import getService, getUtility
from zope.publisher.browser import BrowserView
from zope.app.event import function
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.interfaces.undo import IUndoManager
from zope.app.services.servicenames import Utilities


def undoSetup(event):
    # setup undo fnctionality
    svc = getService(None, Utilities)
    svc.provideUtility(IUndoManager, ZODBUndoManager(event.database))

undoSetup = function.Subscriber(undoSetup)


class ZODBUndoManager:
    """Implement the basic undo management api for a single ZODB database.
    """

    implements(IUndoManager)

    def __init__(self, db):
        self.__db = db

    ############################################################
    # Implementation methods for interface
    # zope.app.interfaces.undo.IUndoManager.

    def getUndoInfo(self):
        '''See interface IUndoManager'''

        return self.__db.undoInfo()

    def undoTransaction(self, id_list):
        '''See interface IUndoManager'''

        for id in id_list:
            self.__db.undo(id)

    #
    ############################################################


class Undo(BrowserView):
    """Undo View"""

    index = ViewPageTemplateFile('undo_log.pt')

    def action (self, id_list, REQUEST=None):
        """
        processes undo form and redirects to form again (if possible)
        """
        utility = getUtility(self.context, IUndoManager)
        utility.undoTransaction(id_list)

        if REQUEST is not None:
            REQUEST.response.redirect('index.html')

    def getUndoInfo(self):
        utility = getUtility(self.context, IUndoManager)
        return utility.getUndoInfo()
