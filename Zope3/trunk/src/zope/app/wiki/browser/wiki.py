##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Browser View Components for Wikis

$Id: wiki.py,v 1.3 2004/03/02 14:25:03 srichter Exp $
"""
from datetime import datetime
from zope.proxy import removeAllProxies

from zope.app import zapi
from zope.app.dublincore.interfaces import ICMFDublinCore
from zope.app.services.servicenames import HubIds
from zope.app.traversing import getName, getPath
from zope.app.browser.container.adding import Adding
from zope.app.services.hub import Registration

from zope.app.wiki.interfaces import IWikiPageHierarchy

class AddWiki(object):
    """Add a Wiki"""

    def createAndAdd(self, data):
        content = super(AddWiki, self).createAndAdd(data)
        if self.request.get('textindex'):
            # Get the environment
            sm = zapi.getServiceManager(content)
            pkg = sm['default']
            # Create, subscribe and add a Registration object.
            if 'WikiReg' not in pkg: 
                reg = Registration()
                pkg['WikiReg'] = reg
                reg.subscribe()

        if self.request.get('frontpage'):
            page = removeAllProxies(
                zapi.createObject(None, 'zope.wiki.WikiPage'))
            page.type = u'zope.source.rest'
            page.source = u'This is the FrontPage of the Wiki.'
            dc = zapi.getAdapter(page, ICMFDublinCore)
            dc.created = datetime.now()
            dc.modified = datetime.now()
            dc.creators = [u'wiki']
            content['FrontPage'] = page

        return content


class WikiSearch(object):
    """Search Wiki Pages"""

    def query(self):
        # XXX: Should use indices once they are back in Zope 3
        queryText = self.request.get('queryText', '')
        results = []
        for name, page in self.context.items():
            if page.source.find(queryText) >= 0:
                results.append(name)
            else:
                for comment in page.values():
                    if comment.source.find(queryText) >= 0:
                        results.append(name)
                    
        return {'results': results,
                'total': len(results)}
    

class TableOfContents:
    """Table of contents for a Wiki"""

    def toc(self):
        """Generate a table of contents."""
        children = []

        for name, page in self.context.items():
            hier = zapi.getAdapter(page, IWikiPageHierarchy)
            if hier.getParents() == ():
                children.append((page, hier.findChildren())) 
        return self._branchHTML(children)

    def _branchHTML(self, children):
        html = '<ul>\n'
        for child, subs in children:
            html += ' <li><a href="%s">%s</a></li>\n' %(getName(child),
                                                        getName(child))
            if subs:
                html += self._branchHTML(subs)
        html += '</ul>\n'
        return html
