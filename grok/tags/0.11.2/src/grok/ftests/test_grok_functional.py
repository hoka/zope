import re
import unittest
import grok
import os.path

from pkg_resources import resource_listdir
from zope.testing import doctest, renormalizing
from zope.app.testing.functional import (HTTPCaller, getRootFolder,
                                         FunctionalTestSetup, sync, ZCMLLayer)

ftesting_zcml = os.path.join(os.path.dirname(grok.__file__), 'ftesting.zcml')
GrokFunctionalLayer = ZCMLLayer(ftesting_zcml, __name__, 'GrokFunctionalLayer')

def setUp(test):
    FunctionalTestSetup().setUp()

def tearDown(test):
    FunctionalTestSetup().tearDown()

checker = renormalizing.RENormalizing([
    # Accommodate to exception wrapping in newer versions of mechanize
    (re.compile(r'httperror_seek_wrapper:', re.M), 'HTTPError:'),
    ])

def http_call(method, path, data=None, **kw):
    """Function to help make RESTful calls.

    method - HTTP method to use
    path - testbrowser style path
    data - (body) data to submit
    kw - any request parameters
    """
    
    if path.startswith('http://localhost'):
        path = path[len('http://localhost'):]
    request_string = '%s %s HTTP/1.1\n' % (method, path)
    for key, value in kw.items():
        request_string += '%s: %s\n' % (key, value)
    if data is not None:
        request_string += '\r\n'
        request_string += data
    return HTTPCaller()(request_string, handle_errors=False)

def suiteFromPackage(name):
    files = resource_listdir(__name__, name)
    suite = unittest.TestSuite()
    for filename in files:
        if not filename.endswith('.py'):
            continue
        if filename == '__init__.py':
            continue

        dottedname = 'grok.ftests.%s.%s' % (name, filename[:-3])
        test = doctest.DocTestSuite(
            dottedname, setUp=setUp, tearDown=tearDown,
            checker=checker,
            extraglobs=dict(http=HTTPCaller(),
                            http_call=http_call,
                            getRootFolder=getRootFolder,
                            sync=sync),
            optionflags=(doctest.ELLIPSIS+
                         doctest.NORMALIZE_WHITESPACE+
                         doctest.REPORT_NDIFF)
            )
        test.layer = GrokFunctionalLayer

        suite.addTest(test)
    return suite

def test_suite():
    suite = unittest.TestSuite()
    for name in ['view', 'staticdir', 'xmlrpc', 'traversal', 'form', 'url',
                 'security', 'utility', 'catalog', 'admin', 'site', 'rest']:
        suite.addTest(suiteFromPackage(name))

    # this test cannot follow the normal testing pattern, as the
    # bug it tests for is only exposed in the context of a doctest
    grok_component = doctest.DocFileSuite('grok_component.txt')
    grok_component.layer = GrokFunctionalLayer
    suite.addTest(grok_component)
    
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
