
class IObjectMover(Interface):
    '''Use getAdapter(obj, IObjectMover) to move an object somewhere.'''

    def moveTo(target, name=None):
        '''Move this object to the target given.

        Returns the new name within the target
        Typically, the target is adapted to IPasteTarget.'''

    def moveable():
        '''Returns True if the object is moveable, otherwise False.'''

    def moveableTo(target, name=None):
        '''Say whether the object can be moved to the given target.
        
        Returns True if it can be moved there. Otherwise, returns
        false.
        '''

class IObjectCopier(Interface):

    def copyTo(target, name=None):
        '''Copy this object to the target given.
        
        Returns the new name within the target, or None
        if the target doesn't do names.
        Typically, the target is adapted to IPasteTarget.
        After the copy is added to the target container, publish
        an IObjectCopied event in the context of the target container.
        If a new object is created as part of the copying process, then
        an IObjectCreated event should be published.
        '''

    def copyable():
        '''Returns True if the object is copyable, otherwise False.'''
        
    def copyableTo(target, name=None):
        '''Say whether the object can be copied to the given target.
        
        Returns True if it can be copied there. Otherwise, returns
        False.
        '''

