##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Test the ZServer configuration machinery."""

import cStringIO as StringIO
import os
import tempfile
import unittest

import ZConfig
import ZServer.datatypes


TEMPFILENAME = tempfile.mktemp()


class ZServerConfigurationTestCase(unittest.TestCase):
    schema = None

    def get_schema(self):
        if self.schema is None:
            sio = StringIO.StringIO("""
            <schema>
              <import package='ZServer'/>
              <multisection name='*' type='server' attribute='servers'/>
            </schema>
            """)
            schema = ZConfig.loadSchemaFile(sio)
            ZServerConfigurationTestCase.schema = schema
        return self.schema

    def load_factory(self, text):
        conf, xxx = ZConfig.loadConfigFile(self.get_schema(),
                                           StringIO.StringIO(text))
        self.assertEqual(len(conf.servers), 1)
        return conf.servers[0]

    def load_unix_domain_factory(self, text):
        fn = TEMPFILENAME
        f = open(fn, 'w')
        f.close()
        try:
            factory = self.load_factory(text % fn)
        finally:
            os.unlink(fn)
        self.assert_(factory.host is None)
        self.assert_(factory.port is None)
        self.assertEqual(factory.path, fn)
        return factory

    def test_http_factory(self):
        factory = self.load_factory("""\
            <http-server>
              address 81
              force-connection-close true
              webdav-source-clients cadaever
            </http-server>
            """)
        self.assert_(isinstance(factory,
                                ZServer.datatypes.HTTPServerFactory))
        self.assert_(factory.force_connection_close)
        self.assertEqual(factory.host, '')
        self.assertEqual(factory.port, 81)
        self.assertEqual(factory.webdav_source_clients, "cadaever")
        self.check_prepare(factory)
        server = factory.create()
        self.assertEqual(server.ip, '127.0.0.1')
        self.assertEqual(server.port, 9381)
        server.close()

    def test_webdav_source_factory(self):
        factory = self.load_factory("""\
            <webdav-source-server>
              address 82
              force-connection-close true
            </webdav-source-server>
            """)
        self.assert_(isinstance(factory,
                                ZServer.datatypes.WebDAVSourceServerFactory))
        self.assert_(factory.force_connection_close)
        self.assertEqual(factory.host, '')
        self.assertEqual(factory.port, 82)
        self.check_prepare(factory)
        server = factory.create()
        self.assertEqual(server.ip, '127.0.0.1')
        self.assertEqual(server.port, 9382)
        server.close()

    def test_pcgi_factory(self):
        factory = self.load_unix_domain_factory("""\
            <persistent-cgi>
              path %s
            </persistent-cgi>
            """)
        self.assert_(isinstance(factory,
                                ZServer.datatypes.PCGIServerFactory))

    def test_fcgi_factory(self):
        factory = self.load_factory("""\
            <fast-cgi>
              address 83
            </fast-cgi>
            """)
        self.assert_(isinstance(factory,
                                ZServer.datatypes.FCGIServerFactory))
        self.assertEqual(factory.host, '')
        self.assertEqual(factory.port, 83)
        self.assertEqual(factory.path, None)
        self.check_prepare(factory)
        factory.create().close()
        factory = self.load_unix_domain_factory("""\
            <fast-cgi>
              address %s
            </fast-cgi>
            """)
        self.assert_(isinstance(factory,
                                ZServer.datatypes.FCGIServerFactory))
        self.check_prepare(factory)

    def test_ftp_factory(self):
        factory = self.load_factory("""\
            <ftp-server>
              address 84
            </ftp-server>
            """)
        self.assert_(isinstance(factory,
                                ZServer.datatypes.FTPServerFactory))
        self.assertEqual(factory.host, '')
        self.assertEqual(factory.port, 84)
        self.check_prepare(factory)
        factory.create().close()

    def test_monitor_factory(self):
        factory = self.load_factory("""\
            <monitor-server>
              address 85
            </monitor-server>
            """)
        self.assert_(isinstance(factory,
                                ZServer.datatypes.MonitorServerFactory))
        self.assertEqual(factory.host, '')
        self.assertEqual(factory.port, 85)
        self.check_prepare(factory)
        factory.create().close()

    def test_icp_factory(self):
        factory = self.load_factory("""\
            <icp-server>
              address 86
            </icp-server>
            """)
        self.assert_(isinstance(factory,
                                ZServer.datatypes.ICPServerFactory))
        self.assertEqual(factory.host, '')
        self.assertEqual(factory.port, 86)
        self.check_prepare(factory)
        factory.create().close()

    def check_prepare(self, factory):
        port = factory.port
        o = object()
        factory.prepare("127.0.0.1", o, "module",
                        {"key": "value"}, portbase=9300)
        self.assert_(factory.dnsresolver is o)
        self.assertEqual(factory.module, "module")
        self.assertEqual(factory.cgienv.items(), [("key", "value")])
        if port is None:
            self.assert_(factory.host is None)
            self.assert_(factory.port is None)
        else:
            self.assertEqual(factory.host, "127.0.0.1")
            self.assertEqual(factory.port, 9300 + port)


def test_suite():
    return unittest.makeSuite(ZServerConfigurationTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
