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
"""Functions that control how the Zope appserver knits itself together.

$Id: main.py,v 1.2 2003/06/25 15:29:32 fdrake Exp $
"""

import logging
import os
import sys
import time

from zdaemon import zdoptions

from zodb.zeo import threadedasync

from zope.app import config
from zope.app.event import publish
from zope.app.process import event
from zope.server.taskthreads import ThreadedTaskDispatcher

CONFIG_FILENAME = "zope.conf"


class ZopeOptions(zdoptions.ZDOptions):

    logsectionname = None

    def default_configfile(self):
        dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__),
                         os.pardir, os.pardir, os.pardir, os.pardir))
        for filename in [CONFIG_FILENAME, CONFIG_FILENAME + ".in"]:
            filename = os.path.join(dir, filename)
            if os.path.isfile(filename):
                return filename
        return None


def main(args=None):
    # Record start times (real time and CPU time)
    t0 = time.time()
    c0 = time.clock()

    setup(args)

    t1 = time.time()
    c1 = time.clock()
    logging.info("Startup time: %.3f sec real, %.3f sec CPU", t1-t0, c1-c0)

    run()
    sys.exit(0)


def run():
    try:
        threadedasync.loop()
    except KeyboardInterrupt:
        # Exit without spewing an exception.
        pass


def setup(args=None):
    if args is None:
        args = sys.argv[1:]
    options = ZopeOptions()
    options.schemadir = os.path.dirname(os.path.abspath(__file__))
    options.realize(args)
    options = options.configroot

    sys.setcheckinterval(options.check_interval)

    options.eventlog()

    config(options.site_definition)

    db = options.database.open()

    publish(None, event.DatabaseOpened(db))

    task_dispatcher = ThreadedTaskDispatcher()
    task_dispatcher.setThreadCount(options.threads)

    for server in options.servers:
        server.create(task_dispatcher, db)

    publish(None, event.ProcessStarting())
