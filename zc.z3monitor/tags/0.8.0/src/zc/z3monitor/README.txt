=====================
Zope 3 Monitor Server
=====================

The Zope 3 monitor server is a server that runs in a Zope 3 process and that
provides a command-line interface to request various bits of information.  It
is based on zc.monitor, which is itself based on zc.ngi, so we can use the
zc.ngi testing infrastructure to demonstrate it.

This package provides several Zope 3 and ZODB monitoring and introspection
tools that work within the zc.monitor server.  These are demonstrated below.

Please see the zc.monitor documentation for details on how the server works.

This package also supports starting a monitor using ZConfig, and provides a
default configure.zcml for registering plugins.

The ZConfig setup is not demonstrated in this documentation, but the usage is
simple.  In your ZConfig file, provide a "product-config" stanza for
zc.z3monitor that specifies the port on which the zc.monitor server should
listen.

For instance, this stanza will start a monitor server on port 8888::

    <product-config zc.z3monitor>
        bind 8888
    </product-config>

To bind to a specific address::

    <product-config zc.z3monitor>
        bind 127.0.0.1:8888
    </product-config>

To bind to a unix domain socket::

    <product-config zc.z3monitor>
        bind /var/socket
    </product-config>

To include the default commands of zc.monitor and zc.z3monitor, simply include
the configure.zcml from this package::

    <include package="zc.z3monitor" />

Now let's look at the commands that this package provides.  We'll get a test
connection to the monitor server and register the plugins that zc.monitor and
zc.z3monitor provide.

    >>> import zc.ngi.testing
    >>> import zc.monitor
    >>> import zc.monitor.interfaces
    >>> import zc.z3monitor
    >>> import zc.z3monitor.interfaces
    >>> import zope.component

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> zope.component.provideUtility(zc.monitor.help,
    ...     zc.monitor.interfaces.IMonitorPlugin, 'help')
    >>> zope.component.provideUtility(zc.monitor.interactive,
    ...     zc.monitor.interfaces.IMonitorPlugin, 'interactive')
    >>> zope.component.provideUtility(zc.monitor.quit,
    ...     zc.monitor.interfaces.IMonitorPlugin, 'quit')

    >>> zope.component.provideUtility(zc.z3monitor.monitor,
    ...     zc.z3monitor.interfaces.IZ3MonitorPlugin, 'monitor')
    >>> zope.component.provideUtility(zc.z3monitor.dbinfo,
    ...     zc.z3monitor.interfaces.IZ3MonitorPlugin, 'dbinfo')
    >>> zope.component.provideUtility(zc.z3monitor.zeocache,
    ...     zc.z3monitor.interfaces.IZ3MonitorPlugin, 'zeocache')
    >>> zope.component.provideUtility(zc.z3monitor.zeostatus,
    ...     zc.z3monitor.interfaces.IZ3MonitorPlugin, 'zeostatus')

We'll use the zc.monitor ``help`` command to see the list of available
commands:

    >>> connection.test_input('help\n')
    Supported commands:
      dbinfo -- Get database statistics
      help -- Get help about server commands
      interactive -- Turn on monitor's interactive mode
      monitor -- Get general process info
      quit -- Quit the monitor
      zeocache -- Get ZEO client cache statistics
      zeostatus -- Get ZEO client status information
    -> CLOSE

The commands that come with the zc.z3monitor package use database information.
They access databases as utilities.  Let's create some test databases and
register them as utilities.

    >>> from ZODB.tests.util import DB
    >>> main = DB()
    >>> from zope import component
    >>> import ZODB.interfaces
    >>> component.provideUtility(main, ZODB.interfaces.IDatabase)
    >>> other = DB()
    >>> component.provideUtility(other, ZODB.interfaces.IDatabase, 'other')

We also need to enable activity monitoring in the databases:

    >>> import ZODB.ActivityMonitor
    >>> main.setActivityMonitor(ZODB.ActivityMonitor.ActivityMonitor())
    >>> other.setActivityMonitor(ZODB.ActivityMonitor.ActivityMonitor())

Process Information
===================

To get information about the process overall, use the monitor
command:

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('help monitor\n')
    Help for monitor:
    <BLANKLINE>
    Get general process info
    <BLANKLINE>
        The minimal output has:
    <BLANKLINE>
        - The number of open database connections to the main database, which
          is the database registered without a name.
        - The virtual memory size, and
        - The resident memory size.
    <BLANKLINE>
        If there are old database connections, they will be listed.  By
        default, connections are considered old if they are greater than 100
        seconds old. You can pass a minimum old connection age in seconds.
        If you pass a value of 0, you'll see all connections.
    <BLANKLINE>
        If you pass a name after the integer, this is used as the database name.
        The database name defaults to the empty string ('').
    <BLANKLINE>
    -> CLOSE

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('monitor\n') #doctest: +NORMALIZE_WHITESPACE
    0
    VmSize:	   35284 kB
    VmRSS:	   28764 kB
    -> CLOSE

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('monitor 100 other\n') #doctest: +NORMALIZE_WHITESPACE
    0
    VmSize:	   35284 kB
    VmRSS:	   28764 kB
    -> CLOSE

Note that, as of this writing, the VmSize and VmRSS lines will only be present
on a system with procfs.  This generally includes many varieties of Linux,
and excludes OS X and Windows.

Let's create a couple of connections and then call z3monitor again
with a value of 0:

    >>> conn1 = main.open()
    >>> conn2 = main.open()

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('monitor 0\n') #doctest: +NORMALIZE_WHITESPACE
    2
    VmSize:	   36560 kB
    VmRSS:	   28704 kB
    0.0    (0)
    0.0    (0)
    -> CLOSE

The extra line of output gives connection debug info.
If we set some additional input, we'll see it:

    >>> conn1.setDebugInfo('/foo')
    >>> conn2.setDebugInfo('/bar')

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('monitor 0\n') #doctest: +NORMALIZE_WHITESPACE
    2
    VmSize:	   13048 kB
    VmRSS:	   10084 kB
    0.0   /bar (0)
    0.0   /foo (0)
    -> CLOSE

    >>> conn1.close()
    >>> conn2.close()

Database Information
====================

To get information about a database, use the dbinfo command:

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('help dbinfo\n')
    Help for dbinfo:
    <BLANKLINE>
    Get database statistics
    <BLANKLINE>
        By default statistics are returned for the main database.  The
        statistics are returned as a single line consisting of the:
    <BLANKLINE>
        - number of database loads
    <BLANKLINE>
        - number of database stores
    <BLANKLINE>
        - number of connections in the last five minutes
    <BLANKLINE>
        - number of objects in the object caches (combined)
    <BLANKLINE>
        - number of non-ghost objects in the object caches (combined)
    <BLANKLINE>
        You can pass a database name, where "-" is an alias for the main database.
    <BLANKLINE>
        By default, the statistics are for a sampling interval of 5
        minutes.  You can request another sampling interval, up to an
        hour, by passing a sampling interval in seconds after the database name.
    <BLANKLINE>
    -> CLOSE

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('dbinfo\n') #doctest: +NORMALIZE_WHITESPACE
    0   0   2   0   0
    -> CLOSE

Let's open a connection and do some work:

    >>> conn = main.open()
    >>> conn.root()['a'] = 1
    >>> import transaction
    >>> transaction.commit()
    >>> conn.root()['a'] = 1
    >>> transaction.commit()
    >>> conn.close()

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('dbinfo\n') #doctest: +NORMALIZE_WHITESPACE
    1   2   3   1   1
    -> CLOSE

You can specify a database name.  So, to get statistics for the other
database, we'll specify the name it was registered with:

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('dbinfo other\n')  #doctest: +NORMALIZE_WHITESPACE
    0   0   0   0   0
    -> CLOSE

You can use '-' to name the main database:

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('dbinfo -\n')  #doctest: +NORMALIZE_WHITESPACE
    1   2   3   1   1
    -> CLOSE

You can specify a number of seconds to sample. For example, to get
data for the last 10 seconds:

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('dbinfo - 10\n') #doctest: +NORMALIZE_WHITESPACE
    1   2   3   1   1
    -> CLOSE

.. Edge case to make sure that ``deltat`` is used:

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('dbinfo - 0\n') #doctest: +NORMALIZE_WHITESPACE
    0   0   0   1   1
    -> CLOSE

ZEO Cache Statistics
====================

You can get ZEO cache statistics using the zeocache command.

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('help zeocache\n')
    Help for zeocache:
    <BLANKLINE>
    Get ZEO client cache statistics
    <BLANKLINE>
        The command returns data in a single line:
    <BLANKLINE>
        - the number of records added to the cache,
    <BLANKLINE>
        - the number of bytes added to the cache,
    <BLANKLINE>
        - the number of records evicted from the cache,
    <BLANKLINE>
        - the number of bytes evicted from the cache,
    <BLANKLINE>
        - the number of cache accesses.
    <BLANKLINE>
        By default, data for the main database are returned.  To return
        information for another database, pass the database name.
    <BLANKLINE>
    -> CLOSE

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('zeocache\n') #doctest: +NORMALIZE_WHITESPACE
    42 4200 23 2300 1000
    -> CLOSE

You can specify a database name:

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('zeocache other\n') #doctest: +NORMALIZE_WHITESPACE
    42 4200 23 2300 1000
    -> CLOSE

ZEO Connection Status
=====================

The zeostatus command lets you get information about ZEO connection status:

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('help zeostatus\n')
    Help for zeostatus:
    <BLANKLINE>
    Get ZEO client status information
    <BLANKLINE>
        The command returns True if the client is connected and False otherwise.
    <BLANKLINE>
        By default, data for the main database are returned.  To return
        information for another database, pass the database name.
    <BLANKLINE>
    -> CLOSE

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('zeostatus\n') #doctest: +NORMALIZE_WHITESPACE
    True
    -> CLOSE

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('zeostatus other\n') #doctest: +NORMALIZE_WHITESPACE
    True
    -> CLOSE

In this example, we're using a faux ZEO connection.  It has an
attribute that determines whether it is connected or not.  Id we
change it, then the zeocache output will change:

    >>> main._storage._is_connected = False

    >>> connection = zc.ngi.testing.TextConnection()
    >>> server = zc.monitor.Server(connection)

    >>> connection.test_input('zeostatus\n') #doctest: +NORMALIZE_WHITESPACE
    False
    -> CLOSE
