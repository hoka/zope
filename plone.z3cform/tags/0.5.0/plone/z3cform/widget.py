from zope import interface
from zope.schema import vocabulary

import z3c.form.term
import z3c.form.browser.checkbox
import z3c.form.interfaces

class SingleCheckboxWidget(z3c.form.browser.checkbox.SingleCheckBoxWidget):
    """XXX: We need to refactor this and patch z3c.form where
    it makes sense.
    """

    def update(self):
        self.ignoreContext = True
        super(SingleCheckboxWidget, self).update()

    def updateTerms(self):
        # The default implementation would render "selected" as a
        # lebel for the single checkbox.  We use no label instead.
        if self.terms is None:
            self.terms = z3c.form.term.Terms()
            self.terms.terms = vocabulary.SimpleVocabulary((
                vocabulary.SimpleTerm(True, 'selected', u''),
                ))
        return self.terms

    def extract(self, default=z3c.form.interfaces.NOVALUE):
        # The default implementation returns [] here.
        if (self.name not in self.request and
            self.name+'-empty-marker' in self.request):
            return default
        else:
            return super(SingleCheckboxWidget, self).extract(default)

@interface.implementer(z3c.form.interfaces.IDataConverter)
def singlecheckboxwidget_factory(field, request):
    widget = SingleCheckboxWidget(request)
    return z3c.form.widget.FieldWidget(field, widget)
