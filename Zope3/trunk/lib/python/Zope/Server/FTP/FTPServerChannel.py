##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""

$Id: FTPServerChannel.py,v 1.3 2002/07/19 18:07:41 shane Exp $
"""

import posixpath
import stat
import sys
import socket
import time

from Zope.Server.LineReceiver.LineServerChannel import LineServerChannel
from FTPStatusMessages import status_msgs
from OSEmulators import ls_longify

from IFTPCommandHandler import IFTPCommandHandler
from PassiveAcceptor import PassiveAcceptor
from RecvChannel import RecvChannel
from XmitChannel import XmitChannel, ApplicationXmitStream
from Zope.Server.VFS.UsernamePassword import UsernamePassword
from Zope.Exceptions import Unauthorized


class FTPServerChannel(LineServerChannel):
    """The FTP Server Channel represents a connection to a particular
       client. We can therefore store information here."""

    __implements__ = LineServerChannel.__implements__, IFTPCommandHandler


    # List of commands that are always available
    special_commands = ('cmd_quit', 'cmd_type', 'cmd_noop', 'cmd_user',
                        'cmd_pass')

    # These are the commands that are accessing the filesystem.
    # Since this could be also potentially a longer process, these commands
    # are also the ones that are executed in a different thread.
    thread_commands = ('cmd_appe', 'cmd_cdup', 'cmd_cwd', 'cmd_dele',
                       'cmd_list', 'cmd_nlst', 'cmd_mdtm', 'cmd_mkd',
                       'cmd_pass', 'cmd_retr', 'cmd_rmd', 'cmd_rnfr',
                       'cmd_rnto', 'cmd_size', 'cmd_stor', 'cmd_stru')

    # Define the status messages
    status_messages = status_msgs

    # Define the type of directory listing this server is returning
    system = ('UNIX', 'L8')

    # comply with (possibly troublesome) RFC959 requirements
    # This is necessary to correctly run an active data connection
    # through a firewall that triggers on the source port (expected
    # to be 'L-1', or 20 in the normal case).
    bind_local_minus_one = 0

    restart_position = 0

    type_map = {'a':'ASCII', 'i':'Binary', 'e':'EBCDIC', 'l':'Binary'}

    type_mode_map = {'a':'t', 'i':'b', 'e':'b', 'l':'b'}


    def __init__(self, server, conn, addr, adj=None):
        super(FTPServerChannel, self).__init__(server, conn, addr, adj)

        self.client_addr = (addr[0], 21)

        self.passive_acceptor = None
        self.client_dc = None

        self.transfer_mode = 'a'  # Have to default to ASCII :-|
        self.passive_mode = 0
        self.cwd = '/'
        self._rnfr = None

        self.username = ''
        self.credentials = None

        self.reply('SERVER_READY', self.server.server_name)


    def _getFilesystem(self):
        """Open the filesystem using the current credentials."""
        return self.server.fs_access.open(self.credentials)


    ############################################################
    # Implementation methods for interface
    # Zope.Server.FTP.IFTPCommandHandler

    def cmd_abor(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        if self.client_dc is not None:
            self.client_dc.close('TRANSFER_ABORTED')
        else:
            self.reply('TRANSFER_ABORTED')


    def cmd_appe (self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        return self.cmd_stor(args, 'a')


    def cmd_cdup(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        path = self._generatePath('../')
        if self._getFilesystem().exists(path):
            self.cwd = path
            self.reply('SUCCESS_250', 'CDUP')
        else:
            self.reply('ERR_NO_FILE', path)


    def cmd_cwd(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        path = self._generatePath(args)
        if self._getFilesystem().exists(path):
            self.cwd = path
            self.reply('SUCCESS_250', 'CWD')
        else:
            self.reply('ERR_NO_DIR', path)


    def cmd_dele(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        if not args:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)

        try:
            self._getFilesystem().remove(path)
        except OSError, err:
            self.reply('ERR_DELETE_FILE', str(err))
        else:
            self.reply('SUCCESS_250', 'DELE')


    def cmd_help(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        self.reply('HELP_START')
        self.write('Help goes here somewhen.\r\n')
        self.reply('HELP_END')


    def cmd_list(self, args, long=1):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        args = args.split()
        try:
            s = self.getDirectoryList(args, long)
        except OSError, err:
            self.reply('ERR_NO_LIST', str(err))
            return
        ok_reply = ('OPEN_DATA_CONN', self.type_map[self.transfer_mode])
        cdc = XmitChannel(self, ok_reply)
        self.client_dc = cdc
        try:
            cdc.write(s)
            cdc.close_when_done()
        except OSError, err:
            cdc.close('ERR_NO_LIST', str(err))


    def cmd_mdtm(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        # We simply do not understand this non-standard extension to MDTM
        if len(args.split()) > 1:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)
        if not self._getFilesystem().isfile(path):
            self.reply('ERR_IS_NOT_FILE', path)
        else:
            mtime = time.gmtime(
                self._getFilesystem().stat(path)[stat.ST_MTIME])
            self.reply('FILE_DATE', (mtime[0], mtime[1], mtime[2],
                                     mtime[3], mtime[4], mtime[5]) )


    def cmd_mkd(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        if not args:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)
        try:
            self._getFilesystem().mkdir(path)
        except OSError, err:
            self.reply('ERR_CREATE_DIR', str(err))
        else:
            self.reply('SUCCESS_257', 'MKD')


    def cmd_mode(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        if len(args) == 1 and args in 'sS':
            self.reply('MODE_OK')
        else:
            self.reply('MODE_UNKNOWN')


    def cmd_nlst(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        self.cmd_list(args, 0)


    def cmd_noop(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        self.reply('SUCCESS_200', 'NOOP')


    def cmd_pass(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        self.authenticated = 0
        password = args
        credentials = UsernamePassword(self.username, password)
        try:
            self.server.fs_access.authenticate(credentials)
        except Unauthorized:
            self.reply('LOGIN_MISMATCH')
            self.close_when_done()
        else:
            self.credentials = credentials
            self.authenticated = 1
            self.reply('LOGIN_SUCCESS')


    def cmd_pasv(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        pc = self.newPassiveAcceptor()
        self.client_dc = None
        port = pc.addr[1]
        ip_addr = pc.control_channel.getsockname()[0]
        self.reply('PASV_MODE_MSG', (','.join(ip_addr.split('.')),
                                     port/256,
                                     port%256 ) )


    def cmd_port(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'

        info = args.split(',')
        ip = '.'.join(info[:4])
        port = int(info[4])*256 + int(info[5])
        # how many data connections at a time?
        # I'm assuming one for now...
        # XXX: we should (optionally) verify that the
        # ip number belongs to the client.  [wu-ftpd does this?]
        self.client_addr = (ip, port)
        self.reply('SUCCESS_200', 'PORT')


    def cmd_pwd(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        self.reply('ALREADY_CURRENT', self.cwd)


    def cmd_quit(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        self.reply('GOODBYE')
        self.close_when_done()


    def cmd_retr(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        if not args:
            self.reply('CMD_UNKNOWN', 'RETR')
        path = self._generatePath(args)

        if not self._getFilesystem().isfile(path):
            self.reply('ERR_IS_NOT_FILE', path)
            return

        mode = 'r' + self.type_mode_map[self.transfer_mode]
        start = 0
        if self.restart_position:
            start = self.restart_position
            self.restart_position = 0

        ok_reply = (
            'OPEN_CONN', (self.type_map[self.transfer_mode], path) )
        cdc = XmitChannel(self, ok_reply)
        self.client_dc = cdc
        outstream = ApplicationXmitStream(cdc)

        try:
            self._getFilesystem().readfile(
                path, mode, outstream, start)
            cdc.close_when_done()
        except OSError, err:
            cdc.close('ERR_OPEN_READ', str(err))
        except IOError, err:
            cdc.close('ERR_IO', str(err))


    def cmd_rest(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        try:
            pos = int(args)
        except ValueError:
            self.reply('ERR_ARGS')
            return
        self.restart_position = pos
        self.reply('RESTART_TRANSFER', pos)


    def cmd_rmd(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        if not args:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)
        try:
            self._getFilesystem().rmdir(path)
        except OSError, err:
            self.reply('ERR_DELETE_DIR', str(err))
        else:
            self.reply('SUCCESS_250', 'RMD')


    def cmd_rnfr(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        path = self._generatePath(args)
        if self._getFilesystem().exists(path):
            self._rnfr = path
            self.reply('READY_FOR_DEST')
        else:
            self.reply('ERR_NO_FILE', path)


    def cmd_rnto(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        path = self._generatePath(args)
        if self._rnfr is None:
            self.reply('ERR_RENAME')
        try:
            self._getFilesystem().rename(self._rnfr, path)
        except OSError, err:
            self.reply('ERR_RENAME', (self._rnfr, path, str(err)))
        else:
            self.reply('SUCCESS_250', 'RNTO')
        self._rnfr = None


    def cmd_size(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        path = self._generatePath(args)
        fs = self._getFilesystem()
        if not fs.isfile(path):
            self.reply('ERR_NO_FILE', path)
        else:
            self.reply('FILE_SIZE', fs.stat(path)[stat.ST_SIZE])


    def cmd_stor(self, args, write_mode='w'):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        if not args:
            self.reply('ERR_ARGS')
            return
        path = self._generatePath(args)

        start = 0
        if self.restart_position:
            self.start = self.restart_position
            restart_position = 0
        mode = write_mode + self.type_mode_map[self.transfer_mode]

        try:
            # Verify the file can be opened, but don't open it yet.
            # The actually write should be transactional without
            # holding up the application.
            fs = self._getFilesystem()
            fs.check_writable(path)
        except OSError, err:
            self.reply('ERR_OPEN_WRITE', str(err))
            return
        except IOError, err:
            self.reply('ERR_IO', str(err))
            return
        cdc = RecvChannel(self, (path, mode, start))
        self.client_dc = cdc
        self.reply('OPEN_CONN', (self.type_map[self.transfer_mode], path))
        self.connectDataChannel(cdc)


    def finishedRecv(self, buffer, (path, mode, start)):
        """Called by RecvChannel when the transfer is finished."""
        # Always called in a task.
        try:
            infile = buffer.getfile()
            infile.seek(0)
            self._getFilesystem().writefile(path, mode, infile, start)
        except OSError, err:
            self.reply('ERR_OPEN_WRITE', str(err))
        except IOError, err:
            self.reply('ERR_IO', str(err))
        except:
            self.exception()
        else:
            self.reply('TRANS_SUCCESS')


    def cmd_stru(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        if len(args) == 1 and args in 'fF':
            self.reply('STRU_OK')
        else:
            self.reply('STRU_UNKNOWN')


    def cmd_syst(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        self.reply('SERVER_TYPE', self.system)


    def cmd_type(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        # ascii, ebcdic, image, local <byte size>
        args = args.split()
        t = args[0].lower()
        # no support for EBCDIC
        # if t not in ['a','e','i','l']:
        if t not in ['a','i','l']:
            self.reply('ERR_ARGS')

        elif t == 'l' and (len(args) > 2 and args[2] != '8'):
            self.reply('WRONG_BYTE_SIZE')

        else:
            self.transfer_mode = t
            self.reply('TYPE_SET_OK', self.type_map[t])


    def cmd_user(self, args):
        'See Zope.Server.FTP.IFTPCommandHandler.IFTPCommandHandler'
        self.authenticated = 0
        if len(args) > 1:
            self.username = args
            self.reply('PASS_REQUIRED')
        else:
            self.reply('ERR_ARGS')

    #
    ############################################################

    def _generatePath(self, args):
        """Convert relative paths to absolute paths."""
        # We use posixpath even on non-Posix platforms because we don't want
        # slashes converted to backslashes.
        path = posixpath.join(self.cwd, args)
        return posixpath.normpath(path)


    def newPassiveAcceptor(self):
        # ensure that only one of these exists at a time.
        if self.passive_acceptor is not None:
            self.passive_acceptor.close()
            self.passive_acceptor = None
        self.passive_acceptor = PassiveAcceptor(self)
        return self.passive_acceptor


    def listdir(self, path, long=0):
        """returns a string"""
        path = self._generatePath(path)
        file_list = self._getFilesystem().listdir(path, long)
        if long:
            file_list = map(ls_longify, file_list)
        return ''.join(map(lambda line: line + '\r\n', file_list))


    def getDirectoryList(self, args, long=0):
        # we need to scan the command line for arguments to '/bin/ls'...
        path_args = []
        for arg in args:
            if arg[0] != '-':
                path_args.append (arg)
            else:
                # ignore arguments
                pass
        if len(path_args) < 1:
            dir = '.'
        else:
            dir = path_args[0]

        dir = self._generatePath(dir)
        return self.listdir(dir, long)


    def connectDataChannel(self, cdc):
        pa = self.passive_acceptor
        if pa:
            # PASV mode.
            if pa.ready:
                # a connection has already been made.
                conn, addr = pa.ready
                cdc.set_socket (conn)
                cdc.connected = 1
                self.passive_acceptor.close()
                self.passive_acceptor = None
            # else we're still waiting for a connect to the PASV port.
            # FTP Explorer is known to do this.
        else:
            # not in PASV mode.
            ip, port = self.client_addr
            cdc.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.bind_local_minus_one:
                cdc.bind(('', self.server.port - 1))
            try:
                cdc.connect((ip, port))
            except socket.error, err:
                cdc.close('NO_DATA_CONN')


    def notifyClientDCClosing(self, *reply_args):
        if self.client_dc is not None:
            self.client_dc = None
            if reply_args:
                self.reply(*reply_args)


    def close(self):
        LineServerChannel.close(self)
        # Make sure the client DC gets closed too.
        cdc = self.client_dc
        if cdc is not None:
            self.client_dc = None
            cdc.close()

