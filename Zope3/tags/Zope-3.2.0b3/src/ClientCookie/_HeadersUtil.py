"""Utility functions for HTTP header value parsing and construction.

Copyright 1997-1998, Gisle Aas
Copyright 2002-2004, John J. Lee

This code is free software; you can redistribute it and/or modify it under
the terms of the BSD License (see the file COPYING included with the
distribution).

"""

import re, string
from types import StringType
try:
    from types import UnicodeType
    STRING_TYPES = StringType, UnicodeType
except:
    STRING_TYPES = StringType,

from _Util import startswith, endswith, http2time

try: True
except NameError:
    True = 1
    False = 0

def is_html(ct_headers, url):
    """
    ct_headers: Sequence of Content-Type headers
    url: Response URL

    """
    if not ct_headers:
        # guess
        return (url.endswith('.htm') or url.endswith('.html') or
                url.endswith('.xhtml'))
    # use first header
    ct = split_header_words(ct_headers)[0][0][0]
    return ct in [
        "text/html", "text/xhtml", "text/xml",
        "application/xml", "application/xhtml+xml",
        ]

def unmatched(match):
    """Return unmatched part of re.Match object."""
    start, end = match.span(0)
    return match.string[:start]+match.string[end:]

token_re =        re.compile(r"^\s*([^=\s;,]+)")
quoted_value_re = re.compile(r"^\s*=\s*\"([^\"\\]*(?:\\.[^\"\\]*)*)\"")
value_re =        re.compile(r"^\s*=\s*([^\s;,]*)")
escape_re = re.compile(r"\\(.)")
def split_header_words(header_values):
    r"""Parse header values into a list of lists containing key,value pairs.

    The function knows how to deal with ",", ";" and "=" as well as quoted
    values after "=".  A list of space separated tokens are parsed as if they
    were separated by ";".

    If the header_values passed as argument contains multiple values, then they
    are treated as if they were a single value separated by comma ",".

    This means that this function is useful for parsing header fields that
    follow this syntax (BNF as from the HTTP/1.1 specification, but we relax
    the requirement for tokens).

      headers           = #header
      header            = (token | parameter) *( [";"] (token | parameter))

      token             = 1*<any CHAR except CTLs or separators>
      separators        = "(" | ")" | "<" | ">" | "@"
                        | "," | ";" | ":" | "\" | <">
                        | "/" | "[" | "]" | "?" | "="
                        | "{" | "}" | SP | HT

      quoted-string     = ( <"> *(qdtext | quoted-pair ) <"> )
      qdtext            = <any TEXT except <">>
      quoted-pair       = "\" CHAR

      parameter         = attribute "=" value
      attribute         = token
      value             = token | quoted-string

    Each header is represented by a list of key/value pairs.  The value for a
    simple token (not part of a parameter) is None.  Syntactically incorrect
    headers will not necessarily be parsed as you would want.

    This is easier to describe with some examples:

    >>> split_header_words(['foo="bar"; port="80,81"; discard, bar=baz'])
    [[('foo', 'bar'), ('port', '80,81'), ('discard', None)], [('bar', 'baz')]]
    >>> split_header_words(['text/html; charset="iso-8859-1"'])
    [[('text/html', None), ('charset', 'iso-8859-1')]]
    >>> split_header_words([r'Basic realm="\"foo\bar\""'])
    [[('Basic', None), ('realm', '"foobar"')]]

    """
    assert type(header_values) not in STRING_TYPES
    result = []
    for text in header_values:
        orig_text = text
        pairs = []
        while text:
            m = token_re.search(text)
            if m:
                text = unmatched(m)
                name = m.group(1)
                m = quoted_value_re.search(text)
                if m:  # quoted value
                    text = unmatched(m)
                    value = m.group(1)
                    value = escape_re.sub(r"\1", value)
                else:
                    m = value_re.search(text)
                    if m:  # unquoted value
                        text = unmatched(m)
                        value = m.group(1)
                        value = string.rstrip(value)
                    else:
                        # no value, a lone token
                        value = None
                pairs.append((name, value))
            elif startswith(string.lstrip(text), ","):
                # concatenated headers, as per RFC 2616 section 4.2
                text = string.lstrip(text)[1:]
                if pairs: result.append(pairs)
                pairs = []
            else:
                # skip junk
                non_junk, nr_junk_chars = re.subn("^[=\s;]*", "", text)
                assert nr_junk_chars > 0, (
                    "split_header_words bug: '%s', '%s', %s" %
                    (orig_text, text, pairs))
                text = non_junk
        if pairs: result.append(pairs)
    return result

join_escape_re = re.compile(r"([\"\\])")
def join_header_words(lists):
    """Do the inverse of the conversion done by split_header_words.

    Takes a list of lists of (key, value) pairs and produces a single header
    value.  Attribute values are quoted if needed.

    >>> join_header_words([[("text/plain", None), ("charset", "iso-8859/1")]])
    'text/plain; charset="iso-8859/1"'
    >>> join_header_words([[("text/plain", None)], [("charset", "iso-8859/1")]])
    'text/plain, charset="iso-8859/1"'

    """
    headers = []
    for pairs in lists:
        attr = []
        for k, v in pairs:
            if v is not None:
                if not re.search(r"^\w+$", v):
                    v = join_escape_re.sub(r"\\\1", v)  # escape " and \
                    v = '"%s"' % v
                if k is None:  # Netscape cookies may have no name
                    k = v
                else:
                    k = "%s=%s" % (k, v)
            attr.append(k)
        if attr: headers.append(string.join(attr, "; "))
    return string.join(headers, ", ")

def parse_ns_headers(ns_headers):
    """Ad-hoc parser for Netscape protocol cookie-attributes.

    The old Netscape cookie format for Set-Cookie can for instance contain
    an unquoted "," in the expires field, so we have to use this ad-hoc
    parser instead of split_header_words.

    XXX This may not make the best possible effort to parse all the crap
    that Netscape Cookie headers contain.  Ronald Tschalar's HTTPClient
    parser is probably better, so could do worse than following that if
    this ever gives any trouble.

    Currently, this is also used for parsing RFC 2109 cookies.

    """
    known_attrs = ("expires", "domain", "path", "secure",
                   # RFC 2109 attrs (may turn up in Netscape cookies, too)
                   "port", "max-age")

    result = []
    for ns_header in ns_headers:
        pairs = []
        version_set = False
        params = re.split(r";\s*", ns_header)
        for ii in range(len(params)):
            param = params[ii]
            param = string.rstrip(param)
            if param == "": continue
            if "=" not in param:
                k, v = param, None
            else:
                k, v = re.split(r"\s*=\s*", param, 1)
                k = string.lstrip(k)
            if ii != 0:
                lc = string.lower(k)
                if lc in known_attrs:
                    k = lc
                if k == "version":
                    # This is an RFC 2109 cookie.
                    version_set = True
                if k == "expires":
                    # convert expires date to seconds since epoch
                    if startswith(v, '"'): v = v[1:]
                    if endswith(v, '"'): v = v[:-1]
                    v = http2time(v)  # None if invalid
            pairs.append((k, v))

        if pairs:
            if not version_set:
                pairs.append(("version", "0"))
            result.append(pairs)

    return result


def _test():
   import doctest, _HeadersUtil
   return doctest.testmod(_HeadersUtil)

if __name__ == "__main__":
   _test()
