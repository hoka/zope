# XXX The fact that this module has the same name as the package makes
# explicit imports impossible elsewhere.  Pick a new name?

from ITransaction import ITransaction

class Set(dict):

    def add(self, k):
        self[k] = 1

class Status:

    ACTIVE = "Active"
    PREPARED = "Prepared"
    COMMITTED = "Committed"
    ABORTED = "Aborted"

class Transaction:

    __implements__ = ITransaction

    def __init__(self, manager=None, parent=None):
        self._manager = manager
        self._parent = None
        self._status = Status.ACTIVE
        self._resources = Set()

    def __repr__(self):
        return "<%s %X %s>" % (self.__class__.__name__, id(self), self._status)

    def begin(self, parent=None):
        """Begin a transaction.

        If parent is not None, it is the parent transaction for this one.
        """
        assert self._manager is not None
        if parent is not None:
            t = Transaction(self.manager, self)
            return t

    def commit(self):
        """Commit a transaction."""
        assert self._manager is not None
        self._manager.commit(self)

    def abort(self):
        """Rollback to initial state."""
        assert self._manager is not None
        self._manager.abort(self)

    def savepoint(self):
        """Save current progress and return a savepoint."""
        assert self._manager is not None
        return self._manager.savepoint(self)

    def join(self, resource):
        """resource is participating in the transaction."""
        assert self._manager is not None
        self._resources.add(resource)

    def status(self):
        """Return the status of the transaction."""
        return self._status
