## Script (Python) "clearCookie.py $Revision$"
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=clear browser cookie
##
REQUEST=context.REQUEST
REQUEST.RESPONSE.expireCookie('folderfilter', path='/')
REQUEST.RESPONSE.redirect( context.absolute_url() + '/folder_contents?portal_status_message=Filter+cleared.')

