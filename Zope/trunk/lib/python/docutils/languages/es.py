# Author: Marcelo Huerta San Mart�n
# Contact: mghsm@uol.com.ar
# Revision: $Revision: 1.1 $
# Date: $Date: 2003/07/10 15:49:34 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/spec/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
Spanish-language mappings for language-dependent features of Docutils.
"""

__docformat__ = 'reStructuredText'

labels = {
      'author': u'Autor',
      'authors': u'Autores',
      'organization': u'Organizaci\u00f3n',
      'address': u'Direcci\u00f3n',
      'contact': u'Contacto',
      'version': u'Versi\u00f3n',
      'revision': u'Revisi\u00f3n',
      'status': u'Estado',
      'date': u'Fecha',
      'copyright': u'Copyright',
      'dedication': u'Dedicatoria',
      'abstract': u'Resumen',
      'attention': u'\u00a1Atenci\u00f3n!',
      'caution': u'\u00a1Precauci\u00f3n!',
      'danger': u'\u00a1PELIGRO!',
      'error': u'Error',
      'hint': u'Sugerencia',
      'important': u'Importante',
      'note': u'Nota',
      'tip': u'Consejo',
      'warning': u'Advertencia',
      'contents': u'Contenido'}
"""Mapping of node class name to label text."""

bibliographic_fields = {
      u'autor': 'author',
      u'autores': 'authors',
      u'organizaci\u00f3n': 'organization',
      u'direcci\u00f3n': 'address',
      u'contacto': 'contact',
      u'versi\u00f3n': 'version',
      u'revisi\u00f3n': 'revision',
      u'estado': 'status',
      u'fecha': 'date',
      u'copyright': 'copyright',
      u'dedicatoria': 'dedication',
      u'resumen': 'abstract'}
"""Spanish (lowcased) to canonical name mapping for bibliographic fields."""

author_separators = [';', ',']
"""List of separator strings for the 'Authors' bibliographic field. Tried in
order."""
