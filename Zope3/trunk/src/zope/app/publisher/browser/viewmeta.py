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
"""Browser configuration code

$Id: viewmeta.py,v 1.4 2002/12/30 23:33:46 jim Exp $
"""

# XXX this will need to be refactored soon. :)

from zope.security.proxy import Proxy
from zope.security.checker import CheckerPublic, NamesChecker, Checker
from zope.security.checker import defineChecker

from zope.interfaces.configuration import INonEmptyDirective
from zope.interfaces.configuration import ISubdirectiveHandler
from zope.configuration.action import Action
from zope.configuration.exceptions import ConfigurationError

from zope.publisher.interfaces.browser import IBrowserPresentation
from zope.publisher.interfaces.browser import IBrowserPublisher

from zope.publisher.browser import BrowserView

from zope.app.component.metaconfigure import handler

from zope.app.pagetemplate.simpleviewclass import SimpleViewClass
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

from zope.app.security.permission import checkPermission

from zope.proxy.context import ContextMethod

from zope.app.publisher.browser.globalbrowsermenuservice \
     import menuItemDirective

# There are three cases we want to suport:
#
# Named view without pages (single-page view)
#
#     <browser:page
#         for=".IContact.IContactInfo."
#         name="info.html" 
#         template="info.pt"
#         class=".ContactInfoView."
#         permission="Zope.View"
#         />
#
# Unamed view with pages (multi-page view)
#
#     <browser:pages
#         for=".IContact."
#         class=".ContactEditView."
#         permission="ZopeProducts.Contact.ManageContacts"
#         >
# 
#       <browser:page name="edit.html"       template="edit.pt" />
#       <browser:page name="editAction.html" attribute="action" />
#       </browser:pages>
#
# Named view with pages (add view is a special case of this)
#
#        <browser:view
#            name="ZopeProducts.Contact"
#            for="Zope.App.OFS.Container.IAdding."
#            class=".ContactAddView."
#            permission="ZopeProducts.Contact.ManageContacts"
#            >
#
#          <browser:page name="add.html"    template="add.pt" />
#          <browser:page name="action.html" attribute="action" />
#          </browser:view>

# We'll also provide a convenience directive for add views:
#
#        <browser:add
#            name="ZopeProducts.Contact"
#            class=".ContactAddView."
#            permission="ZopeProducts.Contact.ManageContacts"
#            >
#
#          <browser:page name="add.html"    template="add.pt" />
#          <browser:page name="action.html" attribute="action" />
#          </browser:view>

# page

def _handle_permission(_context, permission, actions):
    if permission == 'zope.Public':
        permission = CheckerPublic
    else:
        actions.append(Action(discriminator = None, callable = checkPermission,
                              args = (None, permission)))

    return permission

def _handle_allowed_interface(_context, allowed_interface, permission,
                              required, actions):
    # Allow access for all names defined by named interfaces
    if allowed_interface.strip():
        for i in allowed_interface.strip().split():
            i = _context.resolve(i)
            actions .append(
                Action(discriminator = None, callable = handler,
                       args = ('Interfaces', 'provideInterface', None, i)
                       ))
            for name in i:
                required[name] = permission

def _handle_allowed_attributes(_context, allowed_attributes, permission,
                               required):
    # Allow access for all named attributes
    if allowed_attributes.strip():
        for name in allowed_attributes.strip().split():
            required[name] = permission

def _handle_for(_context, for_, actions):
    if for_ == '*':
        for_ = None
        
    if for_ is not None:
        for_ = _context.resolve(for_)
        
        actions .append(
            Action(discriminator = None, callable = handler,
                   args = ('Interfaces', 'provideInterface', None, for_)
            ))

    return for_

class simple(BrowserView):

    __implements__ = IBrowserPublisher, BrowserView.__implements__

    def publishTraverse(self, request, name):
        raise NotFound(self, name, request)

def page(_context, name, permission, for_,
         layer='default', template=None, class_=None,
         allowed_interface='', allowed_attributes='',
         attribute='__call__', menu=None, title=None
         ):

    actions = []
    required = {}

    if menu or title:
        if not (menu and title):
            raise ConfigurationError(
                "If either menu or title are specified, they must "
                "both be specified.")

        actions = menuItemDirective(_context, menu, for_, '@@' + name, title,
                                    permission=permission)

    permission = _handle_permission(_context, permission, actions)
            
    if not (class_ or template):
        raise ConfigurationError("Must specify a class or template")

    if attribute != '__call__' and template:
        raise ConfigurationError(
            "Attribute and template cannot be used together.")

    if template:
        template = str(_context.path(template))
        required['__getitem__'] = permission

    if class_:
        class_ = _context.resolve(class_)
        if template:
            template = str(_context.path(template))

            class_ = SimpleViewClass(template, bases=(class_, ))

        else:
            if not hasattr(class_, 'browserDefault'):
                cdict = { 'browserDefault':
                          lambda self, request:
                          (getattr(self, attribute), ())
                          }
            else:
                cdict = {}
                
            class_ = type(class_.__name__, (class_, simple,), cdict)
            
    else:
        class_ = SimpleViewClass(template)
        
    for n in (attribute, 'browserDefault'):
        required[n] = permission

    _handle_allowed_interface(_context, allowed_interface, permission,
                              required, actions)
    _handle_allowed_attributes(_context, allowed_interface, permission,
                               required)
    for_ = _handle_for(_context, for_, actions)

    defineChecker(class_, Checker(required))

    actions.append(
        Action(
          discriminator = ('view', for_, name, IBrowserPresentation, layer),
          callable = handler,
          args = ('Views', 'provideView',
                  for_, name, IBrowserPresentation, [class_], layer),
          )
        )

    return actions

class view:

    default_allowed_attributes = '__call__'  # space separated string

    __class_implements__ = INonEmptyDirective
    __implements__ = ISubdirectiveHandler

    __pages = None
    __default = None

    def __init__(self, _context, factory=None, name=None, for_=None,
                 layer='default',
                 permission=None,
                 allowed_interface=None, allowed_attributes=None,
                 template=None, class_=None):

        if class_ and factory:
            raise ConfigurationError("Can't specify a class and a factory")

        factory = factory or class_

        if template:
            if name is None:
                raise ConfigurationError(
                    "Must specify name for template view")

            self.default_allowed_attributes = (
                '__call__ __getitem__ browserDefault')

            template = _context.path(template)

        self.template = template

        if for_ is not None:
            for_ = _context.resolve(for_)
        self.for_ = for_

        if ((allowed_attributes or allowed_interface)
            and ((name is None) or not permission)):
            raise ConfigurationError(
                "Must use name attribute with allowed_interface or "
                "allowed_attributes"
                )

        if allowed_interface is not None:
            allowed_interface = _context.resolve(allowed_interface)

        self.factory = self._factory(_context, factory)
        self.layer = layer
        self.name = name
        self.permission = permission
        self.allowed_attributes = allowed_attributes
        self.allowed_interface = allowed_interface
        self.pages = 0

        if name:
            self.__pages = {}


    def page(self, _context, name, attribute=None, permission=None,
             layer=None, template=None):

        if self.template:
            raise ConfigurationError(
                "Can't use page or defaultPage subdirectives for simple "
                "template views")

        self.pages += 1

        if self.name:
            # Named view with pages.

            if layer is not None:
                raise ConfigurationError(
                    "Can't specify a separate layer for pages of named "
                    "templates.")

            if template is not None:
                template = _context.path(template)

            self.__pages[name] = attribute, permission, template
            if self.__default is None:
                self.__default = name

            return ()

        factory = self.factory

        if template is not None:
            attribute = attribute or '__template__'
            klass = factory[-1]
            klass = type(klass.__name__, (klass, object), {
                attribute:
                ViewPageTemplateFile(_context.path(template))
                })
            factory = factory[:]
            factory[-1] = klass

        permission = permission or self.permission

        factory = self._pageFactory(factory or self.factory,
                                    attribute, permission)

        if layer is None:
            layer = self.layer

        return [
            Action(
                discriminator = ('view', self.for_, name,
                                 IBrowserPresentation, layer),
                callable = handler,
                args = ('Views', 'provideView',
                        self.for_, name, IBrowserPresentation, factory, layer),
                )
            ]


    def defaultPage(self, _context, name):
        if self.name:
            self.__default = name
            return ()

        return [Action(
            discriminator = ('defaultViewName', self.for_,
                             IBrowserPresentation, name),
            callable = handler,
            args = ('Views','setDefaultViewName', self.for_,
                    IBrowserPresentation, name),
            )]


    def _factory(self, _context, factory):
        if self.template:
            if factory:
                factory = map(_context.resolve, factory.strip().split())
                bases = (factory[-1], )
                klass = SimpleViewClass(
                    str(_context.path(self.template)),
                    used_for=self.for_, bases=bases
                    )
                factory[-1] = klass
                return factory

            return [SimpleViewClass(
                str(_context.path(self.template)),
                used_for = self.for_
                )]
        else:
            return map(_context.resolve, factory.strip().split())

    def _pageFactory(self, factory, attribute, permission):
        factory = factory[:]
        if permission:
            if permission == 'zope.Public':
                permission = CheckerPublic

            def pageView(context, request,
                         factory=factory[-1], attribute=attribute,
                         permission=permission):
                return Proxy(getattr(factory(context, request), attribute),
                             NamesChecker(__call__ = permission))
        else:
            def pageView(context, request,
                         factory=factory[-1], attribute=attribute):
                return getattr(factory(context, request), attribute)
        factory[-1] = pageView
        return factory

    def _proxyFactory(self, factory, checker):
        factory = factory[:]

        def proxyView(context, request,
                      factory=factory[-1], checker=checker):

            view = factory(context, request)

            # We need this in case the resource gets unwrapped and
            # needs to be rewrapped
            view.__Security_checker__ = checker

            return Proxy(view, checker)

        factory[-1] =  proxyView

        return factory

    def _call(self, require=None):
        if self.name is None:
            return ()

        permission = self.permission
        allowed_interface = self.allowed_interface
        allowed_attributes = self.allowed_attributes
        factory = self.factory

        if permission:
            if require is None:
                require = {}

            if permission == 'zope.Public':
                permission = CheckerPublic

            if ((not allowed_attributes) and (allowed_interface is None)
                and (not self.pages)):
                allowed_attributes = self.default_allowed_attributes

            for name in (allowed_attributes or '').split():
                require[name] = permission

            if allowed_interface:
                for name in allowed_interface.names(1):
                    require[name] = permission

        if require:
            checker = Checker(require.get)

            factory = self._proxyFactory(factory, checker)


        return [
            Action(
                discriminator = ('view', self.for_, self.name,
                                 IBrowserPresentation, self.layer),
                callable = handler,
                args = ('Views', 'provideView',
                        self.for_, self.name, IBrowserPresentation,
                        factory, self.layer),
                )
            ]


    def __call__(self):
        if not self.__pages:
            return self._call()

        # OK, we have named pages on a named view.
        # We'll replace the original class with a new subclass that
        # can traverse to the necessary pages.

        require = {}

        factory = self.factory[:]
        klass = factory[-1]

        klassdict = {'_PageTraverser__pages': {},
                     '_PageTraverser__default': self.__default,
                     '__implements__':
                     (klass.__implements__, PageTraverser.__implements__),
                     }

        for name in self.__pages:
            attribute, permission, template = self.__pages[name]

            # We need to set the default permission on pages if the pages
            # don't already have a permission explicitly set
            permission = permission or self.permission
            if permission == 'zope.Public':
                permission = CheckerPublic

            if not attribute:
                attribute = name

            require[attribute] = permission

            if template:
                klassdict[attribute] = ViewPageTemplateFile(template)

            klassdict['_PageTraverser__pages'][name] = attribute, permission

        klass = type(klass.__name__,
                     (klass, PageTraverser, object),
                     klassdict)
        factory[-1] = klass
        self.factory = factory

        permission_for_browser_publisher = self.permission
        if permission_for_browser_publisher == 'zope.Public':
            permission_for_browser_publisher = CheckerPublic
        for name in IBrowserPublisher.names(all=1):
            require[name] = permission_for_browser_publisher

        return self._call(require=require)


class PageTraverser:

    __implements__ = IBrowserPublisher

    def publishTraverse(self, request, name):
        attribute, permission = self._PageTraverser__pages[name]
        return Proxy(getattr(self, attribute),
                     NamesChecker(__call__=permission)
                     )
    publishTraverse = ContextMethod(publishTraverse)

    def browserDefault(self, request):
        return self, (self._PageTraverser__default, )
    browserDefault = ContextMethod(browserDefault)


def defaultView(_context, name, for_=None):

    if for_ is not None:
        for_ = _context.resolve(for_)

    actions = [
        Action(
        discriminator = ('defaultViewName', for_, IBrowserPresentation, name),
        callable = handler,
        args = ('Views','setDefaultViewName', for_, IBrowserPresentation,
                name),
        )]

    if for_ is not None:
        actions .append(
            Action(
            discriminator = None,
            callable = handler,
            args = ('Interfaces', 'provideInterface',
                    for_.__module__+'.'+for_.__name__,
                    for_)
            )
        )

    return actions
