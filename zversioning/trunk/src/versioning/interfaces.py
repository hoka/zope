"""  Whether the versioning scheme uses the existing ZODB or some
other versioning system like CVS or Subversion as a subsystem
should be configurable.  How the repository stores the data, 
whether it is able to version metadata or only content, 
whether it uses revision numbers for commits
(like Subversion) or document specific version numbers (like CVS)
may thus vary.        
               
Therefore we use a ticket mechanism, which means that
the versioning repository takes any versionable data (not necessarily
the original object), stores them whereever it likes and gives
back arbitrary access information (a path, a global unique id) which
is sufficient to guarantee that the provided versionable data
can be retrieved.

It's the responsibility of the clients to bookkeep this access information 
or tickets. The inner structure of these tickets cannot be
determined in advance. We therefore propose only a marker interface
for this.
    
To abstract from the access is simple, more difficult
is the question, what happens if the used repository allows 
to generate new version independently from Zope.
For instance, if someone uses Subversion
as a backend for versioning, numerous other clients can access 
the versioned contents and commit changes, if they are allowed.

The important distinction here is that some repositories
are passive and only wait for versions that were created in Zope.
Other versioning system may create their own versions of objects
which must be recognized and be read into Zope. In this case
there must be a mechanism that informs the involved Zope
objects about new versions. We propose to use the Zope event system 
to allow versionable objects to subscribe to new versions if the
used backend generates its own versions.
"""

import persistent, zope
from zope.interface import Interface

from zope.app.container.interfaces import INameChooser

class RepositoryError(Exception):
    pass

class IRepository(Interface):
    """A version repository providing core functionality.
    
    IRepository is a kind of abstract component as the most important
    functionality of storing versions of object is not implemented
    here.
    
    See other repository interfaces defining different access strategies.

    As long you have at least one object from your versioned
    object cloud you can reach every object from it (at least the 
    versioned aspects). XXX After having deleted the last object 
    the IHistoryStorage component has to be asked for a bootstrap
    object.
    
    ToDo:
    
        - removeFromVersionControl: meant to be the opposite of 
          applyVersionControl (what's the opposite?)
        - deleteVersionHistory: meant to delete the history, heavy!!!!
          We have to think about use cases and what the framework
          shall support. 99.99% YAGNI
    """
    
    def applyVersionControl(obj):
        """Put the an object under version control.
        
        This method has to be call prior using any other repository
        related methods. The objects current state gets saved as first
        version.
        
        XXX Different comments apply for different repositories. Where
        to put this?
        """
    
    def revertToVersion(obj, selector):
        """Reverts the object to the selected version.
        
        XXX Do we need to say something about branches?
        """
        

class ICopyModifyMergeRepository(IRepository):
    """Top level API for a copy-modify-merge (subversion like) repository.
    """
    
    def applyVersionControl(obj):
        """Put the an object under version control.
        
        This method has to be call prior using any other repository
        related methods. The objects current state gets saved as first
        version.
        
        After this operation the object is in checked in state.
        """
    
    def saveAsVersion(obj, metadata=None):
        """Save the current state of the object for later retreival.
        """

class ICheckoutCheckinRepository(IRepository):
    """Top level API for a checkout-modify-checkin (XXX DeltaV like) repository.
    
    These kind of repositories administrate an "object is in use" 
    information which may be suitable in some environments.
    
    The Checkin/Checkout information may be seen as kind of soft lock.
    """

    def checkout(obj):
        """Marks the object as checked out (being in use/soft locked).
        """
    
    def checkin(obj, metadata=None):
        """Check in the current state of an object and does a soft 
           unlock.
        
        Raises an RepositoryError if the object is not versionable.
        XXX Other exceptions (for repository problems)?
        
        XXX What happens if the follwoing happens:
            - user A checks out the object
            - user B checks it out at another location
            - user B checks in the object
            - Question: is the object marked as checked in or checked out?
        """

    def isCheckedOut(obj):
        """Returns true if the object is checked out.
        """

class IHardlockUnlockRepository(ICheckoutCheckinRepository):
    """Top level API for a lock-modify-unlock repository.
    
    These kind of repositories also manage a lock state to avoid
    editing collisions.
    
    XXX This interface may be unstable as we didn't think a lot about 
    it.
    """


class IIntrospectableRepository(Interface):
    """Additional methods providing more information versioned objects.
    """

    def getVersion(obj, selector): # XXX Naming: getCopyOfVersion
        """Returns the selected version of an object. 
        
        This method does not overwrite 'obj' (like revertToVersion
        does). Instead it returns the version as new object.
        """

    def getVersionHistory(obj):
        """Returns all versions of the given object.
        
        XXX YAGNI? This was the former 'getVersionIds'.
        """

    def listMetadata(obj):
        """Returns the metadata of all versions of the given object.
        """

class IDeletableRepository(Interface) :
    """ Most versioning systems do not allow to throw away versioned
    data, but there might be use cases were simple file repositories
    or other storage solutions can sweep out old versions. """

    def delete(obj) :
        """ Forces the repository to remove the version described by the ticket.
        
            Raises a VersionUndeletable error if the repository does not
            allow deletions or something other went wrong.
        """


class ICheckoutAware(Interface):
    """Marking objects as checked in or checked out.
    
    XXX Naming conventions? Aren't IBlahAware interfaces usually marker 
    interfaces?
    XXX IUsageTrackingAware?, IInUseMarkingAware, ISoftLockingAware
    """
    
    def markAsCheckedIn(obj):
        """Marks the object as being checked in.
        """
        
    def markAsCheckedOut(obj):
        """Marks the object as being checked out.
        """

    def isCheckedOut(obj):
        """Returns true if the object is checked out
        """

   
class IVersionableAspects(Interface) :
    """ An interface that implements a versioning policy for
        a content type and a storage that knows how to version the
        content data.
        
        XXX VersionableData vermittelt zwischen den Daten und der Storage, 
        was gespeichert werden soll
        
        XXX Explain that this is a multidapter? Is there a formal way to 
        do that?
    """

    def writeAspects(metadata=None):
        """Write an aspect from the original object.
        """

    def updateAspects(selector):
        """Updates a certain aspect on the original object.
        
        XXX exceptions?
        XXX Should reading only certain parts of an aspect be possible?
            E.g. to avoid reading a big blob?
        XXX Probably the implementation has to handle lazy reading
            of only parts of an aspect.
        """
    
    def readAspects(selector):
        """Reads a certain aspect of the selected version.
        
        In contrast to 'updateAspects' the aspects are returned and 
        do not replace the already existing aspects on the adapted 
        object.
        
        XXX copy or ref?
        """

class ITicket(Interface) :
    """ A marker interface for access information for versioned data.
    
        A must provide sufficient information to get back these data.  
        A ticket is created when some versionable data have been accepted 
        and successfully stored in the repository.
    
        XXX: Special case IDelayedTicket for asynchronous storages needed?
      
    """

class IVersionHistory(Interface) :
    """ A version history of a single object. We choose an interface
        that is provided by any zope folder or container, but can
        also be easily adapted by any other sequence of objects.
    """
    
    def keys() :
        """ Returns a sequence of unique ids that can be used as access
            keys. 
        """
    
    def values() :
        """ Returns a sequence of versioned objects.
        """
        
    def __getitem__(key) :
        """ Returns the version that is specified by the key. """
  
    

class IHistoryStorage(Interface) : # IHistoriesStorage?
    """ Minimal interface for a pluggable storage that stores a new version
    of an object into an object history.
    
    XXX Important note: IHistoryStorage components must be transaction aware.
    A CVSHistoryStorage component for example has to ensure to handle 
    transactions.
    
    IHistoryStorage components store IVersionableAspects of objects.
    """

    def register(obj):
        """ Puts some object under version control. Returns an IHistory.
        
        Why register?
        We like to give the IHistoryStorage component the possibility
        to veto as early as possible (e.g. to raise "connection to 
        backend repository lost" or "quota for user Ben exceded" 
        exceptions or similar)
        """
    
    def getTicket(obj):
        """ Returns the persistent oid of an object as
            a ticket that remains stable across time.
        """
 
    def getVersion(obj, selector):
        """ Returns the version of an object that is specified by selector. 
        """

    def getObjectHistory(obj):
        """Returns the whole version history of the objects aspects.
        """
        
    def getMetadataHistory(obj):
        """Returns the whole metadata history of the objects aspects.
        """

class IVersionable(persistent.interfaces.IPersistent):
    """Version control is allowed for objects that provide this."""

   
class IMultiClientStorage(Interface) : 
    """ if the repository allows several ways to
    create versions and not only reacts to Zope calls.
    """

    def triggerEvents(ticket=None) :
        """ Induce the repository to activate events, 
        i.e. descriptions of changes that allow the application 
        to decide whether the zope database must be updated or not.
        
        If ticket is specified only the changes of the 
        referenced object should be described.
        
        If ticket is None all changes should be described.   
        """


class IVersionable(persistent.interfaces.IPersistent,
                   zope.app.annotation.interfaces.IAnnotatable):
    """Version control is allowed for objects that provide this."""

class INonVersionable(zope.interface.Interface):
    """Version control is not allowed for objects that provide this.
    
    XXX Do we need that? Is this YAGNI?
    """

class IVersioned(IVersionable):
    """Version control is in effect for this object."""


# XXX describe Event types here


