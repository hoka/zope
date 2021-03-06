
RelStorage is a storage implementation for ZODB that stores pickles in
a relational database. PostgreSQL 8.1 and above (via psycopg2), MySQL
5.0.32+ / 5.1.34+ (via MySQLdb 1.2.2 and above), and Oracle 10g (via
cx_Oracle) are currently supported. RelStorage replaces the PGStorage
project.

.. contents::


Features
========

* It is a drop-in replacement for FileStorage and ZEO.
* There is a simple way to convert FileStorage to RelStorage and back again.
  You can also convert a RelStorage instance to a different relational database.
* Designed for high volume sites: multiple ZODB instances can share the same
  database. This is similar to ZEO, but RelStorage does not require ZEO.
* According to some tests, RelStorage handles high concurrency better than
  the standard combination of ZEO and FileStorage.
* Whereas FileStorage takes longer to start as the database grows due to an
  in-memory index of all objects, RelStorage starts quickly regardless of
  database size.
* Supports undo, packing, and filesystem-based ZODB blobs.
* Both history-preserving and history-free storage are available.
* Capable of failover to replicated SQL databases.
* Free, open source (ZPL 2.1)


Installation
============

You can install RelStorage using easy_install::

    easy_install RelStorage

RelStorage requires a version of ZODB that is aware of MVCC storages.
ZODB 3.9 supports RelStorage without any patches. ZODB 3.7 and 3.8 can
support RelStorage if you first apply a patch to ZODB. You can get
versions of ZODB with the patch already applied here:

    http://packages.willowrise.org

The patches are also included in the source distribution of RelStorage.

You need the Python database adapter that corresponds with your database.
Install psycopg2, MySQLdb 1.2.2+, or cx_Oracle 4.3+.  Note that Debian Etch
ships MySQLdb 1.2.1, but that version has a bug in BLOB handling that manifests
itself only with certain character set configurations.  MySQLdb 1.2.2 fixes the
bug.

Configuring Your Database
-------------------------

You need to configure a database and user account for RelStorage.
RelStorage will populate the database with its schema the first time it
connects.

PostgreSQL
~~~~~~~~~~

If you installed PostgreSQL from a binary package, you probably have a
user account named ``postgres``. Since PostgreSQL respects the name of
the logged-in user by default, switch to the ``postgres`` account to
create the RelStorage user and database. Even ``root`` does not have
the PostgreSQL privileges that the ``postgres`` account has. For
example::

    $ sudo su - postgres
    $ createuser --pwprompt zodbuser
    $ createdb -O zodbuser zodb

New PostgreSQL accounts often require modifications to ``pg_hba.conf``,
which contains host-based access control rules. The location of
``pg_hba.conf`` varies, but ``/etc/postgresql/8.4/main/pg_hba.conf`` is
common. PostgreSQL processes the rules in order, so add new rules
before the default rules rather than after. Here is a sample rule that
allows only local connections by ``zodbuser`` to the ``zodb``
database::

    local  zodb  zodbuser  md5

PostgreSQL re-reads ``pg_hba.conf`` when you ask it to reload its
configuration file::

    /etc/init.d/postgresql reload

MySQL
~~~~~

Use the ``mysql`` utility to create the database and user account. Note
that the ``-p`` option is usually required. You must use the ``-p``
option if the account you are accessing requires a password, but you
should not use the ``-p`` option if the account you are accessing does
not require a password. If you do not provide the ``-p`` option, yet
the account requires a password, the ``mysql`` utility will not prompt
for a password and will fail to authenticate.

Most users can start the ``mysql`` utility with the following shell
command, using any login account::

    $ mysql -u root -p

Here are some sample SQL statements for creating the user and database::

    CREATE USER 'zodbuser'@'localhost' IDENTIFIED BY 'mypassword';
    CREATE DATABASE zodb;
    GRANT ALL ON zodb.* TO 'zodbuser'@'localhost';
    FLUSH PRIVILEGES;

Oracle
~~~~~~

Initial setup will require ``SYS`` privileges. Using Oracle 10g XE, you
can start a ``SYS`` session with the following shell commands::

    $ su - oracle
    $ sqlplus / as sysdba

The commands below will create a PL/SQL package that provides limited
access to the DBMS_LOCK package so that RelStorage can acquire user
locks. Using ``sqlplus`` with ``SYS`` privileges, execute the
following::

    CREATE OR REPLACE PACKAGE relstorage_util AS
        FUNCTION request_lock(id IN NUMBER, timeout IN NUMBER)
            RETURN NUMBER;
    END relstorage_util;
    /

    CREATE OR REPLACE PACKAGE BODY relstorage_util AS
        FUNCTION request_lock(id IN NUMBER, timeout IN NUMBER)
            RETURN NUMBER IS
        BEGIN
            RETURN DBMS_LOCK.REQUEST(
                id => id,
                lockmode => DBMS_LOCK.X_MODE,
                timeout => timeout,
                release_on_commit => TRUE);
        END request_lock;
    END relstorage_util;
    /

Here are some sample SQL statements for creating the database user::

    CREATE USER zodb IDENTIFIED BY mypassword;
    GRANT CONNECT, RESOURCE, CREATE TABLE, CREATE SEQUENCE TO zodb;
    GRANT EXECUTE ON relstorage_util TO zodb;


Configuring Plone
-----------------

To install RelStorage in Plone, see the instructions in the following
article:

    http://shane.willowrise.com/archives/how-to-install-plone-with-relstorage-and-mysql/

Plone uses the ``plone.recipe.zope2instance`` Buildout recipe to
generate zope.conf, so the easiest way to configure RelStorage in a
Plone site is to set the ``rel-storage`` parameter in ``buildout.cfg``.
The ``rel-storage`` parameter contains settings separated by newlines,
with these values:

    * ``type``: any database type supported (``postgresql``, ``mysql``,
      or ``oracle``)
    * RelStorage options like ``cache-servers`` and ``poll-interval``
    * Adapter-specific options

An example::

    rel-storage =
        type mysql
        db plone
        user plone
        passwd PASSWORD

Configuring Zope 2
------------------

To integrate RelStorage in Zope 2, specify a RelStorage backend in
``etc/zope.conf``. Remove the main mount point and add one of the
following blocks. For PostgreSQL::

    %import relstorage
    <zodb_db main>
      mount-point /
      <relstorage>
        <postgresql>
          # The dsn is optional, as are each of the parameters in the dsn.
          dsn dbname='zodb' user='username' host='localhost' password='pass'
        </postgresql>
      </relstorage>
    </zodb_db>

For MySQL::

    %import relstorage
    <zodb_db main>
      mount-point /
      <relstorage>
        <mysql>
          # Most of the options provided by MySQLdb are available.
          # See component.xml.
          db zodb
        </mysql>
      </relstorage>
    </zodb_db>

For Oracle (10g XE in this example)::

    %import relstorage
    <zodb_db main>
      mount-point /
      <relstorage>
        <oracle>
          user username
          password pass
          dsn XE
        </oracle>
     </relstorage>
    </zodb_db>

To add ZODB blob support, provide a blob-dir parameter that specifies
where to store the blobs.  For example::

    %import relstorage
    <zodb_db main>
      mount-point /
      blob-dir ./blobs
      <relstorage>
        <postgresql>
          dsn dbname='zodb' user='username' host='localhost' password='pass'
        </postgresql>
      </relstorage>
    </zodb_db>

Configuring ``repoze.zodbconn``
-------------------------------

To use RelStorage with ``repoze.zodbconn``, a package that makes ZODB
available to WSGI applications, create a configuration file with
contents similar to the following::

    %import relstorage
    <zodb main>
      <relstorage>
        <mysql>
          db zodb
        </mysql>
      </relstorage>
      cache-size 100000
    </zodb>

``repoze.zodbconn`` expects a ZODB URI.  Use a URI of the form
``zconfig://path/to/configuration#main``.


Migrating Existing Data
=======================

The ``zodbconvert`` Utility
---------------------------

RelStorage comes with a script named ``zodbconvert`` that converts
databases to different formats. Use it to convert a FileStorage
instance to RelStorage and back, or to convert between different kinds
of RelStorage instances, or to convert other kinds of storages that
support the storage iterator protocol.

When converting between two history-preserving databases (note that
FileStorage uses a history-preserving format), ``zodbconvert`` utility
preserves all objects and transactions, meaning you can still use the
ZODB undo feature after the conversion, and you can convert back using
the same process in reverse. When converting from a history-free
database to either a history-free database or a history-preserving
database, ``zodbconvert`` retains all data, but the converted
transactions will not be undoable. When converting from a
history-preserving storage to a history-free storage, ``zodbconvert``
drops all historical information during the conversion.

How to use ``zodbconvert``
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a ZConfig style configuration file that specifies two storages,
one named "source", the other "destination". The configuration file
format is very much like zope.conf. Then run ``zodbconvert``, providing
the name of the configuration file as a parameter.

The utility does not modify the source storage. Before copying the
data, the utility verifies the destination storage is completely empty.
If the destination storage is not empty, the utility aborts without
making any changes to the destination. (Adding transactions to an
existing database is complex and out of scope for ``zodbconvert``.)

Here is a sample ``zodbconvert`` configuration file::

  <filestorage source>
    path /zope/var/Data.fs
  </filestorage>

  <relstorage destination>
    <mysql>
      db zodb
    </mysql>
  </relstorage>

This configuration file specifies that the utility should copy all of
the transactions from Data.fs to a MySQL database called "zodb". If you
want to reverse the conversion, exchange the names "source" and
"destination". All storage types and storage parameters available in
zope.conf are also available in this configuration file.

Options for ``zodbconvert``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

  ``--clear``
    Clears all data from the destination storage before copying. Use
    this only if you are certain the destination has no useful data.
    Currently only works when the destination is a RelStorage instance.

  ``--dry-run``
    Opens both storages and analyzes what would be copied, but does not
    actually copy.


Migrating to a new version of RelStorage
----------------------------------------

Sometimes RelStorage needs a schema modification along with a software
upgrade.  Hopefully, this will not often be necessary.

No schema migration is required if you are using PostgreSQL or MySQL
and upgrading from version 1.1.2 or later.  See the `notes subdirectory`_
if you are upgrading from an older version.

.. _`notes subdirectory`: http://svn.zope.org/relstorage/trunk/notes/

To migrate Oracle to version 1.4, see `migrate-to-1.4.txt`_.

.. _`migrate-to-1.4.txt`: http://svn.zope.org/*checkout*/relstorage/trunk/notes/migrate-to-1.4.txt


RelStorage Options
==================

Specify these options in zope.conf, as parameters for the
``relstorage.storage.RelStorage`` constructor, or as attributes of a
``relstorage.storage.Options`` instance. In the latter two cases, use
underscores instead of dashes in the parameter names.

``name``
        The name of the storage. Defaults to a descriptive name that
        includes the adapter connection parameters, except the database
        password.

``read-only``
        If true, only reads may be executed against the storage.

``blob-dir``
        If supplied, the storage will provide blob support; this
        parameter specifies the name of the directory to hold blob data.
        The directory will be created if it does not exist. If no value
        (or an empty value) is provided, then no blob support will be
        provided.

``keep-history``
        If this parameter is set to true (the default), the adapter
        will create and use a history-preserving database schema
        (like FileStorage). A history-preserving schema supports
        ZODB-level undo, but also grows more quickly and requires extensive
        packing on a regular basis.

        If this parameter is set to false, the adapter will create and
        use a history-free database schema. Undo will not be supported,
        but the database will not grow as quickly. The database will
        still require regular garbage collection (which is accessible
        through the database pack mechanism.)

        This parameter must not change once the database schema has
        been installed, because the schemas for history-preserving and
        history-free storage are different. If you want to convert
        between a history-preserving and a history-free database, use
        the ``zodbconvert`` utility to copy to a new database.

``replica-conf``
        If this parameter is provided, it specifies a text file that
        contains a list of database replicas the adapter can choose
        from. For MySQL and PostgreSQL, put in the replica file a list
        of ``host:port`` or ``host`` values, one per line. For Oracle,
        put in a list of DSN values. Blank lines and lines starting
        with ``#`` are ignored.

        The adapter prefers the first replica specified in the file. If
        the first is not available, the adapter automatically tries the
        rest of the replicas, in order. If the file changes, the
        adapter will drop existing SQL database connections and make
        new connections when ZODB starts a new transaction.

``replica-timeout``
        If this parameter has a nonzero value, when the adapter selects
        a replica other than the primary replica, the adapter will
        try to revert to the primary replica after the specified
        timeout (in seconds).  The default is 600, meaning 10 minutes.

``poll-interval``
        Defer polling the database for the specified maximum time interval,
        in seconds.  Set to 0 (the default) to always poll.  Fractional
        seconds are allowed.  Use this to lighten the database load on
        servers with high read volume and low write volume.

        The poll-interval option works best in conjunction with
        the cache-servers option.  If both are enabled, RelStorage will
        poll a single cache key for changes on every request.
        The database will not be polled unless the cache indicates
        there have been changes, or the timeout specified by poll-interval
        has expired.  This configuration keeps clients fully up to date,
        while removing much of the polling burden from the database.
        A good cluster configuration is to use memcache servers
        and a high poll-interval (say, 60 seconds).

        This option can be used without the cache-servers option,
        but a large poll-interval without cache-servers increases the
        probability of basing transactions on stale data, which does not
        affect database consistency, but does increase the probability
        of conflict errors, leading to low performance.

``pack-gc``
        If pack-gc is false, pack operations do not perform
        garbage collection.  Garbage collection is enabled by default.

        If garbage collection is disabled, pack operations keep at least one
        revision of every object.  With garbage collection disabled, the
        pack code does not need to follow object references, making
        packing conceivably much faster.  However, some of that benefit
        may be lost due to an ever increasing number of unused objects.

        Disabling garbage collection is also a hack that ensures
        inter-database references never break.

``pack-dry-run``
        If pack-dry-run is true, pack operations perform a full analysis
        of what to pack, but no data is actually removed.  After a dry run,
        the pack_object, pack_state, and pack_state_tid tables are filled
        with the list of object states and objects that would have been
        removed.

``pack-batch-timeout``
        Packing occurs in batches of transactions; this specifies the
        timeout in seconds for each batch.  Note that some database
        configurations have unpredictable I/O performance
        and might stall much longer than the timeout.
        The default timeout is 5.0 seconds.

``pack-duty-cycle``
        After each batch, the pack code pauses for a time to
        allow concurrent transactions to commit.  The pack-duty-cycle
        specifies what fraction of time should be spent on packing.
        For example, if the duty cycle is 0.75, then 75% of the time
        will be spent packing: a 6 second pack batch
        will be followed by a 2 second delay.  The duty cycle should
        be greater than 0.0 and less than or equal to 1.0.  Specify
        1.0 for no delay between batches.

        The default is 0.5.  Raise it to finish packing faster; lower it
        to reduce the effect of packing on transaction commit performance.

``pack-max-delay``
        This specifies a maximum delay between pack batches.  Sometimes
        the database takes an extra long time to finish a pack batch; at
        those times it is useful to cap the delay imposed by the
        pack-duty-cycle.  The default is 20 seconds.

``cache-servers``
        Specifies a list of memcached servers. Using memcached with
        RelStorage improves the speed of frequent object accesses while
        slightly reducing the speed of other operations.

        Provide a list of host:port pairs, separated by whitespace.
        "127.0.0.1:11211" is a common setting.  Some memcached modules,
        such as pylibmc, allow you to specify a path to a Unix socket
        instead of a host:port pair.

        The default is to disable memcached integration.

``cache-module-name``
        Specifies which Python memcache module to use.  The default is
        "memcache", a pure Python module.  An alternative module is
        "relstorage.pylibmc_wrapper".  This setting has no effect
        unless cache-servers is set.

``cache-prefix``
        The prefix for all keys in the cache.  All clients using a
        database should use the same cache-prefix.  Use this if you use
        a single cache for multiple databases.

``cache-local-mb``
        RelStorage caches pickled objects in memory, similar to a ZEO
        cache. This cache is shared between threads. This parameter
        configures the approximate maximum amount of memory the cache
        should consume, in megabytes.  It defaults to 10.

``cache-delta-size-limit``
        This is an advanced option. RelStorage uses a system of
        checkpoints to improve the cache hit rate. This parameter
        configures how many objects should be stored before creating a
        new checkpoint. The default is 10000.

``commit-lock-timeout``
        During commit, RelStorage acquires a database-wide lock. This
        parameter specifies how long to wait for the lock before
        failing the attempt to commit. The default is 30 seconds.

        The MySQL and Oracle adapters support this parameter. The
        PostgreSQL adapter currently does not.

``commit-lock-id``
        During commit, RelStorage acquires a database-wide lock. This
        parameter specifies the lock ID. This parameter currently
        applies only to the Oracle adapter.

Adapter Options
===============

PostgreSQL Adapter Options
--------------------------

The PostgreSQL adapter accepts:

``dsn``
    Specifies the data source name for connecting to PostgreSQL.
    A PostgreSQL DSN is a list of parameters separated with
    whitespace.  A typical DSN looks like::

        dbname='zodb' user='username' host='localhost' password='pass'

    If dsn is omitted, the adapter will connect to a local database with
    no password.  Both the user and database name will match the
    name of the owner of the current process.

MySQL Adapter Options
---------------------

The MySQL adapter accepts most parameters supported by the MySQL-python
library, including:

``host``
    string, host to connect
``user``
    string, user to connect as
``passwd``
    string, password to use
``db``
    string, database to use
``port``
    integer, TCP/IP port to connect to
``unix_socket``
    string, location of unix_socket (UNIX-ish only)
``conv``
    mapping, maps MySQL FIELD_TYPE.* to Python functions which convert a
    string to the appropriate Python type
``connect_timeout``
    number of seconds to wait before the connection attempt fails.
``compress``
    if set, gzip compression is enabled
``named_pipe``
    if set, connect to server via named pipe (Windows only)
``init_command``
    command which is run once the connection is created
``read_default_file``
    see the MySQL documentation for mysql_options()
``read_default_group``
    see the MySQL documentation for mysql_options()
``client_flag``
    client flags from MySQLdb.constants.CLIENT
``load_infile``
    int, non-zero enables LOAD LOCAL INFILE, zero disables

Oracle Adapter Options
----------------------

The Oracle adapter accepts:

``user``
        The Oracle account name
``password``
        The Oracle account password
``dsn``
        The Oracle data source name.  The Oracle client library will
        normally expect to find the DSN in /etc/oratab.

The ``zodbpack`` Script
=======================

RelStorage also comes with a script named ``zodbpack`` that packs any
ZODB storage that allows concurrent connections (including RelStorage
and ZEO, but not including FileStorage). Use ``zodbpack`` in ``cron``
scripts. Pass the script the name of a configuration file that lists
the storages to pack, in ZConfig format. An example configuration file::

  <relstorage>
    pack-gc true
    pack-duty-cycle 0.9
    <mysql>
      db zodb
    </mysql>
  </relstorage>

Options for ``zodbpack``
------------------------

  ``--days`` or ``-d``
    Specifies how many days of historical data to keep. Defaults to 0,
    meaning no history is kept. This is meaningful even for
    history-free storages, since unreferenced objects are not removed
    from the database until the specified number of days have passed.

Development
===========

You can check out from Subversion using the following command::

    svn co svn://svn.zope.org/repos/main/relstorage/trunk RelStorage

You can also browse the code:

    http://svn.zope.org/relstorage/trunk/

The best place to discuss development of RelStorage is on the zodb-dev
mailing list.



FAQs
====

Q: How can I help improve RelStorage?

    A: The best way to help is to test and to provide database-specific
    expertise.  Ask questions about RelStorage on the zodb-dev mailing list.

Q: Can I perform SQL queries on the data in the database?

    A: No.  Like FileStorage and DirectoryStorage, RelStorage stores the data
    as pickles, making it hard for anything but ZODB to interpret the data.  An
    earlier project called Ape attempted to store data in a truly relational
    way, but it turned out that Ape worked too much against ZODB principles and
    therefore could not be made reliable enough for production use.  RelStorage,
    on the other hand, is much closer to an ordinary ZODB storage, and is
    therefore more appropriate for production use.

Q: How does RelStorage performance compare with FileStorage?

    A: According to benchmarks, RelStorage with PostgreSQL is often faster than
    FileStorage, especially under high concurrency.

Q: Why should I choose RelStorage?

    A: Because RelStorage is a fairly small layer that builds on world-class
    databases.  These databases have proven reliability and scalability, along
    with numerous support options.

Q: Can RelStorage replace ZRS (Zope Replication Services)?

    A: Yes, RelStorage inherits the asynchronous master/slave replication
    capability of MySQL and other databases.  The author is currently
    looking for funding opportunities to support master/master replication.

Q: How do I set up an environment to run the RelStorage tests?

    A: See README.txt in the relstorage/tests directory.


Project URLs
============

* http://pypi.python.org/pypi/RelStorage       (PyPI entry and downloads)
* http://shane.willowrise.com/                 (blog)
