##############################################################################
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""WebDAV method PROPFIND

$Id$
"""
__docformat__ = 'restructuredtext'

from xml.dom import minidom
from zope.schema import getFieldNamesInOrder
from zope.app import zapi
from zope.app.container.interfaces import IReadContainer
from zope.app.form.utility import setUpWidgets

from interfaces import IDAVWidget, IDAVNamespace
from opaquenamespaces import IDAVOpaqueNamespaces

class PROPFIND(object):
    """PROPFIND handler for all objects"""

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.setDepth(request.getHeader('depth', 'infinity'))
        ct = request.getHeader('content-type', 'text/xml')
        if ';' in ct:
            parts = ct.split(';', 1)
            self.content_type = parts[0].strip().lower()
            self.content_type_params = parts[1].strip()
        else:
            self.content_type = ct.lower()
            self.content_type_params = None
        self.default_ns = 'DAV:'

    def getDepth(self):
        return self._depth

    def setDepth(self, depth):
        self._depth = depth.lower()

    def PROPFIND(self):
        request = self.request
        resource_url = str(zapi.getView(self.context, 'absolute_url', request))
        if IReadContainer.providedBy(self.context):
            resource_url = resource_url + '/'
        data = request.bodyFile
        data.seek(0)
        response = ''
        body = ''

        if self.content_type not in ['text/xml', 'application/xml']:
            request.response.setStatus(400)
            return body

        if self.getDepth() not in ['0', '1', 'infinity']:
            request.response.setStatus(400)
            return body

        xmldoc = minidom.parse(data)
        response = minidom.Document()
        ms = response.createElement('multistatus')
        ms.setAttribute('xmlns', self.default_ns)
        response.appendChild(ms)
        re = response.createElement('response')
        ms.appendChild(re)
        re.appendChild(response.createElement('href'))
        re.lastChild.appendChild(response.createTextNode(resource_url))
        _avail_props = {}
        
        # List all *registered* DAV interface namespaces and their properties
        for ns, iface in zapi.getUtilitiesFor(IDAVNamespace):
            _avail_props[ns] = getFieldNamesInOrder(iface)
            
        # List all opaque DAV namespaces and the properties we know of
        for ns, oprops in IDAVOpaqueNamespaces(self.context, {}).items():
            _avail_props[ns] = oprops.keys()
        
        propname = xmldoc.getElementsByTagNameNS(self.default_ns, 'propname')
        if propname:
            self._handlePropname(response, re, _avail_props)

        source = xmldoc.getElementsByTagNameNS(self.default_ns, 'prop')
        _props = {}
        if not source and not propname:
            _props = self._handleAllprop(_avail_props, _props)

        if source and not propname:
            _props = self._handleProp(source, _props)

        avail, not_avail = self._propertyResolver(_props)
        if avail:
            self._renderAvail(avail, response, _props)
        if not_avail:
            self._renderNotAvail(not_avail, response)
            
        self._depthRecurse(ms)

        body = response.toxml().encode('utf-8')
        request.response.setBody(body)
        request.response.setStatus(207)
        return body

    def _depthRecurse(self, ms):
        depth = self.getDepth()
        if depth == '1':
            subdepth = '0'
        if depth == 'infinity':
            subdepth = 'infinity'
        if depth != '0':
            if IReadContainer.providedBy(self.context):
                for id, obj in self.context.items():
                    pfind = zapi.queryView(obj, 'PROPFIND', self.request, None)
                    if pfind is not None:
                        pfind.setDepth(subdepth)
                        value = pfind.PROPFIND()
                        parsed = minidom.parseString(value)
                        responses = parsed.getElementsByTagNameNS(
                            self.default_ns, 'response')
                        for r in responses:
                            ms.appendChild(r)

    def _handleProp(self, source, _props):
        source = source[0]
        childs = [e for e in source.childNodes
                  if e.nodeType == e.ELEMENT_NODE]
        for node in childs:
            ns = node.namespaceURI
            iface = zapi.queryUtility(IDAVNamespace, ns)
            value = _props.get(ns, {'iface': iface, 'props': []})
            value['props'].append(node.localName)
            _props[ns] = value
        return _props

    def _handleAllprop(self, _avail_props, _props):
        for ns in _avail_props.keys():
            iface = zapi.queryUtility(IDAVNamespace, ns)
            _props[ns] = {'iface': iface, 'props': _avail_props.get(ns)}
        return _props

    def _handlePropname(self, response, re, _avail_props):
        re.appendChild(response.createElement('propstat'))
        prop = response.createElement('prop')
        re.lastChild.appendChild(prop)
        count = 0
        for ns in _avail_props.keys():
            attr_name = 'a%s' % count
            if ns is not None and ns != self.default_ns:
                count += 1
                prop.setAttribute('xmlns:%s' % attr_name, ns)
            for p in _avail_props.get(ns):
                el = response.createElement(p)
                prop.appendChild(el)
                if ns is not None and ns != self.default_ns:
                    el.setAttribute('xmlns', attr_name)
        re.lastChild.appendChild(response.createElement('status'))
        re.lastChild.lastChild.appendChild(
            response.createTextNode('HTTP/1.1 200 OK'))

    def _propertyResolver(self, _props):
        avail = {}
        not_avail = {}
        oprops = IDAVOpaqueNamespaces(self.context, {})
        for ns in _props.keys():
            iface = _props[ns]['iface']
            for p in _props[ns]['props']:
                if iface is None:
                    if oprops.get(ns, {}).get(p):
                        l = avail.get(ns, [])
                        l.append(p)
                        avail[ns] = l
                    else:    
                        l = not_avail.get(ns, [])
                        l.append(p)
                        not_avail[ns] = l
                    continue
                adapter = iface(self.context, None)
                if adapter is None:
                    l = not_avail.get(ns, [])
                    l.append(p)
                    not_avail[ns] = l
                    continue
                if hasattr(adapter, p):
                    l = avail.get(ns, [])
                    l.append(p)
                    avail[ns] = l
                else:
                    l = not_avail.get(ns, [])
                    l.append(p)
                    not_avail[ns] = l

        return avail, not_avail
    
    def _renderAvail(self, avail, response, _props):
        re = response.lastChild.lastChild
        re.appendChild(response.createElement('propstat'))
        prop = response.createElement('prop')
        re.lastChild.appendChild(prop)
        re.lastChild.appendChild(response.createElement('status'))
        re.lastChild.lastChild.appendChild(
            response.createTextNode('HTTP/1.1 200 OK'))
        count = 0
        for ns in avail.keys():
            attr_name = 'a%s' % count
            if ns is not None and ns != self.default_ns:
                count += 1
                prop.setAttribute('xmlns:%s' % attr_name, ns)
            iface = _props[ns]['iface']

            if not iface:
                # The opaque properties case, hand it off
                oprops = IDAVOpaqueNamespaces(self.context, {})
                for name in avail.get(ns):
                    oprops.renderProperty(ns, attr_name, name, prop)
                continue
            
            # The registered namespace case
            initial = {}
            adapter = iface(self.context, None)
            for name in avail.get(ns):
                value = getattr(adapter, name, None)
                if value is not None:
                    initial[name] = value
            setUpWidgets(self, iface, IDAVWidget,
                ignoreStickyValues=True, initial=initial, 
                names=avail.get(ns))
                        
            for p in avail.get(ns):
                el = response.createElement('%s' % p )
                if ns is not None and ns != self.default_ns:
                    el.setAttribute('xmlns', attr_name)
                prop.appendChild(el)
                value = getattr(self, p+'_widget')()
                    
                if isinstance(value, (unicode, str)):
                    # Get the widget value here
                    el.appendChild(response.createTextNode(value))
                else:
                    if zapi.isinstance(value, minidom.Node):
                        el.appendChild(value)
                    else:
                        # Try to string-ify
                        value = str(getattr(self, p+'_widget'))
                        # Get the widget value here
                        el.appendChild(response.createTextNode(value))

    def _renderNotAvail(self, not_avail, response):
        re = response.lastChild.lastChild
        re.appendChild(response.createElement('propstat'))
        prop = response.createElement('prop')
        re.lastChild.appendChild(prop)
        re.lastChild.appendChild(response.createElement('status'))
        re.lastChild.lastChild.appendChild(
            response.createTextNode('HTTP/1.1 404 Not Found'))
        count = 0
        for ns in not_avail.keys():
            attr_name = 'a%s' % count
            if ns is not None and ns != self.default_ns:
                count += 1
                prop.setAttribute('xmlns:%s' % attr_name, ns)
            for p in not_avail.get(ns):
                el = response.createElement('%s' % p )
                prop.appendChild(el)
                if ns is not None and ns != self.default_ns:
                    el.setAttribute('xmlns', attr_name)
