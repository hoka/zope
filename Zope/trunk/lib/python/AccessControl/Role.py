"""Access control package"""

__version__='$Revision: 1.4 $'[11:-2]

import Globals
from User import SafeDtml
from Globals import MessageDialog
from string import join, strip, split


class RoleManager:
    """Mixin role management support"""

    manage_rolesForm=SafeDtml('AccessControl/RoleManager_manage_rolesForm')
    smallRolesWidget=SafeDtml('AccessControl/smallRolesWidget')

    def validRoles(self):
	return Globals.Bobobase['Application'].__defined_roles__

    def selectedRoles(self):
	try:    roles=self.__roles__
	except: roles=[]
	if roles is None: roles=[]
	return map(lambda i, r=roles:
		   i in r and ('<OPTION VALUE="%s" SELECTED>%s' % (i,i)) \
		   or  ('<OPTION VALUE="%s">%s' % (i,i)), self.validRoles())

    def aclAChecked(self):
	try:    roles=self.__roles__
	except: return ' CHECKED'
	return ''

    def aclPChecked(self):
	try:    roles=self.__roles__
	except: return ''
	if roles is None: 
	    return ' CHECKED'
	return ''

    def aclEChecked(self):
	try:    roles=self.__roles__
	except: return 0
	if roles is None: 
	    return ''
	return ' CHECKED'


    def manage_editRoles(self,REQUEST,acl_type='A',acl_roles=[]):
        """ """
	try:    del self.__roles__
	except: pass
	if acl_type=='A':
	    return self.manage_rolesForm(self,REQUEST)
	if acl_type=='P':
	    self.__roles__=None
	    return self.manage_rolesForm(self,REQUEST)
	if not acl_roles:
	    raise 'Bad Request','No roles specified!'
	self.__roles__=acl_roles
        return self.manage_rolesForm(self,REQUEST)


    def oldmanage_editRoles(self,REQUEST,roles=[]):
	try:    del self.__roles__
	except: pass
	if not roles:
	    return self.manage_rolesForm(self,REQUEST)
	if roles==['Public',]:
	    self.__roles__=None
	    return self.manage_rolesForm(self,REQUEST)
	if ('Acquire' in roles) or ('Public' in roles):
	    raise 'Bad Request',('<EM>Acquired</EM> and <EM>Public</EM> ' \
				 'cannot be combined with other roles!')
	self.__roles__=roles
        return self.manage_rolesForm(self,REQUEST)

    def manage_addRole(self,REQUEST,role):
	""" """
	app  =Globals.Bobobase['Application']
        roles=list(app.__defined_roles__)
	if role not in roles:
	    roles.append(role)
            roles.sort()
	    app.__defined_roles__=tuple(roles)
	try:    roles=self.__roles__
	except: roles=[]
	if roles is None: roles=[]
        roles.append(role)
	self.__roles__=roles
	return self.manage_rolesForm(self, REQUEST)

    def manage_deleteRole(self,REQUEST,role):
	""" """
	app  =Globals.Bobobase['Application']
	roles=list(app.__defined_roles__)
	if role in roles:
	    del roles[roles.index(role)]
	    app.__defined_roles__=tuple(roles)
	return self.manage_main(self, REQUEST)

    def _setRoles(self,acl_type,acl_roles):
	# Non-web helper to correctly set roles
	try:    del self.__roles__
	except: pass
	if acl_type=='A':
	    return
	if acl_type=='P':
	    self.__roles__=None
	    return
	if not acl_roles:
	    raise 'Bad Request','No roles specified!'
	self.__roles__=acl_roles


# $Log: Role.py,v $
# Revision 1.4  1997/11/06 22:45:26  brian
# Added global roles to app
#
# Revision 1.3  1997/09/08 23:01:33  brian
# Style mods
#
# Revision 1.2  1997/09/02 18:12:13  jim
# Added smallRolesWidget.
#
# Revision 1.1  1997/08/29 18:34:53  brian
# Added basic role management to package.
#
