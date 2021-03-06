##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Lexicon z2 interfaces.

$Id$
"""


# create ILexicon
from Interface.bridge import createZope3Bridge
from interfaces import ILexicon as z3ILexicon
import ILexicon

createZope3Bridge(z3ILexicon, ILexicon, 'ILexicon')

del createZope3Bridge
del z3ILexicon
