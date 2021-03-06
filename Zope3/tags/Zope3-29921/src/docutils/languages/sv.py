# Author:    Adam Chodorowski
# Contact:   chodorowski@users.sourceforge.net
# Revision:  $Revision: 1.1 $
# Date:      $Date: 2003/07/30 20:14:05 $
# Copyright: This module has been placed in the public domain.

"""
Swedish language mappings for language-dependent features of Docutils.
"""

__docformat__ = 'reStructuredText'

labels = {
    'author':       u'F\u00f6rfattare',
    'authors':      u'F\u00f6rfattare',
    'organization': u'Organisation',
    'address':      u'Adress',
    'contact':      u'Kontakt',
    'version':      u'Version',
    'revision':     u'Revision',
    'status':       u'Status',
    'date':         u'Datum',
    'copyright':    u'Copyright',
    'dedication':   u'Dedikation',
    'abstract':     u'Sammanfattning',
    'attention':    u'Observera!',
    'caution':      u'Varning!',
    'danger':       u'FARA!',
    'error':        u'Fel',
    'hint':         u'V\u00e4gledning',
    'important':    u'Viktigt',
    'note':         u'Notera',
    'tip':          u'Tips',
    'warning':      u'Varning',
    'contents':     u'Inneh\u00e5ll' }
"""Mapping of node class name to label text."""

bibliographic_fields = {
    # 'Author' and 'Authors' identical in Swedish; assume the plural:
    u'f\u00f6rfattare': 'authors',
    u'organisation':    'organization',
    u'adress':          'address',
    u'kontakt':         'contact',
    u'version':         'version',
    u'revision':        'revision',
    u'status':          'status',
    u'datum':           'date',
    u'copyright':       'copyright',
    u'dedikation':      'dedication', 
    u'sammanfattning':  'abstract' }
"""Swedish (lowcased) to canonical name mapping for bibliographic fields."""

author_separators = [';', ',']
"""List of separator strings for the 'Authors' bibliographic field. Tried in
order."""
