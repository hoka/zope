##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""A plugable authentication module for LDAP.

$Id$
"""

import ldap

from persistent import Persistent

from zope.exceptions import NotFoundError
from zope.interface import implements

from zope.app.location import locate
from zope.app.container.contained import DuplicationError, Contained, setitem
from zope.app.pluggableauth.interfaces import \
        ILoginPasswordPrincipalSource, IContainerPrincipalSource
from zope.app.security.interfaces import IPrincipal

from zope.app.cache.caching import getCacheForObject, getLocationForCache
from zope.app.cache.annotationcacheable import AnnotationCacheable

from interfaces import ILDAPBasedPrincipalSource
from user import LDAPPrincipal

class LDAPPrincipalSource(Contained, Persistent):
    """A Principal source using LDAP"""

    implements(ILoginPasswordPrincipalSource, ILDAPBasedPrincipalSource,
            IContainerPrincipalSource)

    def __init__(self, server=u'', port=389, basedn=u'',
            login_attribute=u'',
            manager_dn=u'', manager_passwd=u''):
        self.host = server
        self.port = port
        self.basedn = basedn
        self.login_attribute = login_attribute
        self.manager_dn = manager_dn
        self.manager_passwd = manager_passwd
        self.search_scope = 1
        self.__cached = []
    
    ### IContainer-related methods

    def __delitem__(self, login):
        cache = getCacheForObject(self)
        location = getLocationForCache(self)
        if cache and location:
            cache.invalidate(location, {'login' : login})

    ### This is the stuff needed to add the Principal to the cache and to
    ### make it containment friendly.
    def __setitem__(self, login, obj):
        obj.id = login
        setitem(self, self._setitem, login, obj)
        if login not in self.__cached:
            self.__cached.append(login)

    def _setitem(self, key, obj):
        cache = getCacheForObject(self)
        location = getLocationForCache(self)
        if cache and location:
            principal = cache.query(location, {'login' : key})
            if principal is None:
                cache.set(obj, location, {'login' : key})

    def keys(self):
        logins = []
        for login in self.__cached :
            if self[login]:
                logins.append(login)
            else:
                self.__cached.remove(login)
        return logins

    def __iter__(self):
        return iter(self.keys())

    ### return a cached principal, if the principal is not in the cache
    ### then return None
    def __getitem__(self, key):
        principal = None
        cache = getCacheForObject(self)
        location = getLocationForCache(self)
        if cache and location:
            principal = cache.query(location, {'login' : key})
        return principal

    def get(self, key, default=None):
        principal = self[key]
        if principal:
            return principal
        else:
            return default

    def values(self):
        principals = []
        for login in self.keys():
            if self[login]:
                principals.append((login, self[login]))
        return principals

    def __len__(self):
        return len(self.keys())
    
    def items(self):
        principals = []
        for login in self.keys():
            if self[login]:
                principals.append(self[login])
        return principals

    def __contains__(self, key):
        return key in self.keys()
    
    ### IPrincipalSource methods
    
    def __findInLDAP(self, login):
        l = self.__connect()
        l.simple_bind_s(self.manager_dn, self.manager_passwd)
        lsearch = l.search_s(self.basedn, self.search_scope,
                '(%s=%s)' % (self.login_attribute, login))
        if lsearch:
            uid_dn, uid_dict = lsearch[0]
            principal = LDAPPrincipal(
                    login = uid_dict[self.login_attribute][0])
            return principal
        else:
            return None

    def getPrincipal(self, id):
        uid = id.split('\t')[2]
        principal = self[uid]
        if principal:
            return principal
        else:
            principal = self.__findInLDAP(uid)
            if principal:
                self[principal.login] = principal
                return principal
            raise NotFoundError, id

    def getPrincipals(self, name):
        if name == '' :
            search = '(%s=*)' % self.login_attribute
        else:
            search = '(%s=*%s*)' % (self.login_attribute, name)
        l = self.__connect()
        l.simple_bind_s(self.manager_dn, self.manager_passwd)
        lsearch = l.search_s(self.basedn, self.search_scope, search)
        
        principals = []
        for node in lsearch:
            node_dn, node_dict = node
            principal = LDAPPrincipal(
                    login = node_dict[self.login_attribute][0])
            try:
                self[principal.login] = principal
            except DuplicationError:
                # There is already a principal with this login in the cache
                principal = self[principal.login]
            principals.append(principal)

        return principals

    def authenticate(self, uid, password):
        if password:
            l = self.__connect()
            dn = '%s=%s,' % (self.login_attribute, uid) + self.basedn
            try:
                l.simple_bind_s(dn, password)
                principal = LDAPPrincipal(login = uid)
                self[uid] = principal
                return principal
            except ldap.INVALID_CREDENTIALS:
                return None
        else:
            return None

    def __connect(self):
        connection = getattr(self, '_v_conn', None)

        if connection is not None :
            # we have a cached connection,  test it to see if it is still valid
            try :
                connection.simple_bind_s(self.manager_dn, self.manager_passwd)
            #except ldap.LDAPError, err :
            #except (ldap.CONNECT_ERROR, ldap.SERVER_DOWN), err :
            except ldap.SERVER_DOWN, err :
                # it's not valid so discard it
                connection = None

        # no valid connection exists, create a new one and cache it
        if connection is None :
            connectstring = 'ldap://%s:%s' % (self.host, self.port)
            connection = ldap.initialize(connectstring)
            self._v_conn = connection

        return connection
    # end __connect()

# end class LDAPPrincipalSource

