# *-* coding: iso-8859-15 *-*

##########################################################################
# zopyx.smartprintng.client - client library for the SmartPrintNG server
# (C) 2009, ZOPYX Ltd & Co. KG, Tuebingen, Germany
##########################################################################

import os
import sys
import base64
import time
import xmlrpclib
import zipfile
import tempfile
import zipfile
import warnings


class Proxy(object):

    def __init__(self, host='localhost', port=6543, username='', password=''):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.setOutputDirectory(os.path.join(tempfile.gettempdir(), 'smartprintng_client', str(time.time())))

    def setOutputDirectory(self, output_directory):
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        self.output_directory = output_directory

    def _makeZipFromDirectory(self, directory):
        """ Generate a ZIP file from a directory containing all its
            contents. Returns the filename of the generated ZIP file.
        """

        directory = os.path.abspath(directory)
        zip_filename = tempfile.mktemp()
        ZF = zipfile.ZipFile(zip_filename, 'w')
        for dirname, dirnames, filenames in os.walk(directory):
            for fname in filenames:
                arcname = os.path.join(dirname, fname).replace(directory + os.path.sep, '')
                fullname = os.path.abspath(os.path.join(dirname, fname))
                ZF.write(fullname, arcname)
        ZF.close()
        return zip_filename

    def _authenticate(self):
        server = xmlrpclib.ServerProxy('http://%s:%d/authenticate' % (self.host, self.port))
        return server(self.username, self.password)

    def ping(self):
        server = xmlrpclib.ServerProxy('http://%s:%d/ping' % (self.host, self.port))
        return server()

    def availableConverters(self):
        server = xmlrpclib.ServerProxy('http://%s:%d/availableConverters' % (self.host, self.port))
        return server()

    def convertZIP2(self, dirname, converter_name='pdf-prince', workdir=None):
        """ XMLRPC client to SmartPrintNG server """

        auth_token = self._authenticate()

        zip_filename = self._makeZipFromDirectory(dirname)
        server = xmlrpclib.ServerProxy('http://%s:%d/convertZIP' % (self.host, self.port))
        zip_data = server(auth_token,
                          base64.encodestring(file(zip_filename, 'rb').read()),
                          converter_name)

        # and receive the conversion result as base64 encoded ZIP archive
        # (it will contain only *one* file)
        zip_temp = tempfile.mktemp()
        file(zip_temp, 'wb').write(base64.decodestring(zip_data))

        result = dict()
        ZF = zipfile.ZipFile(zip_temp, 'r')
        for name in ZF.namelist():
            fullname = os.path.join(workdir or self.output_directory, os.path.basename(name))
            file(fullname, 'wb').write(ZF.read(name))
            if name.startswith('output.'):
                result['output_filename'] = fullname
            elif name.startswith('conversion-output'):
                result['conversion_output'] = fullname
        ZF.close()
        os.unlink(zip_filename)
        os.unlink(zip_temp)
        return result

    def convertZIPandRedirect(self, dirname, converter_name='pdf-prince', prefix=None):
        """ XMLRPC client to SmartPrintNG server """

        # Authenticate first
        auth_token = self._authenticate()

        zip_filename = self._makeZipFromDirectory(dirname)
        server = xmlrpclib.ServerProxy('http://%s:%d/convertZIPandRedirect' % (self.host, self.port))
        location = server(auth_token,
                          base64.encodestring(file(zip_filename, 'rb').read()),
                          converter_name,
                          prefix)
        os.unlink(zip_filename)
        return location

    def convertZIPEmail(self, dirname, converter_name='pdf-prince', 
                        sender=None, recipients=None, subject=None, body=None):

        # Authenticate first
        auth_token = self._authenticate()

        zip_filename = self._makeZipFromDirectory(dirname)
        server = xmlrpclib.ServerProxy('http://%s:%d/convertZIPEmail' % (self.host, self.port))
        result = server.convertZIPEmail(auth_token,
                                        base64.encodestring(file(zip_filename, 'rb').read()),
                                        converter_name,
                                        sender,
                                        recipients,
                                        subject,
                                        body)
        return result


if __name__ == '__main__':
    # usage: convertZIP <dirname>

    proxy = Proxy(host='localhost', port=6543)
    print proxy.ping()
    print proxy.availableConverters()
    print proxy.convertZIP(sys.argv[1])
    print proxy.convertZIP2(sys.argv[1])
#    print proxy.convertZIPEmail(sys.argv[1], 
#                                sender='foo@bar.org', 
#                                recipients='foo@bar.org', 
#                                subject=unicode('���', 'latin1').encode('utf-8'),
#                                body=unicode('���', 'latin1').encode('utf-8'))

