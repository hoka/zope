Bobo
====

Bobo is a light-weight framework for creating WSGI web applications.

Its goal is to be easy to use and remember.

It addresses 2 problems:

- Mapping URLs to objects

- Calling objects to generate HTTP responses

Bobo doesn't have a templating language, a database integration layer,
or a number of other features that are better provided by WSGI
middle-ware or application-specific libraries.

Bobo builds on other frameworks, most notably WSGI and WebOb.

To learn more. visit: http://bobo.digicool.com

Change History
==============

0.2.2 2010-01-19
----------------

Bugs fixed:

- An intended optmization to cache resource decorator computations
  didn't work, making request handling slower than it should have
  been.

- URLs were sometimes treated as if they had extra slashes when
  traversing subroutes.

- boboserver.File must explicitly open files in binary mode, which is not
  the default on Windows.

0.2.1 2009-06-16
----------------

Packaging update to update documentation.

0.2.0 2009-05-26
----------------

Initial Public Release
