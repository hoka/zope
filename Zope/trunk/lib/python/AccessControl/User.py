"""Access control package"""

__version__='$Revision: 1.32 $'[11:-2]


from PersistentMapping import PersistentMapping
from Persistence import Persistent
from Globals import HTMLFile, MessageDialog
from string import join,strip,split,lower
from App.Management import Navigation, Tabs
from Acquisition import Implicit
from OFS.SimpleItem import Item
from base64 import decodestring
from ImageFile import ImageFile
import App.Undo



class User(Implicit, Persistent):
    def __init__(self,name,password,roles):
	self.name =name
	self.roles=roles
	self.__   =password

    def authenticate(self, password):
	return password==self.__

    def hasRole(self,inst,roles=None):
	if roles is None:
	    return 1
	for role in roles:
	    if role in self.roles:
		return 1
	return 0

    def __len__(self): return 1
    def __str__(self): return self.name
    __repr__=__str__


try:
    f=open('%s/access' % SOFTWARE_HOME, 'r')
    data=split(strip(f.readline()),':')
    f.close()
    super=User(data[0],data[1],('manage',))
    del data
except:
    super=User('superuser','123',('manage',))

nobody=User('Anonymous User','',('Anonymous',))



class UserFolder(Implicit, Persistent, Navigation, Tabs, Item,
		 App.Undo.UndoSupport):
    """ """
    meta_type='User Folder'
    id       ='acl_users'
    title    ='User Folder'
    icon     ='p_/UserFolder'

    isPrincipiaFolderish=1
    isAUserFolder=1


    manage_options=(
    {'icon': icon, 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm', 'target':'manage_main'},
    )

    def __init__(self):
	self.data=PersistentMapping()

    def __len__(self):
	return len(self.data.keys())

    def _isTop(self):
	try:    t=self.aq_parent.aq_parent.acl_users
	except: return 1
	return 0

    def user_names(self):
	keys=self.data.keys()
	keys.sort()
	return keys

    def validate(self,request,auth='',roles=None):
	if not auth:
	    if roles is None:
		return nobody
	    return None
	if lower(auth[:6])!='basic ':
	    return None
	name,password=tuple(split(decodestring(split(auth)[-1]), ':'))
	if self._isTop() and (name==super.name) and \
	super.authenticate(password):
	    return super
	try:    user=self.data[name]
	except: return None
	if not user.authenticate(password):
	    return None
	if roles is None:
	    return user
	for role in roles:
	    if role in user.roles:
		return user
	return None

    _mainUser=HTMLFile('mainUser', globals())
    _add_User=HTMLFile('addUser', globals())
    _editUser=HTMLFile('editUser', globals())

    def _addUser(self,name,password,confirm,roles,REQUEST=None):
	if not name or not password or not confirm:
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Name, password and confirmation must be specified',
                   action ='manage_main')
	if self.data.has_key(name) or (name==super.name):
            return MessageDialog(
		   title  ='Illegal value', 
                   message='A user with the specified name already exists',
                   action ='manage_main')
	if password!=confirm:
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Password and confirmation do not match',
                   action ='manage_main')
        self.data[name]=User(name,password,roles)
	return self._mainUser(self, REQUEST)

    def _changeUser(self,name,password,confirm,roles,REQUEST=None):
	if not name or not password or not confirm:
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Name, password and confirmation must be specified',
                   action ='manage_main')
	if not self.data.has_key(name):
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Unknown user',
                   action ='manage_main')
	if password!=confirm:
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Password and confirmation do not match',
                   action ='manage_main')
	user=self.data[name]
	user.__=password
	user.roles=roles
	return self._mainUser(self, REQUEST)

    def _delUser(self,names,REQUEST=None):
	if not names:
            return MessageDialog(
		   title  ='Illegal value', 
                   message='No users specified',
                   action ='manage_main')

	if 0 in map(self.data.has_key, names):
            return MessageDialog(
		   title  ='Illegal value',
                   message='One or more items specified do not exist',
                   action ='manage_main')
	for name in names:
            del self.data[name]
        return self._mainUser(self, REQUEST)

    def manage_main(self,submit=None,REQUEST=None):
	""" """
	if submit=='Add...':
	    return self._add_User(self, REQUEST)

	if submit=='Edit':
	    try:    user=self.data[reqattr(REQUEST, 'name')]
	    except: return MessageDialog(
		    title  ='Illegal value',
                    message='The specified user does not exist',
                    action ='manage_main')
	    return self._editUser(self,REQUEST,user=user,password=user.__)

	if submit=='Add':
	    name    =reqattr(REQUEST, 'name')
	    password=reqattr(REQUEST, 'password')
	    confirm =reqattr(REQUEST, 'confirm')
	    roles   =reqattr(REQUEST, 'roles')
	    return self._addUser(name,password,confirm,roles,REQUEST)

	if submit=='Change':
	    name    =reqattr(REQUEST, 'name')
	    password=reqattr(REQUEST, 'password')
	    confirm =reqattr(REQUEST, 'confirm')
	    roles   =reqattr(REQUEST, 'roles')
	    return self._changeUser(name,password,confirm,roles,REQUEST)

	if submit=='Delete':
	    names=reqattr(REQUEST, 'names')
	    return self._delUser(names,REQUEST)

	return self._mainUser(self, REQUEST)

    manage=manage_main


    # Copy/Paste support

    def _getCopy(self, container):
	try:    obj=container.aq_self
	except: obj=container
	if hasattr(obj,'acl_users'):
	    raise ('Copy Error',
		   '<EM>This object already contains a UserFolder</EM>')
	return loads(dumps(self))

    def _postCopy(self, container):
	container.__allow_groups__=container.acl_users

    def _setId(self, clip_id):
	if clip_id != self.id:
	     raise ('Copy Error',
		    '<EM>Cannot change the id of a UserFolder</EM>')




class UserFolderHandler:
    """ """
    meta_types_=({'name':'User Folder', 'action':'manage_addUserFolder'},)

    def manage_addUserFolder(self,dtself=None,REQUEST=None,**ignored):
        """ """
	try:    self._setObject('acl_users', UserFolder())
	except: return MessageDialog(
	               title  ='Item Exists',
                       message='This object already contains a User Folder',
                       action ='%s/manage_main' % REQUEST['PARENT_URL'])
        self.__allow_groups__=self.acl_users
	if REQUEST: return self.manage_main(self,REQUEST)

    def UserFolderIds(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='User Folder':
		t.append(i['id'])
	return t

    def UserFolderValues(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='User Folder':
		t.append(getattr(self,i['id']))
	return t

    def UserFolderItems(self):
	t=[]
	for i in self.objectMap():
	    if i['meta_type']=='User Folder':
		n=i['id']
		t.append((n,getattr(self,n)))
	return t


def absattr(attr):
    if callable(attr): return attr()
    return attr

def reqattr(request, attr):
    try:    return request[attr]
    except: return None
