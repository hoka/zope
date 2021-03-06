"""Patch legacy template classes.

We patch the ``TALInterpreter`` class as well as the cook-method on
the pagetemplate base class (which produces the input for the TAL
interpreter).
"""

import sys

from zope.tal.talinterpreter import TALInterpreter
from zope.pagetemplate.pagetemplate import PageTemplate
from z3c.pt.pagetemplate import PageTemplate as ChameleonPageTemplate
from z3c.pt.pagetemplate import PageTemplateFile as ChameleonPageTemplateFile

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.PageTemplates.Expressions import getEngine
from RestrictedPython.Utilities import utility_builtins

from chameleon.tales import StringExpr
from chameleon.tales import NotExpr
from chameleon.tales import PythonExpr
from chameleon.tal import RepeatDict

from .expressions import PathExpr
from .expressions import TrustedPathExpr
from .expressions import ProviderExpr
from .expressions import NocallExpr
from .expressions import ExistsExpr
from .expressions import UntrustedPythonExpr


# Declare Chameleon's repeat dictionary public
RepeatDict.security = ClassSecurityInfo()
RepeatDict.security.declareObjectPublic()
RepeatDict.__allow_access_to_unprotected_subobjects__ = True

InitializeClass(RepeatDict)

# Zope 2 Page Template expressions
_secure_expression_types = {
    'python': UntrustedPythonExpr,
    'string': StringExpr,
    'not': NotExpr,
    'exists': ExistsExpr,
    'path': PathExpr,
    'provider': ProviderExpr,
    'nocall': NocallExpr,
    }


# Zope 3 Page Template expressions
_expression_types = {
    'python': PythonExpr,
    'string': StringExpr,
    'not': NotExpr,
    'exists': ExistsExpr,
    'path': TrustedPathExpr,
    'provider': ProviderExpr,
    'nocall': NocallExpr,
    }


def cook(self):
    engine = self.pt_getEngine()

    filename = getattr(self, 'filename', None)

    if engine is getEngine():
        expression_types = _secure_expression_types
        builtins = utility_builtins
    else:
        expression_types = _expression_types
        builtins = {}

    if filename is None:
        program = ChameleonPageTemplate(
            self._text, keep_body=True,
            expression_types=expression_types,
            encoding='utf-8')
    else:
        program = ChameleonPageTemplateFile(
            filename, keep_body=True,
            expression_types=expression_types,
            encoding='utf-8')

    program._v_builtins = builtins

    self._v_program = program
    self._v_macros = program.macros
    self._v_cooked = 1

    try:
        program.cook_check()
    except:
        etype, e = sys.exc_info()[:2]
        self._v_errors = [
            "Compilation failed",
            "%s.%s: %s" % (etype.__module__, etype.__name__, e)
            ]
    else:
        self._v_errors = ()


@staticmethod
def create_interpreter(cls, *args, **kwargs):
    return ChameleonTALInterpreter(*args, **kwargs)


class ChameleonTALInterpreter(object):
    def __init__(self, template, macros, context, stream, tal=True, **kwargs):
        self.template = template
        self.context = context.vars
        self.repeat = context.repeat_vars
        self.stream = stream
        self.tal = tal

    def __call__(self):
        if self.tal is False:
            result = self.template.body
        else:
            context = self.context

            # Swap out repeat dictionary for Chameleon implementation
            # and store wrapped dictionary in new variable -- this is
            # in turn used by the secure Python expression
            # implementation whenever a 'repeat' symbol is found
            context['wrapped_repeat'] = context['repeat']
            context['repeat'] = RepeatDict(self.repeat)

            # Update context with applicable builtins
            context.update(self.template._v_builtins)

            result = self.template.render(**context)

        self.stream.write(result)


TALInterpreter.__new__ = create_interpreter
PageTemplate._cook = cook
