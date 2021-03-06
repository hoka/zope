##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Topic: Canned catalog queries

$Id$
"""


# This is used by a script (external method) that can be run
# to set up Topics in an existing CMF Site instance.
cmftopic_globals = globals()

def initialize( context ):

    from Products.CMFCore.utils import ContentInit
    from Products.CMFCore.DirectoryView import registerDirectory
    from Products.GenericSetup import EXTENSION
    from Products.GenericSetup import profile_registry

    import Topic
    import SimpleStringCriterion
    import SimpleIntCriterion
    import ListCriterion
    import DateCriteria
    import SortCriterion
    from permissions import AddTopics

    context.registerHelpTitle( 'CMF Topic Help' )
    context.registerHelp( directory='help' )

    # CMF Initializers
    ContentInit( 'CMF Topic Objects'
               , content_types = (Topic.Topic,)
               , permission = AddTopics
               , extra_constructors = (Topic.addTopic,)
               ).initialize( context )

    registerDirectory( 'skins', cmftopic_globals )

    profile_registry.registerProfile('default',
                                     'CMFTopic',
                                     'Adds topic portal type.',
                                     'profiles/default',
                                     'CMFTopic',
                                     EXTENSION)
