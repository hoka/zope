#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################## 
__doc__='''Collected utilities to support database indexing.


$Id: __init__.py,v 1.4 1998/11/25 17:02:27 jeffrey Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

import Query

## import sys, string

## __.__path__.append("%s/bin-%s/%s" % (
##     __.__path__[0], string.split(sys.version)[0], sys.platform))
    
## for m in 'BTree', 'IIBTree', 'IOBTree', 'OIBTree', 'intSet':
##     sys.modules['SearchIndex.%s' % m]=__import__(m)

############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.4  1998/11/25 17:02:27  jeffrey
# got rid of __ for 1.5.x happiness
#
# Revision 1.3  1997/12/05 21:34:30  jim
# Delamification
#
# Revision 1.2  1997/11/21 18:43:49  jim
# hack, hack, hack sys.modules to make old pickles work. :-(
#
# Revision 1.1  1997/09/15 16:07:23  jim
# *** empty log message ***
#
#
