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
""" Unit tests for Event module.

$Id$
"""

from unittest import TestCase, TestSuite, makeSuite, main
import Testing
try:
    import Zope2
except ImportError: # BBB: for Zope 2.7
    import Zope as Zope2
Zope2.startup()

from DateTime import DateTime

from Products.CMFCore.tests.base.dummy import DummyTool
from Products.CMFCore.tests.base.testcase import RequestTest


class TestEvent(TestCase):

    def _makeOne(self, id, *args, **kw):
        from Products.CMFCalendar.Event import Event

        return Event(id, *args, **kw)

    def test_z2interfaces(self):
        from Interface.Verify import verifyClass
        from Products.CMFCore.interfaces.Contentish \
                import Contentish as IContentish
        from Products.CMFCore.interfaces.DublinCore \
                import CatalogableDublinCore as ICatalogableDublinCore
        from Products.CMFCore.interfaces.DublinCore \
                import DublinCore as IDublinCore
        from Products.CMFCore.interfaces.DublinCore \
                import MutableDublinCore as IMutableDublinCore
        from Products.CMFCore.interfaces.Dynamic \
                import DynamicType as IDynamicType
        from Products.CMFCalendar.Event import Event

        verifyClass(ICatalogableDublinCore, Event)
        verifyClass(IContentish, Event)
        verifyClass(IDublinCore, Event)
        verifyClass(IDynamicType, Event)
        verifyClass(IMutableDublinCore, Event)

    def test_z3interfaces(self):
        try:
            from zope.interface.verify import verifyClass
            from Products.CMFCore.interfaces import ICatalogableDublinCore
            from Products.CMFCore.interfaces import IContentish
            from Products.CMFCore.interfaces import IDublinCore
            from Products.CMFCore.interfaces import IDynamicType
            from Products.CMFCore.interfaces import IMutableDublinCore
        except ImportError:
            # BBB: for Zope 2.7
            return
        from Products.CMFCalendar.Event import Event

        verifyClass(ICatalogableDublinCore, Event)
        verifyClass(IContentish, Event)
        verifyClass(IDublinCore, Event)
        verifyClass(IDynamicType, Event)
        verifyClass(IMutableDublinCore, Event)

    def test_new(self):
        event = self._makeOne('test')

        self.assertEqual( event.getId(), 'test' )
        self.failIf( event.Title() )

    def test_edit(self):
        # Year month and day were processed in the wrong order
        # Also see http://collector.zope.org/CMF/202
        event = self._makeOne('foo')
        event.edit( title='title'
                  , description='description'
                  , eventType=( 'eventType', )
                  , effectiveDay=1
                  , effectiveMo=5
                  , effectiveYear=1999
                  , expirationDay=31
                  , expirationMo=12
                  , expirationYear=1999
                  , start_time="00:00"
                  , startAMPM="AM"
                  , stop_time="11:59"
                  , stopAMPM="PM"
                  )

        self.assertEqual( event.Title(), 'title' )
        self.assertEqual( event.Description(), 'description' )
        self.assertEqual( event.Subject(), ( 'eventType', ), event.Subject() )
        self.assertEqual( event.effective_date, None )
        self.assertEqual( event.expiration_date, None )
        self.assertEqual( event.end(), DateTime('1999/12/31 23:59') )
        self.assertEqual( event.start(), DateTime('1999/05/01 00:00') )
        self.failIf( event.contact_name )

    def test_puke(self):
        event = self._makeOne('shouldPuke')

        self.assertRaises( DateTime.DateError
                         , event.edit
                         , effectiveDay=31
                         , effectiveMo=2
                         , effectiveYear=1999
                         , start_time="00:00"
                         , startAMPM="AM"
                         )

EVENT_TXT = """\
Title: Test Event
Subject: Foosubject
Contributors: Jim
Effective_date: 2002-01-01T00:00:00Z
Expiration_date: 2009-12-31T00:00:00Z
StartDate: 2006/02/23 18:00
EndDate: 2006/02/23 23:00
Location: Spuds and Suds, River Street, Anytown
Language: French
Rights: Anytown Gazetteer
ContactName: Jim
ContactEmail: jim@example.com
ContactPhone: (888) 555-1212
EventURL: http://www.example.com
Creator: Jim

Fundraiser for disabled goldfish
"""

class EventPUTTests(RequestTest):

    def _makeOne(self, id, *args, **kw):
        from Products.CMFCalendar.Event import Event

        # NullResource.PUT calls the PUT method on the bare object!
        return Event(id, *args, **kw)

    def test_PutWithoutMetadata(self):
        self.REQUEST['BODY'] = ''
        d = self._makeOne('foo')
        d.PUT(self.REQUEST, self.RESPONSE)

        self.assertEqual( d.Title(), '' )
        self.assertEqual( d.Format(), 'text/plain' )
        self.assertEqual( d.Description(), '' )
        self.assertEqual( d.Subject(), () )
        self.assertEqual( d.Contributors(), () )
        self.assertEqual( d.EffectiveDate('UTC'), 'None' )
        self.assertEqual( d.ExpirationDate('UTC'), 'None' )
        self.assertEqual( d.Language(), '' )
        self.assertEqual( d.Rights(), '' )
        self.assertEqual( d.location, '' )
        self.assertEqual( d.contact_name, '' )
        self.assertEqual( d.contact_email, '' )
        self.assertEqual( d.contact_phone, '' )
        self.assertEqual( d.event_url, '' )

    def test_PutWithMetadata(self):
        self.REQUEST['BODY'] = EVENT_TXT
        self.REQUEST.environ['CONTENT_TYPE'] = 'text/html'
        d = self._makeOne('foo')
        d.PUT(self.REQUEST, self.RESPONSE)

        self.assertEqual( d.Title(), 'Test Event' )
        self.assertEqual( d.Format(), 'text/html' )
        self.assertEqual( d.Description().strip()
                        , 'Fundraiser for disabled goldfish' 
                        )
        self.assertEqual( d.Subject(), ('Foosubject',) )
        self.assertEqual( d.Contributors(), ('Jim',) )
        self.assertEqual( d.EffectiveDate('UTC'), '2002-01-01 00:00:00' )
        self.assertEqual( d.ExpirationDate('UTC'), '2009-12-31 00:00:00' )
        self.assertEqual( d.Language(), 'French' )
        self.assertEqual( d.Rights(), 'Anytown Gazetteer' )
        self.assertEqual( d.location, 'Spuds and Suds, River Street, Anytown' )
        self.assertEqual( d.contact_name, 'Jim' )
        self.assertEqual( d.contact_email, 'jim@example.com' )
        self.assertEqual( d.contact_phone, '(888) 555-1212' )
        self.assertEqual( d.event_url, 'http://www.example.com' )
        self.assertEqual( d.start(), DateTime('2006/02/23 18:00') )
        self.assertEqual( d.end(), DateTime('2006/02/23 23:00') )


def test_suite():
    return TestSuite((
        makeSuite(TestEvent),
        makeSuite(EventPUTTests),
        ))

if __name__ == '__main__':
    main(defaultTest='test_suite')
