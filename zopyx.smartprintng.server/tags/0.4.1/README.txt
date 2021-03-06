zopyx.smartprintng.server
=========================

A repoze.bfg based server implementation for the SmartPrintNG framework.

The SmartPrintNG server is part of the SmartPrintNG web-to-print solution
of ZOPYX.

Installation
============

- create an virtualenv environment (Python 2,4, 2.5 or 2.6)::

    virtualenv --no-site-packages .

- install ``repoze.bfg`` (by installing ``repoze.bfg.xmlrpc`` having ``repoze.bfg``
  as a dependency) ::

    bin/easy_install -i http://dist.repoze.org/bfgsite/simple repoze.bfg.xmlrpc

- install the SmartPrintNG server::

    bin/easy_install zopyx.smartprintng.server

- create a ``server.ini`` configuration file (and change according to your needs)::

    [DEFAULT]
    debug = true

    [app:main]
    use = egg:zopyx.smartprintng.server#app
    reload_templates = true
    debug_authorization = false
    debug_notfound = false

    [server:main]
    use = egg:Paste#http
    host = 127.0.0.1
    port = 6543

- start the server::

    bin/paster serve server.ini 

XMLRPC API
==========

The SmartPrintNG server exposes several methods through XMLRPC::

    def convertZIP(zip_archive, converter_name):
        """ 'zip_archive' is ZIP archive (encoded as base-64 byte string).
            The archive must contain exactly *one* HTML file to be converted
            including all related resources like stylesheets and images.
            All files must be stored flat within the archive (no subfolders).
            All references to externals resources like the 'src' attribute
            of the IMG tag or references to the stylesheet(s) must use
            relative paths. The method returns the converted output file
            also as base64-encoded ZIP archive.
        """

    def convertZIPEmail(context, zip_archive, converter_name='pdf-prince', 
                        sender=None, recipient=None, subject=None, body=None):
        """ Similar to convertZIP() except that this method will send the 
            converted output document to a recipient by email. 'subject' and
            'body' parameters *must* be utf-8 encoded.
        """

    def availableConverters():
        """ Returns a list of available converter names on the 
            SmartPrintNG backend.
        """

    def ping():
        """ says 'pong' - or something similar """

Email configuration
===================

For using the email support through the ``convertZIPEmail()`` the email server must be
configured through a dedicated configuration file. An ``email.ini`` may look like this::

    [mail]
    hostname = smtp.gmail.com
    username = some_username
    password = some_password
    force_tls = False
    no_tls = False

You have to pass the name of the email configuration file to ``paster`` when starting
then server::

    bin/paster serve server.ini mail_config=/path/to/email.ini



Support
=======

Support for SmartPrintNG server is currently only available on a project basis.


Contact
=======

| ZOPYX Ltd. & Co. KG
| c/o Andreas Jung, 
| Charlottenstr. 37/1
| D-72070 Tuebingen, Germany
| E-mail: info at zopyx dot com
| Web: http://www.zopyx.com


