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
"""Highest-level classes to support filesystem synchronization:

class Network -- handle network connection
class FSSync  -- implement various commands (checkout, commit etc.)

$Id: fssync.py,v 1.25 2003/05/25 06:10:03 gvanrossum Exp $
"""

import os
import sys
import base64
import shutil
import urllib
import filecmp
import htmllib
import httplib
import tempfile
import urlparse
import formatter

from StringIO import StringIO

from os.path import exists, isfile, isdir, islink
from os.path import dirname, basename, split, join
from os.path import realpath, normcase, normpath

from zope.fssync.metadata import Metadata
from zope.fssync.fsmerger import FSMerger
from zope.fssync.fsutil import Error
from zope.fssync import fsutil
from zope.fssync.snarf import Snarfer, Unsnarfer

class Network(object):

    """Handle network communication.

    This class has various methods for managing the root url (which is
    stored in a file @@Zope/Root) and has a method to send an HTTP(S)
    request to the root URL, expecting a snarf file back (that's all the
    application needs).

    Public instance variables:

    rooturl     -- full root url, e.g. 'http://user:passwd@host:port/path'
    roottype    -- 'http' or 'https'
    user_passwd -- 'user:passwd'
    host_port   -- 'host:port'
    rootpath    -- '/path'
    """

    def __init__(self, rooturl=None):
        """Constructor.  Optionally pass the root url."""
        self.setrooturl(rooturl)

    def loadrooturl(self, target):
        """Load the root url for the given target.

        This calls findrooturl() to find the root url for the target,
        and then calls setrooturl() to set it.  If self.findrooturl()
        can't find a root url, Error() is raised.
        """
        rooturl = self.findrooturl(target)
        if not rooturl:
            raise Error("can't find root url for target", target)
        self.setrooturl(rooturl)

    def saverooturl(self, target):
        """Save the root url in the target's @@Zope directory.

        This writes the file <target>/@@Zope/Root; the directory
        <target>/@@Zope must already exist.
        """
        if self.rooturl:
            self.writefile(self.rooturl + "\n",
                           join(target, "@@Zope", "Root"))

    def findrooturl(self, target):
        """Find the root url for the given target.

        This looks in <target>/@@Zope/Root, and then in the
        corresponding place for target's parent, and then further
        ancestors, until the filesystem root is reached.

        If no root url is found, return None.
        """
        dir = realpath(target)
        while dir:
            zopedir = join(dir, "@@Zope")
            rootfile = join(zopedir, "Root")
            try:
                data = self.readfile(rootfile)
            except IOError:
                pass
            else:
                data = data.strip()
                if data:
                    return data
            head, tail = split(dir)
            if tail in fsutil.unwanted:
                break
            dir = head
        return None

    def setrooturl(self, rooturl):
        """Set the root url.

        If the argument is None or empty, self.rooturl and all derived
        instance variables are set to None.  Otherwise, self.rooturl
        is set to the argument the broken-down root url is stored in
        the other instance variables.
        """
        if not rooturl:
            rooturl = roottype = rootpath = user_passwd = host_port = None
        else:
            roottype, rest = urllib.splittype(rooturl)
            if roottype not in ("http", "https"):
                raise Error("root url must be 'http' or 'https'", rooturl)
            if roottype == "https" and not hasattr(httplib, "HTTPS"):
                raise Error("https not supported by this Python build")
            netloc, rootpath = urllib.splithost(rest)
            if not rootpath:
                rootpath = "/"
            user_passwd, host_port = urllib.splituser(netloc)

        self.rooturl = rooturl
        self.roottype = roottype
        self.rootpath = rootpath
        self.user_passwd = user_passwd
        self.host_port = host_port

    def readfile(self, file, mode="r"):
        # Internal helper to read a file
        f = open(file, mode)
        try:
            return f.read()
        finally:
            f.close()

    def writefile(self, data, file, mode="w"):
        # Internal helper to write a file
        f = open(file, mode)
        try:
            f.write(data)
        finally:
            f.close()

    def httpreq(self, path, view, datafp=None,
                content_type="application/x-snarf"):
        """Issue an HTTP or HTTPS request.

        The request parameters are taken from the root url, except
        that the requested path is constructed by concatenating the
        path and view arguments.

        If the optional 'datafp' argument is not None, it should be a
        seekable stream from which the input document for the request
        is taken.  In this case, a POST request is issued, and the
        content-type header is set to the 'content_type' argument,
        defaulting to 'application/x-snarf'.  Otherwise (if datafp is
        None), a GET request is issued and no input document is sent.

        If the request succeeds and returns a document whose
        content-type is 'application/x-snarf', the return value is a tuple
        (fp, headers) where fp is a non-seekable stream from which the
        return document can be read, and headers is a case-insensitive
        mapping giving the response headers.

        If the request returns an HTTP error, the Error exception is
        raised.  If it returns success (error code 200) but the
        content-type of the result is not 'application/x-snarf', the Error
        exception is also raised.  In these error cases, if the result
        document's content-type is a text type (anything starting with
        'text/'), the text of the result document is included in the
        Error exception object; in the specific case that the type is
        text/html, HTML formatting is removed using a primitive
        formatter.

        XXX This doesn't support proxies or redirect responses.
        """
        assert self.rooturl
        if not path.endswith("/"):
            path += "/"
        path += view
        if self.roottype == "https":
            h = httplib.HTTPS(self.host_port)
        else:
            h = httplib.HTTP(self.host_port)
        if datafp is None:
            h.putrequest("GET", path)
            filesize = 0   # for PyChecker
        else:
            datafp.seek(0, 2)
            filesize = datafp.tell()
            datafp.seek(0)
            h.putrequest("POST", path)
            h.putheader("Content-type", content_type)
            h.putheader("Content-length", str(filesize))
        if self.user_passwd:
            auth = base64.encodestring(self.user_passwd).strip()
            h.putheader('Authorization', 'Basic %s' % auth)
        h.putheader("Host", self.host_port)
        h.endheaders()
        if datafp is not None:
            nbytes = 0
            while True:
                buf = datafp.read(8192)
                if not buf:
                    break
                nbytes += len(buf)
                h.send(buf)
            assert nbytes == filesize
        errcode, errmsg, headers = h.getreply()
        fp = h.getfile()
        if errcode != 200:
            raise Error("HTTP error %s (%s); error document:\n%s",
                        errcode, errmsg,
                        self.slurptext(fp, headers))
        if headers["Content-type"] != "application/x-snarf":
            raise Error(self.slurptext(fp, headers))
        return fp, headers

    def slurptext(self, fp, headers):
        """Helper to read the result document.

        This removes the formatting from a text/html document; returns
        other text documents as-is; and for non-text documents,
        returns just a string giving the content-type.
        """
        data = fp.read()
        ctype = headers["Content-type"]
        if ctype == "text/html":
            s = StringIO()
            f = formatter.AbstractFormatter(formatter.DumbWriter(s))
            p = htmllib.HTMLParser(f)
            p.feed(data)
            p.close()
            return s.getvalue().strip()
        if ctype.startswith("text/"):
            return data.strip()
        return "Content-type: %s" % ctype

class FSSync(object):

    def __init__(self, metadata=None, network=None, rooturl=None):
        if metadata is None:
            metadata = Metadata()
        if network is None:
            network = Network()
        self.metadata = metadata
        self.network = network
        self.network.setrooturl(rooturl)
        self.fsmerger = FSMerger(self.metadata, self.reporter)

    def checkout(self, target):
        rootpath = self.network.rootpath
        if not rootpath:
            raise Error("root url not set")
        if self.metadata.getentry(target):
            raise Error("target already registered", target)
        if exists(target) and not isdir(target):
            raise Error("target should be a directory", target)
        fsutil.ensuredir(target)
        i = rootpath.rfind("/")
        tail = rootpath[i+1:]
        tail = tail or "root"
        fp, headers = self.network.httpreq(rootpath, "@@toFS.snarf")
        try:
            self.merge_snarffile(fp, target, tail)
        finally:
            fp.close()
        self.network.saverooturl(target)

    def multiple(self, args, method, *more):
        if not args:
            args = [os.curdir]
        for target in args:
            if self.metadata.getentry(target):
                method(target, *more)
            else:
                names = self.metadata.getnames(target)
                if not names:
                    method(target) # Will raise an exception
                else:
                    for name in names:
                        method(join(target, name), *more)

    def commit(self, target, note="fssync"):
        entry = self.metadata.getentry(target)
        if not entry:
            raise Error("nothing known about", target)
        self.network.loadrooturl(target)
        path = entry["path"]
        snarffile = tempfile.mktemp(".snf")
        head, tail = split(realpath(target))
        try:
            f = open(snarffile, "wb")
            try:
                snf = Snarfer(f)
                snf.add(join(head, tail), tail)
                snf.addtree(join(head, "@@Zope"), "@@Zope/")
            finally:
                f.close()
            infp = open(snarffile, "rb")
            view = "@@fromFS.snarf?note=%s" % urllib.quote(note)
            try:
                outfp, headers = self.network.httpreq(path, view, infp)
            finally:
                infp.close()
        finally:
            pass
            if isfile(snarffile):
                os.remove(snarffile)
        try:
            self.merge_snarffile(outfp, head, tail)
        finally:
            outfp.close()

    def update(self, target):
        entry = self.metadata.getentry(target)
        if not entry:
            raise Error("nothing known about", target)
        self.network.loadrooturl(target)
        head, tail = fsutil.split(target)
        path = entry["path"]
        fp, headers = self.network.httpreq(path, "@@toFS.snarf")
        try:
            self.merge_snarffile(fp, head, tail)
        finally:
            fp.close()

    def merge_snarffile(self, fp, localdir, tail):
        uns = Unsnarfer(fp)
        tmpdir = tempfile.mktemp()
        try:
            os.mkdir(tmpdir)
            uns.unsnarf(tmpdir)
            self.fsmerger.merge(join(localdir, tail), join(tmpdir, tail))
            self.metadata.flush()
            print "All done."
        finally:
            if isdir(tmpdir):
                shutil.rmtree(tmpdir)

    def reporter(self, msg):
        if msg[0] not in "/*":
            print msg

    def diff(self, target, mode=1, diffopts=""):
        assert mode == 1, "modes 2 and 3 are not yet supported"
        entry = self.metadata.getentry(target)
        if not entry:
            raise Error("diff target '%s' doesn't exist", target)
        if "flag" in entry:
            raise Error("diff target '%s' is added or deleted", target)
        if isdir(target):
            self.dirdiff(target, mode, diffopts)
            return
        if not isfile(target):
            raise Error("diff target '%s' is file nor directory", target)
        orig = fsutil.getoriginal(target)
        if not isfile(orig):
            raise Error("can't find original for diff target '%s'", target)
        if filecmp.cmp(target, orig, shallow=False):
            return
        print "Index:", target
        sys.stdout.flush()
        cmd = ("diff %s %s %s" % (diffopts, quote(orig), quote(target)))
        os.system(cmd)

    def dirdiff(self, target, mode=1, diffopts=""):
        assert isdir(target)
        names = self.metadata.getnames(target)
        for name in names:
            t = join(target, name)
            e = self.metadata.getentry(t)
            if e and "flag" not in e:
                self.diff(t, mode, diffopts)

    def add(self, path):
        if not exists(path):
            raise Error("nothing known about '%s'", path)
        entry = self.metadata.getentry(path)
        if entry:
            raise Error("path '%s' is already registered", path)
        head, tail = fsutil.split(path)
        pentry = self.metadata.getentry(head)
        if not pentry:
            raise Error("can't add '%s': its parent is not registered", path)
        if "path" not in pentry:
            raise Error("can't add '%s': its parent has no 'path' key", path)
        zpath = pentry["path"]
        if not zpath.endswith("/"):
            zpath += "/"
        zpath += tail
        entry["path"] = zpath
        entry["flag"] = "added"
        if isdir(path):
            entry["type"] = entry["factory"] = "zope.app.content.folder.Folder"
        self.metadata.flush()

    def remove(self, path):
        if exists(path):
            raise Error("'%s' still exists", path)
        entry = self.metadata.getentry(path)
        if not entry:
            raise Error("nothing known about '%s'", path)
        zpath = entry.get("path")
        if not zpath:
            raise Error("can't remote '%s': its zope path is unknown", path)
        if entry.get("flag") == "added":
            entry.clear()
        else:
            entry["flag"] = "removed"
        self.metadata.flush()

    def status(self, target, descend_only=False):
        entry = self.metadata.getentry(target)
        flag = entry.get("flag")
        if isfile(target):
            if not entry:
                if not self.fsmerger.ignore(target):
                    print "?", target
            elif flag == "added":
                print "A", target
            elif flag == "removed":
                print "R(reborn)", target
            else:
                original = fsutil.getoriginal(target)
                if isfile(original):
                    if filecmp.cmp(target, original):
                        print "=", target
                    else:
                        print "M", target
                else:
                    print "M(lost-original)", target
        elif isdir(target):
            pname = join(target, "")
            if not entry:
                if not descend_only and not self.fsmerger.ignore(target):
                    print "?", pname
            elif flag == "added":
                print "A", pname
            elif flag == "removed":
                print "R(reborn)", pname
            else:
                print "/", pname
            if entry:
                # Recurse down the directory
                namesdir = {}
                for name in os.listdir(target):
                    ncname = normcase(name)
                    if ncname != fsutil.nczope:
                        namesdir[ncname] = name
                for name in self.metadata.getnames(target):
                    ncname = normcase(name)
                    namesdir[ncname] = name
                ncnames = namesdir.keys()
                ncnames.sort()
                for ncname in ncnames:
                    self.status(join(target, namesdir[ncname]))
        elif exists(target):
            if not entry:
                if not self.fsmerger.ignore(target):
                    print "?", target
            elif flag:
                print flag[0].upper() + "(unrecognized)", target
            else:
                print "M(unrecognized)", target
        else:
            if not entry:
                print "nonexistent", target
            elif flag == "removed":
                print "R", target
            elif flag == "added":
                print "A(lost)", target
            else:
                print "lost", target
        annotations = fsutil.getannotations(target)
        if isdir(annotations):
            self.status(annotations, True)
        extra = fsutil.getextra(target)
        if isdir(extra):
            self.status(extra, True)

def quote(s):
    """Helper to put quotes around arguments passed to shell if necessary."""
    if os.name == "posix":
        meta = "\\\"'*?[&|()<>`#$; \t\n"
    else:
        meta = " "
    needquotes = False
    for c in meta:
        if c in s:
            needquotes = True
            break
    if needquotes:
        if os.name == "posix":
            # use ' to quote, replace ' by '"'"'
            s = "'" + s.replace("'", "'\"'\"'") + "'"
        else:
            # (Windows) use " to quote, replace " by ""
            s = '"' + s.replace('"', '""') + '"'
    return s
