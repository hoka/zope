##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Data loader that looks in CVS for content."""

import copy
import os
import posixpath
import re
import shutil
import tempfile
import urllib
import urlparse

from zpkgtools import Error


class CvsLoadingError(Error):
    """Raised when there was some error loading from CVS.

    :Ivariables:
      - `cvsurl`: Parsed cvs: URL object.
      - `exitcode`: Return code of the CVS process.
    """

    def __init__(self, cvsurl, exitcode):
        self.cvsurl = cvsurl
        self.exitcode = exitcode
        Error.__init__(self, ("could not load from %s (cvs exit code %d)"
                              % (cvsurl.getUrl(), exitcode)))


_cvs_url_match = re.compile(
    """
    cvs://(?P<host>[^/]*)
    /(?P<cvsroot>[^:]*)
    (:(?P<path>[^:]*)
    (:(?P<tag>[^:]*))?)?$
    """,
    re.IGNORECASE | re.VERBOSE).match

_repository_url_match = re.compile(
    """
    repository:(?P<path>[^:]*)
    (:(?P<tag>[^:]*))?$
    """,
    re.IGNORECASE | re.VERBOSE).match

def parse(cvsurl):
    m = _cvs_url_match(cvsurl)
    if m is None:
        m = _repository_url_match(cvsurl)
        if m is None:
            raise ValueError("not a valid CVS url")
        return RepositoryUrl(m.group("path"), m.group("tag"))
    host = m.group("host")
    cvsroot = "/" + m.group("cvsroot")
    path = m.group("path")
    tag = m.group("tag") or ""
    username = None
    password = None
    type = None
    if "@" in host:
        userinfo, host = host.split("@", 1)
        if ":" in userinfo:
            username, password = userinfo.split(":", 1)
        else:
            username = userinfo
    if ":" in host:
        host, type = host.split(":", 1)
    return CvsUrl(type, host, cvsroot, path, tag, username, password)


def fromPath(path):
    path = os.path.normpath(path)
    if os.path.isdir(path):
        dirname = path
        basename = ""
    else:
        dirname, basename = os.path.split(path)
    cvsdir = os.path.join(dirname, "CVS")
    tagfile = os.path.join(cvsdir, "Tag")
    if os.path.isfile(tagfile):
        tag = _read_one_line(tagfile)[1:]
    else:
        tag = None
    if basename:
        # The tag may be overridden for specific files; check:
        entries = os.path.join(cvsdir, "Entries")
        if os.path.isfile(entries):
            entries = file(entries, "rU")
            for line in entries:
                parts = line.split("/")
                if (len(parts) >= 6 and
                    os.path.normcase(parts[1]) == os.path.normcase(basename)):
                    tag = parts[5][1:].rstrip() or tag
                    break
    modpath = _read_one_line(os.path.join(cvsdir, "Repository"))
    repo = _read_one_line(os.path.join(cvsdir, "Root"))
    host = ""
    type = username = None
    if repo[:1] == ":":
        parts = repo.split(":")
        type = parts[1]
        host = parts[2]
        cvsroot = parts[3]
    elif ":" in repo:
        host, cvsroot = repo.split(":", 1)
    if "@" in host:
        username, host = host.split("@")
    return CvsUrl(type, host, cvsroot,
                  posixpath.join(modpath, basename),
                  tag, username)


def _read_one_line(filename):
    f = file(filename, "rU")
    try:
        line = f.readline()
    finally:
        f.close()
    return line.rstrip()


class UrlBase:

    def __str__(self):
        return "<%s.%s: %s>" % (self.__class__.__module__,
                                self.__class__.__name__,
                                self.getUrl())


class CvsUrl(UrlBase):
    def __init__(self, type, host, cvsroot, path,
                 tag=None, username=None, password=None):
        assert cvsroot.startswith("/")
        self.type = type or None
        self.host = host or None
        self.cvsroot = cvsroot
        self.path = path
        self.tag = tag or None
        self.username = username or None
        self.password = password or None

    def getCvsRoot(self):
        s = ""
        if self.type:
            s = ":%s:" % self.type
        if self.username:
            s = "%s%s@" % (s, self.username)
        if self.host:
            s = "%s%s:" % (s, self.host)
        return s + self.cvsroot

    def getUrl(self):
        host = self.host or ""
        if self.type:
            host = "%s:%s" % (host, self.type)
        if self.username:
            username = self.username
            if self.password:
                username = "%s:%s" % (username, self.password)
            host = "%s@%s" % (username, host)
        url = "cvs://%s%s:%s" % (host, self.cvsroot, self.path)
        if self.tag:
            url = "%s:%s" % (url, self.tag)
        return url

    def join(self, relurl):
        assert isinstance(relurl, RepositoryUrl)
        cvsurl = copy.copy(self)
        if relurl.path:
            path = posixpath.normpath(relurl.path)
            if path[:1] == "/":
                newpath = path[1:]
            else:
                newpath = posixpath.join(cvsurl.path, relurl.path)
            cvsurl.path = posixpath.normpath(newpath)
        if relurl.tag:
            cvsurl.tag = relurl.tag
        return cvsurl


class RepositoryUrl(UrlBase):

    def __init__(self, path, tag=None):
        self.path = path or None
        self.tag = tag or None

    def getUrl(self):
        url = "repository:" + self.path
        if self.tag:
            url = "%s:%s" % (url, self.tag)
        return url


def open(url, mode="r"):
    if mode[:1] != "r" or "+" in mode:
        raise ValueError("CVS resources can only be opened in read-only mode")
    loader = CvsLoader()
    path = loader.load(url)
    if os.path.isfile(path):
        return FileProxy(path, mode, loader, url)
    # Only files and directories come from CVS, so no need to check
    # for magical directory entries here:
    loader.cleanup()
    raise IOError(errno.EISDIR, "Is a directory", url)


class CvsLoader:

    def __init__(self, tag=None):
        self.tag = tag or None
        self.workdirs = {}  # URL -> (directory, path)

    def cleanup(self):
        """Remove all checkouts that are present."""
        while self.workdirs:
            url, (directory, path) = self.workdirs.popitem()
            if directory:
                shutil.rmtree(directory)

    def load(self, url):
        """Load resource from URL into a temporary location.

        Returns the location of the resource once loaded.
        """
        key = url
        try:
            url = parse(url)
        except ValueError:
            # XXX Hack to make this support file: URLs to ease
            # testing with filesystem-based resources.  There
            # really should be some sort of dispatch mechanism,
            # but we won't do that right now.
            parts = urlparse.urlparse(url)
            if parts[0] == "file" and not parts[1]:
                fn = urllib.url2pathname(parts[2])
                if os.path.exists(fn):
                    return fn
                raise ValueError(
                    "file: URL refers to non-existant resource")
            raise TypeError(
                "load() requires a cvs or repository URL; received %r"
                % url)
        if isinstance(url, RepositoryUrl):
            raise ValueError("repository: URLs must be joined with the"
                             " appropriate cvs: base URL")
        elif isinstance(url, CvsUrl):
            cvsurl = copy.copy(url)
            key = cvsurl.getUrl()
        else:
            raise TypeError("load() requires a cvs: URL")
        if not cvsurl.tag:
            cvsurl.tag = self.tag
            key = cvsurl.getUrl()
        # If we've already loaded this, use that copy.  This doesn't
        # consider fetching something with a different path that's
        # represent by a previous load():
        if key in self.workdirs:
            return self.workdirs[key][1]

        workdir = tempfile.mkdtemp(prefix="cvsloader-")
        cvsroot = cvsurl.getCvsRoot()
        tag = cvsurl.tag or "HEAD"
        path = cvsurl.path or "."

        rc = self.runCvsExport(cvsroot, workdir, tag, path)
        if rc:
            # Some error occurred: we haven't figured out what, and
            # don't really care; details went to standard error.
            # Assume there's nothing to be gained from the temporary
            # directory and toss it.
            shutil.rmtree(workdir)
            raise CvsLoadingError(cvsurl, rc)

        if path == ".":
            self.workdirs[key] = (workdir, workdir)
            return workdir
        elif self.isFileResource(cvsurl):
            basename = posixpath.basename(path)
            path = os.path.join(workdir, basename, basename)
            self.workdirs[key] = (workdir, path)
            return path
        else:
            basename = posixpath.basename(path)
            path = os.path.join(workdir, basename)
            self.workdirs[key] = (workdir, path)
            return path

    def runCvsExport(self, cvsroot, workdir, tag, path):
        # cvs -f -Q -z6 -d CVSROOT export -kk -d WORKDIR -r TAG PATH
        # separated out from load() to ease testing the rest of load()
        # XXX not sure of a good way to test this method!
        wf = posixpath.basename(path)
        pwd = os.getcwd()
        os.chdir(workdir)
        try:
            return os.spawnlp(os.P_WAIT, "cvs",
                              "cvs", "-f", "-Q", "-z6", "-d", cvsroot,
                              "export", "-kk", "-d", wf, "-r", tag, path)
        finally:
            os.chdir(pwd)

    # XXX CVS does some weird things with export; not sure how much
    # they mean yet.  Note that there's no way to tell if the resource
    # is a file or directory from the cvs: URL.
    #
    # - If the directory named with -d already exists, a CVS/
    #   directory is created within that and is populated, regardless
    #   of whether the requested resource is a file or directory.
    #
    # - If the directory does not already exist it is created, and no
    #   CVS/ directory is created within that.
    #
    # - If the requested resource is a file, it is created within the
    #   new directory, otherwise the directory is populated with the
    #   contents of the directory in the repository.
    #
    # "cvs rlog -R" gives a list of ,v files for the selected
    # resource.  If there's more than one, it's a directory.
    # Otherwise, it's a file if the path matches the repository root +
    # the path from the cvs: URL.

    def isFileResource(self, cvsurl):
        if not cvsurl.path:
            # The whole repository is always a directory
            return False
        f = self.openCvsRLog(cvsurl.getCvsRoot(), cvsurl.path)
        line1 = f.readline().rstrip()
        line2 = f.readline()
        f.close()
        if line2:
            # more than one line; must be a directory
            return False
        module, base = posixpath.split(cvsurl.path)
        comma_v = posixpath.join(cvsurl.cvsroot, cvsurl.path) + ",v"
        comma_v_attic = posixpath.join(
            cvsurl.cvsroot, module, "Attic", base) + ",v"
        return line1 in (comma_v, comma_v_attic)

    # separate this out to ease testing

    def openCvsRLog(self, cvsroot, path):
        return os.popen(
            "cvs -f -q -d '%s' rlog -R -l '%s'" % (cvsroot, path), "r")


class FileProxy(object):

    def __init__(self, path, mode, loader, url=None):
        self.name = url or path
        self._file = file(path, mode)
        self._cleanup = loader.cleanup

    def __getattr__(self, name):
        return getattr(self._file, name)

    def close(self):
        if not self._file.closed:
            self._file.close()
            self._cleanup()
            self._cleanup = None

    # We shouldn't ever actually need to deal with softspace since
    # we're read-only, but... real files still behave this way, so we
    # emulate it.

    def _get_softspace(self):
        return self._file.softspace

    def _set_softspace(self, value):
        self._file.softspace = value

    softspace = property(_get_softspace, _set_softspace)
