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
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from ZODB.POSException import StorageSystemError

# Try to create a function that creates Unix file locks.
try:
    import fcntl

    lock_file_FLAG = fcntl.LOCK_EX | fcntl.LOCK_NB

    def lock_file(file):
        try:
            un = file.fileno()
        except:
            return # don't care if not a real file

        try:
            fcntl.flock(un, lock_file_FLAG)
        except:
            raise StorageSystemError, (
                "Could not lock the database file.  There must be\n"
                "another process that has opened the file.\n"
                "<p>")

except:
    # Try windows-specific code:
    try:
        from winlock import LockFile
        def lock_file(file):
            try:
                un=file.fileno()
            except:
                return # don't care if not a real file

            try:
                LockFile(un, 0, 0, 1, 0) # just lock the first byte, who cares
            except:
                raise StorageSystemError, (
                    "Could not lock the database file.  There must be\n"
                    "another process that has opened the file.\n"
                    "<p>")
    except:
        import zLOG
        def lock_file(file):
            zLOG.LOG("FS", zLOG.INFO,
                     "No file-locking support on this platform")
