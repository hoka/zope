from zope.interface import implements
from zope.component import adapts

from zope.traversing.interfaces import ITraversable
from zope.publisher.interfaces.browser import IBrowserRequest

from plone.z3cform.interfaces import IFormWrapper
from plone.z3cform import z2

class WidgetTraversal(object):
    """Allow traversal to widgets via the ++widget++ namespace. The context
    is the from layout wrapper.
    
    Note that widgets may need to mixing in Acquisition.Explicit for this to
    work.
    """
    
    implements(ITraversable)
    adapts(IFormWrapper, IBrowserRequest)
    
    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def traverse(self, name, ignored):
        
        form = self.context.form_instance
        z2.switch_on(self.context, request_layer=self.context.request_layer)
        
        form.update()
        
        # Find the widget - it may be in a group
        if name in form.widgets:
            return form.widgets.get(name)
        elif form.groups is not None:
            for group in form.groups:
                if name in group.widgets:
                    return group.widgets.get(name)
        
        return None