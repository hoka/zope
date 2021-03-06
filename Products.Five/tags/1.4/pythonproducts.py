##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Setup necessary monkey patches and other related logic for using 
regular python packages for zope2 products

$Id$
"""
__author__ = "Rocky Burt"

import os
import types

import Products
from App.Product import initializeProduct
from App.ProductContext import ProductContext

_zope_app = None

def setupPythonProducts(appOrContext):
    """Initialize the python-packages-as-products logic
    """
    
    from OFS.Application import Application
    
    global _zope_app
    if isinstance(appOrContext, Application):
        _zope_app = appOrContext
    else:
        _zope_app = appOrContext._ProductContext__app
    
    applyPatches(_zope_app)


def applyPatches(app):
    """Apply necessary monkey patches to force Zope 2 to be capable of
    handling "products" that are not necessarily located under the Products
    package.  Ultimately all functionality provided by these patches should
    be folded into Zope 2 core.
    """
    
    patch_ProductDispatcher__bobo_traverse__(app)
    patch_externalmethod(app)


# BEGIN MONKEY PATCHES
# Most of these monkey patches were repurposed from the code I 
# wrote for Basket - Rocky

def product_packages(app):
    """Returns all product packages including the regularly defined
    zope2 packages and those without the Products namespace package.
    """
    
    old_product_packages = {}
    for x in dir(Products):
        m = getattr(Products, x)
        if isinstance(m, types.ModuleType):
            old_product_packages[x] = m
    
    packages = {}
    products = app.Control_Panel.Products
    for product_id in products.objectIds():
        product = products[product_id]
        if hasattr(product, 'package_name'):
            pos = product.package_name.rfind('.')
            if pos > -1:
                packages[product_id] = __import__(product.package_name, 
                                                  globals(), {}, 
                                                  product.package_name[pos+1:])
            else:
                packages[product_id] = __import__(product.package_name)
        elif old_product_packages.has_key(product_id):
            packages[product_id] = old_product_packages[product_id]
    
    return packages
    
def patch_ProductDispatcher__bobo_traverse__(app):
    """Currently, z2's App.FactoryDispatcher.ProductDispatcher only checks
    the Products module for products to look up existing factory dispatchers
    on.  This needs to be fixed to look in all enabled product packages
    as well.
    """
    
    from App.FactoryDispatcher import FactoryDispatcher, ProductDispatcher
    global _original__bobo_traverse__
    _original__bobo_traverse__ = ProductDispatcher.__bobo_traverse__
    
    def __bobo_traverse__(self, REQUEST, name):
        product=self.aq_acquire('_getProducts')()._product(name)

        # Try to get a custom dispatcher from a Python product
        productPkgs = product_packages(app)
        dispatcher_class=getattr(
            productPkgs.get(name, None),
            '__FactoryDispatcher__',
            FactoryDispatcher)

        dispatcher=dispatcher_class(product, self.aq_parent, REQUEST)
        return dispatcher.__of__(self)
    
    ProductDispatcher.__bobo_traverse__ = __bobo_traverse__
    

def patch_externalmethod(app):
    """In an effort to make External Methods work with regular python
    packages, this function replaces App.Extensions.getPath with a custom 
    getPath function.  See the getPath doc string for extra details.
    """
    
    from App import Extensions, FactoryDispatcher
    from Products.ExternalMethod import ExternalMethod
    
    global _originalGetPath
    _originalGetPath = Extensions.getPath

    def getPath(prefix, name, checkProduct=1, suffixes=('',)):
        """Make sure to check paths of all registered product packages.
        """

        result = _originalGetPath(prefix, name, checkProduct, suffixes)
        if result is not None:
            return result

        try:
            l = name.rfind('.')
            if l > 0:
                realName = name[l + 1:]
                toplevel = name[:l]
                
                pos = toplevel.rfind('.')
                if pos > -1:
                    m = __import__(toplevel, globals(), {}, toplevel[pos+1:])
                else:
                    m = __import__(toplevel)
        
                d = os.path.join(m.__path__[0], prefix, realName)
                
                for s in suffixes:
                    if s: s="%s.%s" % (d, s)
                    else: s=d
                    if os.path.exists(s): 
                        return s
        except:
            pass
    
    Extensions.getPath = getPath
    ExternalMethod.getPath = getPath
