##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

import string, sys, traceback
from StringIO import StringIO
from DT_Util import ParseError, parse_params, render_blocks
from DT_Util import namespace, InstanceDict
from DT_Return import DTReturn

class Try:
    """Zope DTML Exception handling
    
    usage:
    
    <!--#try-->
    <!--#except SomeError AnotherError-->
    <!--#except YetAnotherError-->
    <!--#except-->
    <!--#else-->
    <!--#/try-->
      
    or:
      
    <!--#try-->
    <!--#finally-->
    <!--#/try-->
    
    The DTML try tag functions quite like Python's try command.
    
    The contents of the try tag are rendered. If an exception is raised,
    then control switches to the except blocks. The first except block to
    match the type of the error raised is rendered. If an except block has
    no name then it matches all raised errors.
    
    The try tag understands class-based exceptions, as well as string-based
    exceptions. Note: the 'raise' tag raises string-based exceptions.
    
    Inside the except blocks information about the error is available via
    three variables.
    
      'error_type' -- This variable is the name of the exception caught.
    
      'error_value' -- This is the caught exception's value.
    
      'error_tb' -- This is a traceback for the caught exception.
      
    The optional else block is rendered when no exception occurs in the
    try block. Exceptions in the else block are not handled by the preceding
    except blocks.

    The try..finally form specifies a `cleanup` block, to be rendered even
    when an exception occurs. Note that any rendered result is discarded if
    an exception occurs in either the try or finally blocks. The finally block
    is only of any use if you need to clean up something that will not be
    cleaned up by the transaction abort code.

    The finally block will always be called, wether there was an exception in
    the try block or not, or wether or not you used a return tag in the try
    block. Note that any output of the finally block is discarded if you use a
    return tag in the try block.

    If an exception occurs in the try block, and an exception occurs in the
    finally block, or you use the return tag in that block, any information
    about that first exception is lost. No information about the first
    exception is available in the finally block. Also, if you use a return tag
    in the try block, and an exception occurs in the finally block or you use
    a return tag there as well, the result returned in the try block will be
    lost.

    Original version by Jordan B. Baker.
    
    Try..finally and try..else implementation by Martijn Pieters.
    """
    
    name = 'try'
    blockContinuations = 'except', 'else', 'finally'
    finallyBlock=None
    elseBlock=None

    def __init__(self, blocks):
        tname, args, section = blocks[0]

        self.args = parse_params(args)
        self.section = section.blocks


        # Find out if this is a try..finally type
        if len(blocks) == 2 and blocks[1][0] == 'finally':
            self.finallyBlock = blocks[1][2].blocks

        # This is a try [except]* [else] block.
        else:
            # store handlers as tuples (name,block)
            self.handlers = []
            defaultHandlerFound = 0

            for tname,nargs,nsection in blocks[1:]:
                if tname == 'else':
                    if not self.elseBlock is None:
                        raise ParseError, (
                            'No more than one else block is allowed',
                            self.name)
                    self.elseBlock = nsection.blocks

                elif tname == 'finally':
                    raise ParseError, (
                        'A try..finally combination cannot contain '
                        'any other else, except or finally blocks',
                        self.name)

                else:
                    if not self.elseBlock is None:
                        raise ParseError, (
                            'The else block should be the last block '
                            'in a try tag', self.name)

                    for errname in string.split(nargs):
                        self.handlers.append((errname,nsection.blocks))
                    if string.strip(nargs)=='':
                        if defaultHandlerFound:
                            raise ParseError, (
                                'Only one default exception handler '
                                'is allowed', self.name)
                        else:
                            defaultHandlerFound = 1
                            self.handlers.append(('',nsection.blocks))

    def render(self, md):
        if (self.finallyBlock is None):
            return self.render_try_except(md)
        else:
            return self.render_try_finally(md)

    def render_try_except(self, md):
        result = ''

        # first we try to render the first block
        try:
            result = render_blocks(self.section, md)
        except DTReturn:
            raise
        except:
            # but an error occurs.. save the info.
            t,v = sys.exc_info()[:2]
            if type(t)==type(''):
                errname = t
            else:
                errname = t.__name__

            handler = self.find_handler(t)
                                    
            if handler is None:
                # we didn't find a handler, so reraise the error
                raise

            # found the handler block, now render it
            try:
                f=StringIO()
                traceback.print_exc(100,f)
                error_tb=f.getvalue()
                ns = namespace(md, error_type=errname, error_value=v,
                    error_tb=error_tb)[0]
                md._push(InstanceDict(ns,md))
                return render_blocks(handler, md)
            finally:
                md._pop(1)

        else:
            # No errors have occured, render the optional else block
            if (self.elseBlock is None):
                return result
            else:
                return result + render_blocks(self.elseBlock, md)
               
    def render_try_finally(self, md):
        result = ''
        # first try to render the first block
        try:
            result = render_blocks(self.section, md)
        # Then handle finally block
        finally:
            result = result + render_blocks(self.finallyBlock, md)
        return result

    def find_handler(self,exception):
        "recursively search for a handler for a given exception"
        if type(exception)==type(''):
            for e,h in self.handlers:
                if exception==e or e=='':
                    return h
            else:
                return None
        for e,h in self.handlers:
            if e==exception.__name__ or e=='' or self.match_base(exception,e):
                return h    
        return None 

    def match_base(self,exception,name):
        for base in exception.__bases__:
            if base.__name__==name or self.match_base(base,name):
                return 1
        return None
        
    __call__ = render
