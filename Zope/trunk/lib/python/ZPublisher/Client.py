#!/bin/sh
""":"
exec python $0 ${1+"$@"}
"""
#"
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
"""Bobo call interface

This module provides tools for accessing web objects as if they were 
functions or objects with methods.  It also provides a simple call function 
that allows one to simply make a single web request.

  Function -- Function-like objects that return both header and body
              data when called.

  Object -- Treat a URL as a web object with methods

  call -- Simple interface to call a remote function.

The module also provides a command-line interface for calling objects.

"""
__version__='$Revision: 1.37 $'[11:-2]

import sys, regex, socket, mimetools
from httplib import HTTP
from os import getpid
from time import time
from random import random
from base64 import encodestring
from urllib import urlopen, quote
from types import FileType, ListType, DictType, TupleType
from string import strip, split, atoi, join, rfind, translate, maketrans, replace
from urlparse import urlparse

class Function:
    username=None
    password=None
    method=None
    timeout=60

    def __init__(self,url,
                 arguments=(),method=None,username=None,password=None,
                 timeout=None,
                 **headers):
        while url[-1:]=='/': url=url[:-1]
        self.url=url
        self.headers=headers
        if not headers.has_key('Host') and not headers.has_key('host'):
            headers['Host']=urlparse(url)[1]
        self.func_name=url[rfind(url,'/')+1:]
        self.__dict__['__name__']=self.func_name
        self.func_defaults=()
        
        self.args=arguments

        if method is not None: self.method=method
        if username is not None: self.username=username
        if password is not None: self.password=password
        if timeout is not None: self.timeout=timeout

        if urlregex.match(url) >= 0:
            host,port,rurl=urlregex.group(1,2,3)
            if port: port=atoi(port[1:])
            else: port=80
            self.host=host
            self.port=port
            rurl=rurl or '/'
            self.rurl=rurl
        else: raise ValueError, url

    def __call__(self,*args,**kw):
        method=self.method
        if method=='PUT' and len(args)==1 and not kw:
            query=[args[0]]
            args=()
        else:
            query=[]
        for i in range(len(args)):
            try:
                k=self.args[i]
                if kw.has_key(k): raise TypeError, 'Keyword arg redefined'
                kw[k]=args[i]
            except IndexError:    raise TypeError, 'Too many arguments'

        headers={}
        for k, v in self.headers.items(): headers[translate(k,dashtrans)]=v
        method=self.method
        if headers.has_key('Content-Type'):
            content_type=headers['Content-Type']
            if content_type=='multipart/form-data':
                return self._mp_call(kw)
        else:
            content_type=None
            if not method or method=='POST':
                for v in kw.values():
                    if hasattr(v,'read'): return self._mp_call(kw)
                
        can_marshal=type2marshal.has_key
        for k,v in kw.items():
            t=type(v)
            if can_marshal(t): q=type2marshal[t](k,v)
            else: q='%s=%s' % (k,quote(v))
            query.append(q)

        url=self.rurl
        if query:
            query=join(query,'&')
            method=method or 'POST'
            if method == 'PUT':
                headers['Content-Length']=str(len(query))
            if method != 'POST':
                url="%s?%s" % (url,query)
                query=''
            elif not content_type:
                headers['Content-Type']='application/x-www-form-urlencoded'
                headers['Content-Length']=str(len(query))
        else: method=method or 'GET'

        if (self.username and self.password and
            not headers.has_key('Authorization')):
            headers['Authorization']=(
                "Basic %s" %
                replace(encodestring('%s:%s' % (self.username,self.password)),
				     '\012',''))
	    
        try:
            h=HTTP()
            h.connect(self.host, self.port)
            h.putrequest(method, self.rurl)
            for hn,hv in headers.items():
                h.putheader(translate(hn,dashtrans),hv)
            h.endheaders()
            if query: h.send(query)
            ec,em,headers=h.getreply()
            response     =h.getfile().read()
        except:
            raise NotAvailable, RemoteException(
                NotAvailable,sys.exc_info()[1],self.url,query)

        if ec==200: return (headers,response)
        self.handleError(query, ec, em, headers, response)


    def handleError(self, query, ec, em, headers, response):
        try:    v=headers.dict['bobo-exception-value']
        except: v=ec
        try:    f=headers.dict['bobo-exception-file']
        except: f='Unknown'
        try:    l=headers.dict['bobo-exception-line']
        except: l='Unknown'
        try:    t=exceptmap[headers.dict['bobo-exception-type']]
        except:
            if   ec >= 400 and ec < 500: t=NotFound
            elif ec == 503:              t=NotAvailable
            else:                        t=ServerError
        raise t, RemoteException(t,v,f,l,self.url,query,ec,em,response)
        

    

    def _mp_call(self,kw,
                type2suffix={
                    type(1.0): ':float',
                    type(1):   ':int',
                    type(1L):  ':long',
                    type([]):  ':list',
                    type(()):  ':tuple',
                    }
                ):
        # Call a function using the file-upload protcol

        # Add type markers to special values:
        d={}
        special_type=type2suffix.has_key
        for k,v in kw.items():
            if ':' not in k:
                t=type(v)
                if special_type(t): d['%s%s' % (k,type2suffix[t])]=v
                else: d[k]=v
            else: d[k]=v

        rq=[('POST %s HTTP/1.0' % self.rurl),]
        for n,v in self.headers.items():
            rq.append('%s: %s' % (n,v))
        if self.username and self.password:
            c=replace(encodestring('%s:%s' % (self.username,self.password)),'\012','')
            rq.append('Authorization: Basic %s' % c)
        rq.append(MultiPart(d).render())
        rq=join(rq,'\r\n')   

        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect((self.host,self.port))
            sock.send(rq)
            reply=sock.makefile('rb')
            sock=None
            line=reply.readline()

            try:
                [ver, ec, em] = split(line, None, 2)
            except ValueError:
                raise 'BadReply','Bad reply from server: '+line
            if ver[:5] != 'HTTP/':
                raise 'BadReply','Bad reply from server: '+line

            ec=atoi(ec)
            em=strip(em)
            headers=mimetools.Message(reply,0)
            response=reply.read()
        finally:
          if 0:
            raise NotAvailable, (
                RemoteException(NotAvailable,sys.exc_info()[1],
                                self.url,'<MultiPart Form>'))
                
        if ec==200: return (headers,response)
        self.handleError('', ec, em, headers, response)

class Object:
    """Surrogate object for an object on the web"""
    username=None
    password=None
    method=None
    timeout=None
    special_methods= 'GET','POST','PUT'

    def __init__(self, url,
                 method=None,username=None,password=None,
                 timeout=None,
                 **headers):
        self.url=url
        self.headers=headers
        if not headers.has_key('Host') and not headers.has_key('host'):
            headers['Host']=urlparse(url)[1]
        if method is not None: self.method=method
        if username is not None: self.username=username
        if password is not None: self.password=password
        if timeout is not None: self.timeout=timeout

    def __getattr__(self, name):
        if name in self.special_methods:
            method=name
            url=self.url
        else:
            method=self.method
            url="%s/%s" % (self.url, name)

        f=Function(url,
                   method=method,
                   username=self.username,
                   password=self.password,
                   timeout=self.timeout)

        f.headers=self.headers

        return f

def call(url,username=None, password=None, **kw):
    
    return apply(Function(url,username=username, password=password), (), kw)

##############################################################################
# Implementation details below here

urlregex=regex.compile('http://\([^:/]+\)\(:[0-9]+\)?\(/.+\)?', regex.casefold)

dashtrans=maketrans('_','-')

def marshal_float(n,f): return '%s:float=%s' % (n,f)
def marshal_int(n,f):   return '%s:int=%s' % (n,f)
def marshal_long(n,f):  return ('%s:long=%s' % (n,f))[:-1]

sample_regex=regex.compile('')
def marshal_regex(n,r):
    if r.translate is sample_regex.translate:
        t='Regex'
    elif r.translate is regex.casefold:
        t='regex'
    else:
        raise ValueError, 'regular expression used unsupported translation'
    return "%s:%s=%s" % (n,t,quote(r.givenpat))

def marshal_list(n,l,tname='list', lt=type([]), tt=type(())):
    r=[]
    for v in l:
        t=type(v)
        if t is lt or t is tt:
            raise TypeError, 'Invalid recursion in data to be marshaled.'
        r.append(marshal_whatever("%s:%s" % (n,tname) ,v))
    
    return join(r,'&')

def marshal_tuple(n,l):
    return marshal_list(n,l,'tuple')
    
type2marshal={
    type(1.0):                  marshal_float,
    type(1):                    marshal_int,
    type(1L):                   marshal_long,
    type(regex.compile('')):    marshal_regex,
    type([]):                   marshal_list,
    type(()):                   marshal_tuple,
    }

def marshal_whatever(k,v):
    try: q=type2marshal[type(v)](k,v)
    except KeyError: q='%s=%s' % (k,quote(str(v)))
    return q

def querify(items):
    query=[]
    for k,v in items: query.append(marshal_whatever(k,v))

    return query and join(query,'&') or ''

NotFound     ='bci.NotFound'
InternalError='bci.InternalError'
BadRequest   ='bci.BadRequest'
Unauthorized ='bci.Unauthorized'
ServerError  ='bci.ServerError'
NotAvailable ='bci.NotAvailable'

exceptmap   ={'AttributeError'   :AttributeError,
              'BadRequest'       :BadRequest,
              'EOFError'         :EOFError,
              'IOError'          :IOError,
              'ImportError'      :ImportError,
              'IndexError'       :IndexError,
              'InternalError'    :InternalError,
              'KeyError'         :KeyError,
              'MemoryError'      :MemoryError,
              'NameError'        :NameError,
              'NotAvailable'     :NotAvailable,
              'NotFound'         :NotFound,
              'OverflowError'    :OverflowError,
              'RuntimeError'     :RuntimeError,
              'ServerError'      :ServerError,
              'SyntaxError'      :SyntaxError,
              'SystemError'      :SystemError,
              'SystemExit'       :SystemExit,
              'TypeError'        :TypeError,
              'Unauthorized'     :Unauthorized,
              'ValueError'       :ValueError,
              'ZeroDivisionError':ZeroDivisionError}


class RemoteException:

    def __init__(self,etype=None,evalue=None,efile=None,eline=None,url=None,
                 query=None,http_code=None,http_msg=None, http_resp=None):
        """Contains information about an exception which
           occurs in a remote method call"""
        self.exc_type    =etype
        self.exc_value   =evalue
        self.exc_file    =efile
        self.exc_line    =eline
        self.url         =url
        self.query       =query
        self.http_code   =http_code
        self.http_message=http_msg
        self.response    =http_resp

    def __repr__(self):
        return '%s (File: %s Line: %s)\n%s %s for %s' % (
                self.exc_value,self.exc_file,self.exc_line,
                self.http_code,self.http_message,self.url)



class MultiPart:
    def __init__(self,*args):
        c=len(args)
        if c==1:    name,val=None,args[0]
        elif c==2:  name,val=args[0],args[1]
        else:       raise ValueError, 'Invalid arguments'


        h={'Content-Type':              {'_v':''},
           'Content-Transfer-Encoding': {'_v':''},
           'Content-Disposition':       {'_v':''},}
        dt=type(val)
        b=t=None

        if dt==DictType:
            t=1
            b=self.boundary()
            d=[]
            h['Content-Type']['_v']='multipart/form-data; boundary=%s' % b
            for n,v in val.items():
                d.append(MultiPart(n,v))

        elif (dt==ListType) or (dt==TupleType):
            raise ValueError, 'Sorry, nested multipart is not done yet!'

        elif dt==FileType or hasattr(val,'read'):
            if hasattr(val,'name'):
                fn=replace(val.name, '\\', '/')
                fn=fn[(rfind(fn,'/')+1):]
                ex=fn[(rfind(fn,'.')+1):]
                if self._extmap.has_key(ex): ct=self._extmap[ex]
                else: ct=self._extmap['']
            else:
                fn=''
                ct=self._extmap[None]
            if self._encmap.has_key(ct): ce=self._encmap[ct]
            else: ce=''

            h['Content-Disposition']['_v']      ='form-data'
            h['Content-Disposition']['name']    ='"%s"' % name
            h['Content-Disposition']['filename']='"%s"' % fn
            h['Content-Transfer-Encoding']['_v']=ce
            h['Content-Type']['_v']             =ct
            d=[]
            l=val.read(8192)
            while l:
                d.append(l)
                l=val.read(8192)
        else:
            h['Content-Disposition']['_v']='form-data'
            h['Content-Disposition']['name']='"%s"' % name
            d=[str(val)]

        self._headers =h
        self._data    =d
        self._boundary=b
        self._top     =t


    def boundary(self):
        return '%s_%s_%s' % (int(time()), getpid(), int(random()*1000000000))


    def render(self):
        h=self._headers
        s=[]

        if self._top:
            for n,v in h.items():
                if v['_v']:
                    s.append('%s: %s' % (n,v['_v']))
                    for k in v.keys():
                        if k != '_v': s.append('; %s=%s' % (k, v[k]))
                    s.append('\r\n')
            p=[]
            t=[]
            b=self._boundary
            for d in self._data: p.append(d.render())
            t.append('--%s\n' % b)
            t.append(join(p,'\n--%s\n' % b))
            t.append('\n--%s--\n' % b)
            t=join(t,'')
            s.append('Content-Length: %s\r\n\r\n' % len(t))
            s.append(t)
            return join(s,'')

        else:
            for n,v in h.items():
                if v['_v']:
                    s.append('%s: %s' % (n,v['_v']))
                    for k in v.keys():
                        if k != '_v': s.append('; %s=%s' % (k, v[k]))
                    s.append('\r\n')
            s.append('\r\n')

            if self._boundary:
                p=[]
                b=self._boundary
                for d in self._data: p.append(d.render())
                s.append('--%s\n' % b)
                s.append(join(p,'\n--%s\n' % b))
                s.append('\n--%s--\n' % b)
                return join(s,'')
            else:
                return join(s+self._data,'')


    _extmap={'':     'text/plain',
             'rdb':  'text/plain',
             'html': 'text/html',
             'dtml': 'text/html',
             'htm':  'text/html',
             'dtm':  'text/html',
             'gif':  'image/gif',
             'jpg':  'image/jpeg',
             'exe':  'application/octet-stream',
             None :  'application/octet-stream',
             }

    _encmap={'image/gif': 'binary',
             'image/jpg': 'binary',
             'application/octet-stream': 'binary',
             }


def ErrorTypes(code):
    if code >= 400 and code < 500: return NotFound
    if code >= 500 and code < 600: return ServerError
    return 'HTTP_Error_%s' % code

usage="""
Usage: %s [-u username:password] url [name=value ...]

where url is the web resource to call.

The -u option may be used to provide a user name and password.

Optional arguments may be provides as name=value pairs.

In a name value pair, if a name ends in ":file", then the value is
treated as a file name and the file is send using the file-upload
protocol.   If the file name is "-", then data are taken from standard
input.

The body of the response is written to standard output.
The headers of the response are written to standard error.

""" % sys.argv[0]

def main():
    import getopt
    from string import split

    user=None

    try:
        optlist, args = getopt.getopt(sys.argv[1:],'u:')
        url=args[0]
        u =filter(lambda o: o[0]=='-u', optlist)
        if u:
            [user, pw] = split(u[0][1],':')

        kw={}
        for arg in args[1:]:
            [name,v]=split(arg,'=')
            if name[-5:]==':file':
                name=name[:-5]
                if v=='-': v=sys.stdin
                else: v=open(v)
            kw[name]=v

    except:
        print usage
        sys.exit(1)
        
    # The "main" program for this module
    f=Function(url)
    if user: f.username, f.password = user, pw
    headers, body = apply(f,(),kw)
    sys.stderr.write(join(map(lambda h: "%s: %s\n" % h, headers.items()),"")
                     +"\n\n")
    print body


if __name__ == "__main__":
    main()
