==========================
Filesystem Synchronization
==========================

This package provides an API for the synchronization of Python objects
with a serialized filesystem representation. This API does not address
security issues. (See zope.app.fssync for a protected web-based API).
This API is Zope and ZODB independent.

The main use cases are

    - data export / import (e.g. moving data from one place to another)

    - content management (e.g. managing a wiki or other collections of
      documents offline)

The target representation depends on your use case. In the use case of
data export/import, for instance, it is crucial that all data are
exported as completely as possible. Since the data need not be read
by humans in most circumstances a pickle format may be the most
complete and easy one to use.
In the use case of content management it may be more important that
all metadata are readable by humans. In this case another format,
e.g. RDFa, may be more appropriate.

Main components
===============

A synchronizer serializes content objects and stores the serialized
data in a repository in an application specific format. It uses
deserializers to read the object back into the content space.
The serialization format must be rich enough to preserve various forms
of references which should be reestablished on deserialization.

All these components should be replaceable. Application may use
different serialization formats with different references for
different purposes (e.g. backup vs. content management) and different
target systems (e.g. a zip archive vs. a svn repository).

The main components are:

    - ISyncTasks like Checkout, Check, and Commit which synchronize
      a content space with a repository. These tasks uses serializers
      to produce serialized data for a repository in an application
      specific format. They use deserializers to read the data back.
      The default implementation uses xmlpickle for python objects,
      data streams for file contents, and special directories for
      extras and metadata. Alternative implementations may use
      standard pickles, a human readable format like RDFa, or
      application specific formats.

    - ISynchronizer: Synchronizers produce serialized pieces of a
      Python object (the ISerializer part of a synchronizer) and
      consume serialized data to (re-)create Python objects (the
      IDeserializer part of a synchronizer).

    - IPickler: An adapter that determines the pickle format.

    - IRepository: represents a target system that can be used
      to read and write serialized data.


Let's take some samples:

    >>> from StringIO import StringIO
    >>> from zope import interface
    >>> from zope import component
    >>> from zope.fssync import interfaces
    >>> from zope.fssync import task
    >>> from zope.fssync import synchronizer
    >>> from zope.fssync import repository
    >>> from zope.fssync import pickle

    >>> class A(object):
    ...     data = 'data of a'
    >>> class B(A):
    ...     pass
    >>> a = A()
    >>> b = B()
    >>> b.data = 'data of b'
    >>> b.extra = 'extra of b'
    >>> root = dict(a=a, b=b)


Persistent References
=====================

Many applications use more than one system of persistent references.
Zope, for instance, uses p_oids, int ids, key references,
traversal paths, dotted names, named utilities, etc.

Other systems might use generic reference systems like global unique
ids or primary keys together with domain specific references, like
emails, URI, postal addresses, code numbers, etc.
All these references are candidates for exportable references as long
as they can be resolved on import or reimport.

In our example we use simple integer ids:

    >>> class GlobalIds(object):
    ...     ids = dict()
    ...     count = 0
    ...     def getId(self, obj):
    ...         for k, v in self.ids.iteritems():
    ...             if obj == v:
    ...                 return k
    ...     def register(self, obj):
    ...         uid = self.getId(obj)
    ...         if uid is not None:
    ...             return uid
    ...         self.count += 1
    ...         self.ids[self.count] = obj
    ...         return self.count
    ...     def resolve(self, uid):
    ...         return self.ids.get(int(uid), None)

    >>> globalIds = GlobalIds()
    >>> globalIds.register(a)
    1
    >>> globalIds.register(b)
    2
    >>> globalIds.register(root)
    3

In our example we use the int ids as a substitute for the default path
references which are the most common references in Zope.

In our examples we use a SnarfRepository which can easily be examined:

>>> snarf = repository.SnarfRepository(StringIO())
>>> checkout = task.Checkout(synchronizer.getSynchronizer, snarf)

Snarf is a Zope3 specific archive format where the key
need is for simple software. The format is dead simple: each file
is represented by the string

    '<size> <pathname>\n'

followed by exactly <size> bytes.  Directories are not represented
explicitly.


Entry Ids
=========

Persistent ids are also used in the metadata files of fssync.
The references are generated by an IEntryId adapter which must
have a string representation in order to be saveable in a text file.
Typically these object ids correspond to the persistent pickle ids, but
this is not necessarily the case.

Since we do not have paths we use our integer ids:

    >>> @component.adapter(interface.Interface)
    ... @interface.implementer(interfaces.IEntryId)
    ... def entryId(obj):
    ...     global globalIds
    ...     return globalIds.getId(obj)
    >>> component.provideAdapter(entryId)


Synchronizer
============

In the use case of data export / import it is crucial that fssync is
able to serialize "all" object data. Note that it isn't always obvious
what data is intrinsic to an object. Therefore we must provide
special serialization / de-serialization tools which take care of
writing and reading "all" data.

An obvious solution would be to use inheriting synchronization
adapters. But this solution bears a risk. If someone created a subclass
and forgot to create an adapter, then their data would be serialized
incompletely. To give an example: What happens if someone has a
serialization adapter for class Person which serializes every aspect of
Person instances and defines a subclass Employee(Person) later on?
If the Employee class has some extra aspects (for example additional
attributes like insurance id, wage, etc.) these would never be serialized
as long as there is no special serialization adapter for Employees
which handles this extra aspects. The behavior is different if the
adapters are looked up by their dotted class name (i.e. the most specific
class) and not their class or interface (which might led to adapters
written for super classes). If no specific adapter exists a default
serializer (e.g a xmlpickler) can serialize the object completely. So
even if you forget to provide special serializers for all your classes
you can be sure that your data are complete.

Since the component architecture doesn't support adapters that work
one class only (not their subclasses), we register the adapter classes
as named ISynchronizerFactory utilities and use the dotted name of the
class as lookup key. The default synchronizer is registered as a
unnamed ISynchronizerFactory utility. This synchronizer ensures that
all data are pickled to the target repository.

    >>> component.provideUtility(synchronizer.DefaultSynchronizer,
    ...                             provides=interfaces.ISynchronizerFactory)

All special synchronizers are registered for a specific content class and
not an abstract interface. The class is represented by the dotted class
name in the factory registration:

    >>> class AFileSynchronizer(synchronizer.Synchronizer):
    ...     interface.implements(interfaces.IFileSynchronizer)
    ...     def dump(self, writeable):
    ...         writeable.write(self.context.data)
    ...     def load(self, readable):
    ...         self.context.data = readable.read()

    >>> component.provideUtility(AFileSynchronizer,
    ...                             interfaces.ISynchronizerFactory,
    ...                             name=synchronizer.dottedname(A))

The lookup of the utilities by the dotted class name is handled
by the getSynchronizer function, which first tries to find
a named utility. The IDefaultSynchronizer utility is used as a fallback:

    >>> synchronizer.getSynchronizer(a)
    <zope.fssync.doctest.AFileSynchronizer object at ...>

If no named adapter is registered it returns the registered unnamed default
adapter (as long as the permissions allow this):

    >>> synchronizer.getSynchronizer(b)
    <zope.fssync.synchronizer.DefaultSynchronizer object at ...>

This default serializer typically uses a pickle format, which is determined
by the IPickler adapter. Here we use Zope's xmlpickle.

    >>> component.provideAdapter(pickle.XMLPickler)
    >>> component.provideAdapter(pickle.XMLUnpickler)

For container like objects we must provide an adapter that maps the
container to a directory. In our example we use the buildin dict class:

    >>> component.provideUtility(synchronizer.DirectorySynchronizer,
    ...                             interfaces.ISynchronizerFactory,
    ...                             name=synchronizer.dottedname(dict))


Now we can export the object to the snarf archive:

    >>> checkout.perform(root, 'test')
    >>> print snarf.stream.getvalue()
    00000213 @@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="test"
             keytype="__builtin__.str"
             type="__builtin__.dict"
             factory="__builtin__.dict"
             id="3"
             />
    </entries>
    00000339 test/@@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="a"
             keytype="__builtin__.str"
             type="zope.fssync.doctest.A"
             factory="zope.fssync.doctest.A"
             id="1"
             />
      <entry name="b"
             keytype="__builtin__.str"
             type="zope.fssync.doctest.B"
             id="2"
             />
    </entries>
    00000009 test/a
    data of a00000370 test/b
    <?xml version="1.0" encoding="utf-8" ?>
    <pickle>
      <object>
        <klass>
          <global name="B" module="zope.fssync.doctest"/>
        </klass>
        <attributes>
          <attribute name="data">
              <string>data of b</string>
          </attribute>
          <attribute name="extra">
              <string>extra of b</string>
          </attribute>
        </attributes>
      </object>
    </pickle>
    <BLANKLINE>

After the registration of the necessary generators we can reimport the
serialized data from the repository:

    >>> component.provideUtility(synchronizer.FileGenerator(),
    ...                                 provides=interfaces.IFileGenerator)

    >>> target = {}
    >>> commit = task.Commit(synchronizer.getSynchronizer, snarf)
    >>> commit.perform(target, 'root', 'test')
    >>> sorted(target.keys())
    ['root']
    >>> sorted(target['root'].keys())
    ['a', 'b']

    >>> target['root']['a'].data
    'data of a'

    >>> target['root']['b'].extra
    'extra of b'

If we want to commit the data back into the original place we must check
whether the repository is still consistent with the original content.
We modify the objects in place to see what happens:

    >>> check = task.Check(synchronizer.getSynchronizer, snarf)
    >>> check.check(root, '', 'test')
    >>> check.errors()
    []

    >>> root['a'].data = 'overwritten'
    >>> root['b'].extra = 'overwritten'

    >>> check = task.Check(synchronizer.getSynchronizer, snarf)
    >>> check.check(root, '', 'test')
    >>> check.errors()
    ['test/a', 'test/b']

    >>> commit.perform(root, '', 'test')
    >>> sorted(root.keys())
    ['a', 'b']
    >>> root['a'].data
    'data of a'
    >>> root['b'].extra
    'extra of b'

    >>> del root['a']
    >>> commit.perform(root, '', 'test')
    >>> sorted(root.keys())
    ['a', 'b']

    >>> del root['b']
    >>> commit.perform(root, '', 'test')
    >>> sorted(root.keys())
    ['a', 'b']

    >>> del root['a']
    >>> del root['b']
    >>> commit.perform(root, '', 'test')
    >>> sorted(root.keys())
    ['a', 'b']


Pickling
========

In many data structures, large, complex objects are composed of
smaller objects.  These objects are typically stored in one of two
ways:

    1.  The smaller objects are stored inside the larger object.

    2.  The smaller objects are allocated in their own location,
        and the larger object stores references to them.

In case 1 the object is self-contained and can be pickled
completely. This is the default behavior of the fssync pickler:

    >>> pickler = interfaces.IPickler([42])
    >>> pickler
    <zope.fssync.pickle.XMLPickler object at ...>
    >>> print pickler.dumps()
    <?xml version="1.0" encoding="utf-8" ?>
    <pickle>
      <list>
        <int>42</int>
      </list>
    </pickle>
    <BLANKLINE>

Case 2 is more complex since the pickler has to take persistent
references into account.

    >>> class Complex(object):
    ...     def __init__(self, part1, part2):
    ...         self.part1 = part1
    ...         self.part2 = part2

Everthing here depends on the definition of what we consider to be an intrinsic
reference. In the examples above we simply considered all objects as intrinsic.

    >>> from zope.fssync import pickle
    >>> c = root['c'] = Complex(a, b)
    >>> stream = StringIO()
    >>> print interfaces.IPickler(c).dumps()
    <?xml version="1.0" encoding="utf-8" ?>
    <pickle>
      <initialized_object>
        <klass>
          <global id="o0" name="_reconstructor" module="copy_reg"/>
        </klass>
        <arguments>
          <tuple>
            <global name="Complex" module="zope.fssync.doctest"/>
            <global id="o1" name="object" module="__builtin__"/>
            <none/>
          </tuple>
        </arguments>
        <state>
          <dictionary>
            <item key="part1">
                <object>
                  <klass>
                    <global name="A" module="zope.fssync.doctest"/>
                  </klass>
                  <attributes>
                    <attribute name="data">
                        <string>data of a</string>
                    </attribute>
                  </attributes>
                </object>
            </item>
            <item key="part2">
                <object>
                  <klass>
                    <global name="B" module="zope.fssync.doctest"/>
                  </klass>
                  <attributes>
                    <attribute name="data">
                        <string>data of b</string>
                    </attribute>
                    <attribute name="extra">
                        <string>overwritten</string>
                    </attribute>
                  </attributes>
                </object>
            </item>
          </dictionary>
        </state>
      </initialized_object>
    </pickle>
    <BLANKLINE>

In order to use persistent references we must define a
PersistentIdGenerator for our pickler, which determines whether
an object should be pickled completely or only by reference:

    >>> class PersistentIdGenerator(object):
    ...     interface.implements(interfaces.IPersistentIdGenerator)
    ...     component.adapts(interfaces.IPickler)
    ...     def __init__(self, pickler):
    ...         self.pickler = pickler
    ...     def id(self, obj):
    ...         if isinstance(obj, Complex):
    ...             return None
    ...         return globalIds.getId(obj)

    >>> component.provideAdapter(PersistentIdGenerator)

    >>> globalIds.register(a)
    1
    >>> globalIds.register(b)
    2
    >>> globalIds.register(root)
    3

    >>> xml = interfaces.IPickler(c).dumps()
    >>> print xml
    <?xml version="1.0" encoding="utf-8" ?>
    <pickle>
      <object>
        <klass>
          <global name="Complex" module="zope.fssync.doctest"/>
        </klass>
        <attributes>
          <attribute name="part1">
              <persistent> <string>1</string> </persistent>
          </attribute>
          <attribute name="part2">
              <persistent> <string>2</string> </persistent>
          </attribute>
        </attributes>
      </object>
    </pickle>
    <BLANKLINE>

The persistent ids can be loaded if we define and register
a IPersistentIdLoader adapter first:

    >>> class PersistentIdLoader(object):
    ...     interface.implements(interfaces.IPersistentIdLoader)
    ...     component.adapts(interfaces.IUnpickler)
    ...     def __init__(self, unpickler):
    ...         self.unpickler = unpickler
    ...     def load(self, id):
    ...         global globalIds
    ...         return globalIds.resolve(id)

    >>> component.provideAdapter(PersistentIdLoader)
    >>> c2 = interfaces.IUnpickler(None).loads(xml)
    >>> c2.part1 == a
    True


Annotations, Extras, and Metadata
=================================

Complex objects often combine metadata and content data in various ways.
The fssync package allows to distinguish between file content, extras,
annotations, and fssync specific metadata:

    - The file content or body is directly stored in a corresponding
      file.
    - The extras are object attributes which are part of the object but not
      part of the file content. They are typically store in extra files.
    - Annotations are content related metadata which can be stored as
      attribute annotations or outside the object itself. They are typically
      stored in seperate pickles for each annotation namespace.
    - Metadata directly related to fssync are stored in Entries.xml
      files.

Where exactly these aspects are stored is defined in the
synchronization format. The default format uses a @@Zope directory with
subdirectories for object extras and annotations. These @@Zope directories
also contain an Entries.xml metadata file which defines the following
attributes:

    - id: the system id of the object, in Zope typically a traversal path
    - name: the filename of the serialized object
    - factory: the factory of the object, typically a dotted name of a class
    - type: a type identifier for pickled objects without factory
    - provides: directly provided interfaces of the object
    - key: the original name in the content space which is used
           in cases where the repository is not able to store this key
           unambigously
    - binary: a flag that prevents merging of binary data
    - flag: a status flag with the values 'added' or 'removed'

In part the metadata have to be delivered by the synchronizer. The base
synchronizer, for instance, returns the directly provided interfaces
of an object as part of it's metadata:

    >>> class IMarkerInterface(interface.Interface):
    ...     pass
    >>> interface.directlyProvides(a, IMarkerInterface)
    >>> pprint(synchronizer.Synchronizer(a).metadata())
    {'factory': 'zope.fssync.doctest.A',
     'provides': 'zope.fssync.doctest.IMarkerInterface'}

The setmetadata method can be used to write metadata
back to an object. Which metadata are consumed is up to the
synchronizer:

    >>> metadata = {'provides': 'zope.fssync.doctest.IMarkerInterface'}
    >>> synchronizer.Synchronizer(b).setmetadata(metadata)
    >>> [x for x in interface.directlyProvidedBy(b)]
    [<InterfaceClass zope.fssync.doctest.IMarkerInterface>]

In order to serialize annotations we must first provide a
ISynchronizableAnnotations adapter:

    >>> snarf = repository.SnarfRepository(StringIO())
    >>> checkout = task.Checkout(synchronizer.getSynchronizer, snarf)

    >>> from zope import annotation
    >>> from zope.annotation.attribute import AttributeAnnotations
    >>> component.provideAdapter(AttributeAnnotations)
    >>> class IAnnotatableSample(interface.Interface):
    ...     pass
    >>> class AnnotatableSample(object):
    ...     interface.implements(IAnnotatableSample,
    ...                             annotation.interfaces.IAttributeAnnotatable)
    ...     data = 'Main file content'
    ...     extra = None
    >>> sample = AnnotatableSample()

    >>> class ITestAnnotations(interface.Interface):
    ...     a = interface.Attribute('A')
    ...     b = interface.Attribute('B')
    >>> import persistent
    >>> class TestAnnotations(persistent.Persistent):
    ...     interface.implements(ITestAnnotations,
    ...                             annotation.interfaces.IAnnotations)
    ...     component.adapts(IAnnotatableSample)
    ...     def __init__(self):
    ...         self.a = None
    ...         self.b = None

    >>> component.provideAdapter(synchronizer.SynchronizableAnnotations)



    >>> from zope.annotation.factory import factory
    >>> component.provideAdapter(factory(TestAnnotations))
    >>> ITestAnnotations(sample).a = 'annotation a'
    >>> ITestAnnotations(sample).a
    'annotation a'
    >>> sample.extra = 'extra'

Without a special serializer the annotations are pickled since
the annotations are stored in the __annotions__ attribute:

    >>> root = dict()
    >>> root['test'] = sample
    >>> checkout.perform(root, 'test')
    >>> print snarf.stream.getvalue()
    00000197 @@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="test"
             keytype="__builtin__.str"
             type="__builtin__.dict"
             factory="__builtin__.dict"
             />
    </entries>
    00000182 test/@@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="test"
             keytype="__builtin__.str"
             type="zope.fssync.doctest.AnnotatableSample"
             />
    </entries>
    00001929 test/test
    <?xml version="1.0" encoding="utf-8" ?>
    <pickle>
      <object>
        <klass>
          <global name="AnnotatableSample" module="zope.fssync.doctest"/>
        </klass>
        ...
        </attributes>
      </object>
    </pickle>
    <BLANKLINE>

If we provide a directory serializer for annotations and extras we get a
file for each extra attribute and annotation namespace.

    >>> component.provideUtility(
    ...     synchronizer.DirectorySynchronizer,
    ...     interfaces.ISynchronizerFactory,
    ...     name=synchronizer.dottedname(synchronizer.Extras))

    >>> component.provideUtility(
    ...     synchronizer.DirectorySynchronizer,
    ...     interfaces.ISynchronizerFactory,
    ...     name=synchronizer.dottedname(
    ...                 synchronizer.SynchronizableAnnotations))

Since the annotations are already handled by the Synchronizer base class
we only need to specify the extra attribute here:

    >>> class SampleFileSynchronizer(synchronizer.Synchronizer):
    ...     interface.implements(interfaces.IFileSynchronizer)
    ...     def dump(self, writeable):
    ...         writeable.write(self.context.data)
    ...     def extras(self):
    ...         return synchronizer.Extras(extra=self.context.extra)
    ...     def load(self, readable):
    ...         self.context.data = readable.read()
    >>> component.provideUtility(SampleFileSynchronizer,
    ...     interfaces.ISynchronizerFactory,
    ...     name=synchronizer.dottedname(AnnotatableSample))

    >>> interface.directlyProvides(sample, IMarkerInterface)
    >>> root['test'] = sample
    >>> checkout.perform(root, 'test')
    >>> print snarf.stream.getvalue()
    00000197 @@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="test"
             keytype="__builtin__.str"
             type="__builtin__.dict"
             factory="__builtin__.dict"
             />
    </entries>
    00000182 test/@@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="test"
             keytype="__builtin__.str"
             type="zope.fssync.doctest.AnnotatableSample"
             />
    </entries>
    00001929 test/test
    <?xml version="1.0" encoding="utf-8" ?>
    <pickle>
      <object>
        <klass>
          <global name="AnnotatableSample" module="zope.fssync.doctest"/>
        </klass>
        <attributes>
          <attribute name="__annotations__">
              ...
          </attribute>
          <attribute name="extra">
              <string>extra</string>
          </attribute>
        </attributes>
      </object>
    </pickle>
    00000197 @@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="test"
             keytype="__builtin__.str"
             type="__builtin__.dict"
             factory="__builtin__.dict"
             />
    </entries>
    00000296 test/@@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="test"
             keytype="__builtin__.str"
             type="zope.fssync.doctest.AnnotatableSample"
             factory="zope.fssync.doctest.AnnotatableSample"
             provides="zope.fssync.doctest.IMarkerInterface"
             />
    </entries>
    00000211 test/@@Zope/Annotations/test/@@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="zope.fssync.doctest.TestAnnotations"
             keytype="__builtin__.str"
             type="zope.fssync.doctest.TestAnnotations"
             />
    </entries>
    00000617 test/@@Zope/Annotations/test/zope.fssync.doctest.TestAnnotations
    <?xml version="1.0" encoding="utf-8" ?>
    <pickle>
    ...
    </pickle>
    00000161 test/@@Zope/Extra/test/@@Zope/Entries.xml
    <?xml version='1.0' encoding='utf-8'?>
    <entries>
      <entry name="extra"
             keytype="__builtin__.str"
             type="__builtin__.str"
             />
    </entries>
    00000082 test/@@Zope/Extra/test/extra
    <?xml version="1.0" encoding="utf-8" ?>
    <pickle> <string>extra</string> </pickle>
    00000017 test/test
    Main file content

The annotations and extras can of course also be deserialized. The default
deserializer handles both cases:

    >>> target = {}
    >>> commit = task.Commit(synchronizer.getSynchronizer, snarf)
    >>> commit.perform(target, 'root', 'test')
    >>> result = target['root']['test']
    >>> result.extra
    'extra'
    >>> ITestAnnotations(result).a
    'annotation a'

Since we use an IDirectorySynchronizer each extra attribute and
annotation namespace get's it's own file:

    >>> for path in sorted(snarf.iterPaths()):
    ...     print path
    @@Zope/Entries.xml
    test/@@Zope/Annotations/test/@@Zope/Entries.xml
    test/@@Zope/Annotations/test/zope.fssync.doctest.TestAnnotations
    test/@@Zope/Entries.xml
    test/@@Zope/Extra/test/@@Zope/Entries.xml
    test/@@Zope/Extra/test/extra
    test/test

The number of files can be reduced if we provide the default synchronizer
which uses a single file for all annotations and a single file for
all extras:

    >>> component.provideUtility(
    ...     synchronizer.DefaultSynchronizer,
    ...     interfaces.ISynchronizerFactory,
    ...     name=synchronizer.dottedname(synchronizer.Extras))

    >>> component.provideUtility(
    ...     synchronizer.DefaultSynchronizer,
    ...     interfaces.ISynchronizerFactory,
    ...     name=synchronizer.dottedname(
    ...                 synchronizer.SynchronizableAnnotations))

    >>> root['test'] = sample
    >>> snarf = repository.SnarfRepository(StringIO())
    >>> checkout.repository = snarf
    >>> checkout.perform(root, 'test')
    >>> for path in sorted(snarf.iterPaths()):
    ...     print path
    @@Zope/Entries.xml
    test/@@Zope/Annotations/test
    test/@@Zope/Entries.xml
    test/@@Zope/Extra/test
    test/test

The annotations and extras can of course also be deserialized. The default
deserializer handles both

    >>> target = {}
    >>> commit = task.Commit(synchronizer.getSynchronizer, snarf)
    >>> commit.perform(target, 'root', 'test')
    >>> result = target['root']['test']
    >>> result.extra
    'extra'
    >>> ITestAnnotations(result).a
    'annotation a'
    >>> [x for x in interface.directlyProvidedBy(result)]
    [<InterfaceClass zope.fssync.doctest.IMarkerInterface>]

If we encounter an error, or multiple errors, while commiting we'll
see them in the traceback.

    >>> def bad_sync(container, key, fspath, add_callback):
    ...     raise ValueError('1','2','3')

    >>> target = {}
    >>> commit = task.Commit(synchronizer.getSynchronizer, snarf)
    >>> old_sync_new = commit.synchNew
    >>> commit.synchNew = bad_sync
    >>> commit.perform(target, 'root', 'test')
    Traceback (most recent call last):
        ...
    Exception: 1,2,3

Notice that if we encounter multiple exceptions we print them all
out at the end.

    >>> old_sync_old = commit.synchOld
    >>> commit.synchOld = bad_sync
    >>> commit.perform(target, 'root', 'test')
    Traceback (most recent call last):
        ...
    Exceptions:
        1,2,3
        1,2,3

    >>> commit.synchNew = old_sync_new
    >>> commit.synchOld = old_sync_old
