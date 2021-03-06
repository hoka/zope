##############################################################################
#
# Copyright (c) 2004 Five Contributors. All rights reserved.
#
# This software is distributed under the terms of the Zope Public
# License (ZPL) v2.1. See COPYING.txt for more information.
#
##############################################################################
"""Browser directives

Directives to emulate the 'http://namespaces.zope.org/browser'
namespace in ZCML known from zope.app.

$Id$
"""
import os

from zope.interface import Interface
from zope.component import getGlobalService, ComponentLookupError
from zope.configuration.exceptions import ConfigurationError
from zope.component.servicenames import Presentation
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.publisher.browser.viewmeta import pages as zope_app_pages
from zope.app.component.metaconfigure import handler
from zope.app.component.interface import provideInterface

from resource import FileResourceFactory, ImageResourceFactory
from resource import PageTemplateResourceFactory
from resource import DirectoryResourceFactory
from browser import BrowserView
from metaclass import makeClass
from security import getSecurityInfo, protectClass, protectName, initializeClass

def page(_context, name, permission, for_,
         layer='default', template=None, class_=None,
         attribute='__call__', menu=None, title=None,
         allowed_interface=None, allowed_attributes=None,
         ):

    try:
        s = getGlobalService(Presentation)
    except ComponentLookupError, err:
        pass

    if not (class_ or template):
        raise ConfigurationError("Must specify a class or template")
    if allowed_attributes is None:
        allowed_attributes = []
    if allowed_interface is not None:
        for interface in allowed_interface:
            attrs = [n for n, d in interface.namesAndDescriptions(1)]
            allowed_attributes.extend(attrs)

    if attribute != '__call__':
        if template:
            raise ConfigurationError(
                "Attribute and template cannot be used together.")

        if not class_:
            raise ConfigurationError(
                "A class must be provided if attribute is used")

    if template:
        template = os.path.abspath(str(_context.path(template)))
        if not os.path.isfile(template):
            raise ConfigurationError("No such file", template)

    if class_:
        # new-style classes do not work with Five. As we want to import
        # packages from z3 directly, we ignore new-style classes for now.
        if type(class_) == type:
            return
        if attribute != '__call__':
            if not hasattr(class_, attribute):
                raise ConfigurationError(
                    "The provided class doesn't have the specified attribute "
                    )
        cdict = getSecurityInfo(class_)
        if template:
            new_class = makeClassForTemplate(template, bases=(class_, ),
                                             cdict=cdict)
        elif attribute != "__call__":
            # we're supposed to make a page for an attribute (read:
            # method) and it's not __call__.  We thus need to create a
            # new class using our mixin for attributes.
            cdict.update({'__page_attribute__': attribute})
            new_class = makeClass(class_.__name__,
                                  (class_, ViewMixinForAttributes),
                                  cdict)

            # in case the attribute does not provide a docstring,
            # ZPublisher refuses to publish it.  So, as a workaround,
            # we provide a stub docstring
            func = getattr(new_class, attribute)
            if not func.__doc__:
                # cannot test for MethodType/UnboundMethod here
                # because of ExtensionClass
                if hasattr(func, 'im_func'):
                    # you can only set a docstring on functions, not
                    # on method objects
                    func = func.im_func
                func.__doc__ = "Stub docstring to make ZPublisher work"
        else:
            # we could use the class verbatim here, but we'll execute
            # some security declarations on it so we really shouldn't
            # modify the original.  So, instead we make a new class
            # with just one base class -- the original
            new_class = makeClass(class_.__name__, (class_,), cdict)

    else:
        # template
        new_class = makeClassForTemplate(template)

    _handle_for(_context, for_)

    _context.action(
        discriminator = ('view', for_, name, IBrowserRequest, layer),
        callable = handler,
        args = (Presentation, 'provideAdapter',
                IBrowserRequest, new_class, name, [for_], Interface, layer,
                _context.info),
        )
    _context.action(
        discriminator = ('five:protectClass', new_class),
        callable = protectClass,
        args = (new_class, permission)
        )
    if allowed_attributes:
        for attr in allowed_attributes:
            _context.action(
                discriminator = ('five:protectName', new_class, attr),
                callable = protectName,
                args = (new_class, attr, permission)
                )
    _context.action(
        discriminator = ('five:initialize:class', new_class),
        callable = initializeClass,
        args = (new_class,)
        )

class pages(zope_app_pages):

    def page(self, _context, name, attribute='__call__', template=None,
             menu=None, title=None):
        return page(_context,
                    name=name,
                    attribute=attribute,
                    template=template,
                    menu=menu, title=title,
                    **(self.opts))

def defaultView(_context, name, for_=None):

    type = IBrowserRequest

    _context.action(
        discriminator = ('defaultViewName', for_, type, name),
        callable = handler,
        args = (Presentation,
                'setDefaultViewName', for_, type, name),
        )

    _handle_for(_context, for_)

def _handle_for(_context, for_):
    if for_ is not None:
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = ('', for_)
            )

_factory_map = {'image':{'prefix':'ImageResource',
                         'count':0,
                         'factory':ImageResourceFactory},
                'file':{'prefix':'FileResource',
                        'count':0,
                        'factory':FileResourceFactory},
                'template':{'prefix':'PageTemplateResource',
                            'count':0,
                            'factory':PageTemplateResourceFactory}
                }

def resource(_context, name, layer='default', permission='zope.Public',
             file=None, image=None, template=None):

    if ((file and image) or (file and template) or
        (image and template) or not (file or image or template)):
        raise ConfigurationError(
            "Must use exactly one of file or image or template"
            "attributes for resource directives"
            )

    res = file or image or template
    res_type = ((file and 'file') or
                 (image and 'image') or
                 (template and 'template'))
    factory_info = _factory_map.get(res_type)
    factory_info['count'] += 1
    res_factory = factory_info['factory']
    class_name = '%s%s' % (factory_info['prefix'], factory_info['count'])
    new_class = makeClass(class_name, (res_factory.resource,), {})
    factory = res_factory(name, res, resource_factory=new_class)

    _context.action(
        discriminator = ('resource', name, IBrowserRequest, layer),
        callable = handler,
        args = (Presentation, 'provideResource',
                name, IBrowserRequest, factory, layer),
        )
    _context.action(
        discriminator = ('five:protectClass', new_class),
        callable = protectClass,
        args = (new_class, permission)
        )
    _context.action(
        discriminator = ('five:initialize:class', new_class),
        callable = initializeClass,
        args = (new_class,)
        )

_rd_map = {ImageResourceFactory:{'prefix':'DirContainedImageResource',
                                 'count':0},
           FileResourceFactory:{'prefix':'DirContainedFileResource',
                                'count':0},
           PageTemplateResourceFactory:{'prefix':'DirContainedPTResource',
                                        'count':0},
           DirectoryResourceFactory:{'prefix':'DirectoryResource',
                                     'count':0}
           }

def resourceDirectory(_context, name, directory, layer='default',
                      permission='zope.Public'):

    if not os.path.isdir(directory):
        raise ConfigurationError(
            "Directory %s does not exist" % directory
            )

    resource = DirectoryResourceFactory.resource
    f_cache = {}
    resource_factories = dict(resource.resource_factories)
    resource_factories['default'] = resource.default_factory
    for ext, factory in resource_factories.items():
        if f_cache.get(factory) is not None:
            continue
        factory_info = _rd_map.get(factory)
        factory_info['count'] += 1
        class_name = '%s%s' % (factory_info['prefix'], factory_info['count'])
        factory_name = '%s%s' % (factory.__name__, factory_info['count'])
        f_resource = makeClass(class_name, (factory.resource,), {})
        f_cache[factory] = makeClass(factory_name, (factory,),
                                     {'resource':f_resource})
    for ext, factory in resource_factories.items():
        resource_factories[ext] = f_cache[factory]
    default_factory = resource_factories['default']
    del resource_factories['default']

    cdict = {'resource_factories':resource_factories,
             'default_factory':default_factory}

    factory_info = _rd_map.get(DirectoryResourceFactory)
    factory_info['count'] += 1
    class_name = '%s%s' % (factory_info['prefix'], factory_info['count'])
    dir_factory = makeClass(class_name, (resource,), cdict)
    factory = DirectoryResourceFactory(name, directory,
                                       resource_factory=dir_factory)

    new_classes = [dir_factory,
                   ] + [f.resource for f in f_cache.values()]

    _context.action(
        discriminator = ('resource', name, IBrowserRequest, layer),
        callable = handler,
        args = (Presentation, 'provideResource',
                name, IBrowserRequest, factory, layer),
        )
    for new_class in new_classes:
        _context.action(
            discriminator = ('five:protectClass', new_class),
            callable = protectClass,
            args = (new_class, permission)
            )
        _context.action(
            discriminator = ('five:initialize:class', new_class),
            callable = initializeClass,
            args = (new_class,)
            )

#
# mixin classes / class factories
#

class ViewMixinForAttributes(BrowserView):

    # we have an attribute that we can simply tell ZPublisher to go to
    def __browser_default__(self, request):
        return self, (self.__page_attribute__,)

    # this is technically not needed because ZPublisher finds our
    # attribute through __browser_default__; but we also want to be
    # able to call pages from python modules, PythonScripts or ZPT
    def __call__(self, *args, **kw):
        attr = self.__page_attribute__
        meth = getattr(self, attr)
        return meth(*args, **kw)

class ViewMixinForTemplates(BrowserView):

    # short cut to get to macros more easily
    def __getitem__(self, name):
        return self.index.macros[name]

    # make the template publishable
    def __call__(self, *args, **kw):
        return self.index(self, *args, **kw)

def makeClassForTemplate(src, template=None, used_for=None,
                         bases=(), cdict=None):
    # XXX needs to deal with security from the bases?
    if cdict is None:
        cdict = {}
    cdict.update({'index': ViewPageTemplateFile(src, template)})
    bases += (ViewMixinForTemplates,)
    class_ = makeClass("SimpleViewClass from %s" % src, bases, cdict)

    if used_for is not None:
        class_.__used_for__ = used_for

    return class_
