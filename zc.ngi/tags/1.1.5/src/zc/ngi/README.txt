=========================
Network Gateway Interface
=========================

Network programs are typically difficult to test because they require
setting up network connections, clients, and servers.  In addition,
application code gets mixed up with networking code.

The Network Gateway Interface (NGI) seeks to improve this situation by
separating application code from network code.  This allows
application and network code to be tested independently and provides
greater separation of concerns.

There are several interfaces defined by the NGI:

IImplementation
    APIs for implementing and connecting to TCP servers and for
    implemented and sending messages to UDP servers.

IConnection
    Network connection implementation.  This is the core interface that
    applications interact with,

IConnectionHandler
    Application component that handles TCP network input.

IClientConnectHandler
    Application callback that handles successful or failed outgoing
    TCP connections.

IServer
    Application callback to handle incoming connections.

IUDPHandler
    Application callback to handle incoming UDP messages.

The interfaces are split between "implementation" and "application"
interfaces.  An implementation of the NGI provides Implementation,
IConnection, IListener, and IUDPListener. An application provides
IConnectionHandler and one or more of IClientConnectHandler,
IServer, or IUDPHandler.

For more information, see interfaces.py.

Testing Implementation
======================

These interface can have a number of implementations.  The simplest
implementation is the testing implementation, which is used to test
application code.

    >>> import zc.ngi.testing

The testing module provides IConnection, IConnector, and IListener
implementations. We'll use this below to illustrate how application code
is written.

Implementing Network Clients
============================

Network clients make connections to and then use these connections to
communicate with servers.  To do so, a client must be provided with an
IConnector implantation.  How this happens is outside the scope of
the NGI.  An IConnector implementation could, for example, be provided
via the Zope component architecture, or via pkg_resources entry
points.

Let's create a simple client that calls an echo server and verifies
that the server properly echoes data sent do it.

    >>> class EchoClient:
    ...
    ...     def __init__(self, connect):
    ...         self.connect = connect
    ...
    ...     def check(self, addr, strings):
    ...         self.strings = strings
    ...         self.connect(addr, self)
    ...
    ...     def connected(self, connection):
    ...         for s in self.strings:
    ...             connection.write(s + '\n')
    ...         self.input = ''
    ...         connection.setHandler(self)
    ...
    ...     def failed_connect(self, reason):
    ...         print 'failed connect:', reason
    ...
    ...     def handle_input(self, connection, data):
    ...         print 'got input:', repr(data)
    ...         self.input += data
    ...         while '\n' in self.input:
    ...             data, self.input = self.input.split('\n', 1)
    ...             if self.strings:
    ...                expected = self.strings.pop(0)
    ...                if data == expected:
    ...                    print 'matched:', data
    ...                else:
    ...                    print 'unmatched:', data
    ...                if not self.strings:
    ...                    connection.close()
    ...             else:
    ...                print 'Unexpected input', data
    ...
    ...     def handle_close(self, connection, reason):
    ...         print 'closed:', reason
    ...         if self.strings:
    ...             print 'closed prematurely'
    ...
    ...     def handle_exception(self, connection, exception):
    ...         print 'exception:', exception.__class__.__name__, exception


The client implements the IClientConnectHandler and IConnectionHandler
interfaces.  More complex clients might implement these interfaces with
separate classes.

We'll instantiate our client using the testing connect:

    >>> client = EchoClient(zc.ngi.testing.connect)

Now we'll try to check a non-existent server:

    >>> client.check(('localhost', 42), ['hello', 'world', 'how are you?'])
    failed connect: no such server

Our client simply prints a message (and gives up) if a connection
fails. More complex applications might retry, waiting between attempts,
and so on.

The testing connect always fails unless given a test connection
ahead of time.  We'll create a testing connection and register it so a
connection can succeed:

    >>> connection = zc.ngi.testing.Connection()
    >>> zc.ngi.testing.connectable(('localhost', 42), connection)

We can register multiple connections with the same address:

    >>> connection2 = zc.ngi.testing.Connection()
    >>> zc.ngi.testing.connectable(('localhost', 42), connection2)

The connections will be used in order.

Now, our client should be able to connect to the first connection we
created:

    >>> client.check(('localhost', 42), ['hello', 'world', 'how are you?'])
    -> 'hello\n'
    -> 'world\n'
    -> 'how are you?\n'

The test connection echoes data written to it, preceded by "-> ".

Active connections are true:

    >>> bool(connection2)
    True

Test connections provide methods generating test input and flow closing
connections.  We can use these to simulate network events.  Let's
generate some input for our client:

    >>> connection.test_input('hello')
    got input: 'hello'

    >>> connection.test_input('\nbob\n')
    got input: '\nbob\n'
    matched: hello
    unmatched: bob

    >>> connection.test_close('done')
    closed: done
    closed prematurely

    >>> client.check(('localhost', 42), ['hello'])
    -> 'hello\n'

    >>> connection2.test_input('hello\n')
    got input: 'hello\n'
    matched: hello
    -> CLOSE

    >>> bool(connection2)
    False

Passing iterables to connections
================================

The writelines method of IConnection accepts iterables of strings.

    >>> def greet():
    ...     yield 'hello\n'
    ...     yield 'world\n'

    >>> zc.ngi.testing.Connection().writelines(greet())
    -> 'hello\n'
    -> 'world\n'

If there is an error in your iterator, or if the iterator returns
a non-string value, an exception will be reported using
handle_exception:

    >>> def bad():
    ...     yield 2
    >>> connection = zc.ngi.testing.Connection()
    >>> connection.setHandler(zc.ngi.testing.PrintingHandler(connection))
    >>> connection.writelines(bad())
    -> EXCEPTION TypeError Got a non-string result from iterable


Implementing network servers
============================

Implementing network servers is very similar to implementing clients,
except that a listener, rather than a connect is used.  Let's
implement a simple echo server:


    >>> class EchoServer:
    ...
    ...     def __init__(self, connection):
    ...         print 'server connected'
    ...         self.input = ''
    ...         connection.setHandler(self)
    ...
    ...     def handle_input(self, connection, data):
    ...         print 'server got input:', repr(data)
    ...         self.input += data
    ...         if '\n' in self.input:
    ...             data, self.input = self.input.split('\n', 1)
    ...             connection.write(data + '\n')
    ...             if data == 'Q':
    ...                 connection.close()
    ...
    ...     def handle_close(self, connection, reason):
    ...         print 'server closed:', reason

Out EchoServer *class* provides IServer and implement IInputHandler.

To use a server, we need a listener.  We'll use the use the testing
listener:

    >>> listener = zc.ngi.testing.listener(EchoServer)

To simulate a client connection, we create a testing connection and
call the listener's connect method:

    >>> connection = zc.ngi.testing.Connection()
    >>> listener.connect(connection)
    server connected

    >>> connection.test_input('hello\n')
    server got input: 'hello\n'
    -> 'hello\n'

    >>> connection.test_close('done')
    server closed: done

    >>> connection = zc.ngi.testing.Connection()
    >>> listener.connect(connection)
    server connected

    >>> connection.test_input('hello\n')
    server got input: 'hello\n'
    -> 'hello\n'

    >>> connection.test_input('Q\n')
    server got input: 'Q\n'
    -> 'Q\n'
    -> CLOSE

Note that it is an error to write to a closed connection:

    >>> connection.write('Hello')
    Traceback (most recent call last):
    ...
    TypeError: Connection closed


Server Control
--------------

The object returned from a listener is an IServerControl.  It provides
access to the active connections:

    >>> list(listener.connections())
    []

    >>> connection = zc.ngi.testing.Connection()
    >>> listener.connect(connection)
    server connected

    >>> list(listener.connections()) == [connection]
    True

    >>> connection2 = zc.ngi.testing.Connection()
    >>> listener.connect(connection2)
    server connected

    >>> len(list(listener.connections()))
    2
    >>> connection in list(listener.connections())
    True
    >>> connection2 in list(listener.connections())
    True

Server connections have a control attribute that is the connections
server control:

    >>> connection.control is listener
    True

Server control objects provide a close method that allows a server to
be shut down.  If the close method is called without arguments, then
then all server connections are closed immediately and no more
connections are accepted:

    >>> listener.close()
    server closed: stopped
    server closed: stopped

    >>> connection = zc.ngi.testing.Connection()
    >>> listener.connect(connection)
    Traceback (most recent call last):
    ...
    TypeError: Listener closed

If a handler function is passed, then connections aren't closed
immediately:

    >>> listener = zc.ngi.testing.listener(EchoServer)
    >>> connection = zc.ngi.testing.Connection()
    >>> listener.connect(connection)
    server connected
    >>> connection2 = zc.ngi.testing.Connection()
    >>> listener.connect(connection2)
    server connected

    >>> def handler(control):
    ...     if control is listener:
    ...        print 'All connections closed'

    >>> listener.close(handler)

But no more connections are accepted:

    >>> connection3 = zc.ngi.testing.Connection()
    >>> listener.connect(connection3)
    Traceback (most recent call last):
    ...
    TypeError: Listener closed

And the handler will be called when all of the listener's connections
are closed:

    >>> connection.close()
    -> CLOSE
    >>> connection2.close()
    -> CLOSE
    All connections closed

Long output
===========

Test requests output data written to them.  If output exceeds 50
characters in length, it is wrapped by simply breaking the repr into
50-characters parts:

    >>> connection = zc.ngi.testing.Connection()
    >>> connection.write('hello ' * 50)
    -> 'hello hello hello hello hello hello hello hello h
    .> ello hello hello hello hello hello hello hello hel
    .> lo hello hello hello hello hello hello hello hello
    .>  hello hello hello hello hello hello hello hello h
    .> ello hello hello hello hello hello hello hello hel
    .> lo hello hello hello hello hello hello hello hello
    .>  '

Text output
===========

If the output from an application consists of short lines of text, a
TextConnection can be used.  A TextConnection simply outputs it's data
directly.

    >>> connection = zc.ngi.testing.TextConnection()
    >>> connection.write('hello\nworld\n')
    hello
    world

END_OF_DATA
===========

Closing a connection closes it immediately, without sending any
pending data.  An alternate way to close a connection is to write
zc.ngi.END_OF_DATA. The connection will be automatically closed when
zc.ngi.END_OF_DATA is encountered in the output stream.

    >>> connection.write(zc.ngi.END_OF_DATA)
    -> CLOSE

    >>> connection.write('Hello')
    Traceback (most recent call last):
    ...
    TypeError: Connection closed

Connecting servers and clients
==============================

It is sometimes useful to connect a client handler and a server
handler.  Listeners created with the zc.ngi.testing.listener class have a
connect method that can be used to create connections to a server.

Let's connect out echo server and client. First, we'll create out
server using the listener constructor:

    >>> listener = zc.ngi.testing.listener(EchoServer)

Then we'll use the connect method on the listener:

    >>> client = EchoClient(listener.connect)
    >>> client.check(('localhost', 42), ['hello', 'world', 'how are you?'])
    server connected
    server got input: 'hello\n'
    server got input: 'world\n'
    server got input: 'how are you?\n'
    got input: 'hello\nworld\nhow are you?\n'
    matched: hello
    matched: world
    matched: how are you?
    server closed: closed

.. Peer connectors

  Below is an older API for connecting servers and clients in a
  testing environment.  The mechanisms defined above are prefered.

  The zc.ngi.testing.peer function can be used to create a
  connection to a peer handler. To illustrate, we'll set up an echo
  client that connects to our echo server:

    >>> client = EchoClient(zc.ngi.testing.peer(('localhost', 42), EchoServer))
    >>> client.check(('localhost', 42), ['hello', 'world', 'how are you?'])
    server connected
    server got input: 'hello\n'
    server got input: 'world\n'
    server got input: 'how are you?\n'
    got input: 'hello\nworld\nhow are you?\n'
    matched: hello
    matched: world
    matched: how are you?
    server closed: closed

UDP Support
===========

To send a UDP message, just use an implementations udp method:

    >>> zc.ngi.testing.udp(('', 42), "hello")

If there isn't a server listening, the call will effectively be
ignored. This is UDP. :)

    >>> def my_udp_handler(addr, data):
    ...     print 'from %r got %r' % (addr, data)

    >>> listener = zc.ngi.testing.udp_listener(('', 42), my_udp_handler)

    >>> zc.ngi.testing.udp(('', 42), "hello")
    from '<test>' got 'hello'

    >>> listener.close()
    >>> zc.ngi.testing.udp(('', 42), "hello")

A default handler is used if you don't pass a handler:

    >>> listener = zc.ngi.testing.udp_listener(('', 43))
    >>> zc.ngi.testing.udp(('', 43), "hello")
    udp from '<test>' to ('', 43):
      'hello'

    >>> listener.close()
    >>> zc.ngi.testing.udp(('', 43), "hello")
