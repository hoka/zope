import unittest
import doctest

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('example1.txt'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
