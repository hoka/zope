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
"""Subversion support functions.

:var REPOSITORY_CONTENT: List of Subversion repository features
  checked for by `is_repository()`.
"""

import os
import posixpath
import sys
import urllib
import urlparse

from zpkgtools import LoadingError
from zpkgtools import runlog


class SubversionLoadingError(LoadingError):
    """Raised when there was some error loading from Subversion."""


if sys.platform[:3].lower() == "win":
    ROOTDIR = "\\"
else:
    ROOTDIR = "/"


def is_subversion_url(url):
    """Return `True` if the URL should be used for Subversion.

    :rtype: bool
    """
    type, rest = urllib.splittype(url)
    if type in ("svn", "svn+ssh"):
        return True
    if type == "file":
        if not url.startswith("file://"):
            return False
        parts = urlparse.urlsplit(url)
        if not parts[1] in ("", "localhost"):
            return False
        path = urllib.url2pathname(parts[2])
        # need to look for a subversion repository along the path
        while path and path != ROOTDIR and not os.path.exists(path):
            path = os.path.dirname(path)
        # path exists; is there a Subversion repository there?
        if is_repository(path):
            return True
        path = os.path.dirname(path)
        if is_repository(path):
            return True
        path = os.path.dirname(path)
        if is_repository(path):
            return True
    # We just don't handle http: and https: repositories, and I've no
    # idea how to detect them yet.
    return False


REPOSITORY_CONTENT = [
    # name, isdir
    ("conf", True),
    ("dav", True),
    (os.path.join("db", "DB_CONFIG"), False),
    ("hooks", True),
    ("locks", True),
    ]

def is_repository(path):
    # internal use
    """Return `True` if `path` is a Subversion repository.

    :rtype: bool

    This uses some general expectations of what the repository is
    supposed to look like; some repositories may not have everything
    this looks for, but that's pretty unlikely.
    """
    if not os.path.isdir(path):
        return False
    for name, isdir in REPOSITORY_CONTENT:
        fn = os.path.join(path, name)
        if isdir:
            ok = os.path.isdir(fn)
        else:
            ok = os.path.isfile(fn)
        if not ok:
            return False
    return True


class SubversionUrl:
    """Parsed representation for a Subversion URL that appears to use the
    'standard' trunk/tags tree structure.
    """
    def __init__(self, prefix, tail, tag=None):
        self.prefix = prefix
        self.tail = tail
        self.tag = tag or None

    def getUrl(self):
        if self.tag and self.tag != "HEAD":
            return "%s/tags/%s/%s" % (self.prefix, self.tag, self.tail)
        else:
            return "%s/trunk/%s" % (self.prefix, self.tail)

    def join(self, relurl):
        tag = relurl.tag
        if relurl.path:
            if posixpath.isabs(relurl.path):
                raise ValueError("cannot join an absolute path with a"
                                 " Subversion URL")
            parts = split_on_tag(relurl.path)
            if parts is None:
                path = posixpath.join(tail, relurl.path)
                if path == ".." or path.startswith("../"):
                    raise ValueError("could not join with repository: URL")
                prefix = self.prefix
                tail = self.path
            else:
                prefix, tail, tag = parts
            if tag and relurl.tag and tag != relurl.tag:
                raise ValueError(
                    "inconsistent tags identified by repository: URL")
            if not tag:
                tag = relurl.tag
        else:
            prefix = self.prefix
            tail = self.tail
        return SubversionUrl(prefix, tail, tag)


class TaglessSubversionUrl:
    """Parsed representation for a Subversion URL that does not appear
    to use the 'standard' trunk/tags tree structure.

    This has different limitations on how it can be joined with
    ``repository:`` URLs.
    """
    def __init__(self, url):
        self.url = url
        self.prefix = url
        self.tail = None
        self.tag = None

    def getUrl(self):
        return self.url

    def join(self, relurl):
        if relurl.tag:
            raise ValueError("cannot join a tagged relative URL with an"
                             " unconventional Subversion URL")
        if posixpath.isabs(relurl.path):
            raise ValueError("cannot join an absolute path with a"
                             " Subversion URL")
        url = posixpath.join(self.url, relurl.path)
        return TaglessSubversionUrl(url)


def parse(url):
    """Return a parsed representation of a Subversion URL.

    :raises ValueError: If the URL is not a valid Subversion URL.
    """
    if not is_subversion_url(url):
        raise ValueError("not a Subversion URL")

    parts = split_on_tag(url)
    if parts is None:
        return TaglessSubversionUrl(url)
    return SubversionUrl(*parts)


def split_on_tag(url):
    """Try to split a Subversion URL into a prefix, tagname, and tail.

    :param url: The URL to split.

    This assumes the standard layout for projects in Subversion
    repositories.  Returns `None` if the standard layout appears not
    to apply.
    """
    if "/tags/*/" in url:
        parts = url.split("/tags/*/", 1)
        tag = None
    elif "/trunk/" in url:
        parts = url.split("/trunk/", 1)
        tag = "HEAD"
    elif "/tags/" in url:
        parts = url.split("/tags/", 1)
        tag, rest = parts[1].split("/", 1)
        parts[1] = rest
    else:
        return None
    return parts[0], parts[1], tag


class SubversionLoader:
    # This is really only an object so the API mirrors the CvsLoader.
    """Simpler loader object that loads from Subversion."""

    def load(self, url, workdir):
        """Load a resource from Subversion.

        :return: Local filesystem path to the loaded resource.  The
          path will always be located in the tree rooted at `workdir`.

        :param url: URL to pass to Subversion.

        :param workdir: Directory to write results into.

        :raises SubversionLoadingError: When Subversion exits with an
          error not handled by this method.

        """
        # do an "svn cat" to get a file, or learn that this is a directory
        cmd = "svn cat '%s'" % url
        runlog.report_command(cmd)
        stdin, stdout, stderr = os.popen3(cmd)
        data = stdout.read()
        if not data:
            # maybe url referenced a directory
            err = stderr.readline()
            if "directory" in err:
                # it is!
                target = os.path.join(workdir, "foo")
                cmd = "svn export -q '%s' '%s'" % (url, target)
                runlog.report_command(cmd)
                rc = os.system(cmd)
                runlog.report_exit_code(rc)
                if rc != 0:
                    raise SubversionLoadingError(url, rc)
                return target
            else:
                # don't know the exit code, so make one up
                raise SubversionLoadingError(url, 1)
        else:
            name = posixpath.basename(url)
            path = os.path.join(workdir, name)
            f = open(path, "wb")
            f.write(data)
            f.close()
            return path
