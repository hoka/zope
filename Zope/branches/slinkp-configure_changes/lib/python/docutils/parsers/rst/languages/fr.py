# Authors: David Goodger; William Dode
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.2.10.3.8.1 $
# Date: $Date: 2004/05/12 19:57:51 $
# Copyright: This module has been placed in the public domain.

# New language mappings are welcome.  Before doing a new translation, please
# read <http://docutils.sf.net/spec/howto/i18n.html>.  Two files must be
# translated for each language: one in docutils/languages, the other in
# docutils/parsers/rst/languages.

"""
French-language mappings for language-dependent features of
reStructuredText.
"""

__docformat__ = 'reStructuredText'


directives = {
      u'attention': 'attention',
      u'pr\u00E9caution': 'caution',
      u'danger': 'danger',
      u'erreur': 'error',
      u'conseil': 'hint',
      u'important': 'important',
      u'note': 'note',
      u'astuce': 'tip',
      u'avertissement': 'warning',
      u'admonition': 'admonition',
      u'encadr\u00E9': 'sidebar',
      u'sujet': 'topic',
      u'bloc-textuel': 'line-block',
      u'bloc-interpr\u00E9t\u00E9': 'parsed-literal',
      u'code-interpr\u00E9t\u00E9': 'parsed-literal',
      u'intertitre': 'rubric',
      u'exergue': 'epigraph',
      u'\u00E9pigraphe': 'epigraph',
      u'chapeau': 'highlights',
      u'accroche': 'pull-quote',
      u'tableau': 'table',
      #u'questions': 'questions',
      #u'qr': 'questions',
      #u'faq': 'questions',
      u'm\u00E9ta': 'meta',
      #u'imagemap (translation required)': 'imagemap',
      u'image': 'image',
      u'figure': 'figure',
      u'inclure': 'include',
      u'brut': 'raw',
      u'remplacer': 'replace',
      u'remplace': 'replace',
      u'unicode': 'unicode',
      u'classe': 'class',
      u'role (translation required)': 'role',
      u'sommaire': 'contents',
      u'table-des-mati\u00E8res': 'contents',
      u'sectnum': 'sectnum',
      u'section-num\u00E9rot\u00E9e': 'sectnum',
      u'liens': 'target-notes',
      #u'footnotes (translation required)': 'footnotes',
      #u'citations (translation required)': 'citations',
      }
"""French name to registered (in directives/__init__.py) directive name
mapping."""

roles = {
      u'abr\u00E9viation': 'abbreviation',
      u'acronyme': 'acronym',
      u'sigle': 'acronym',
      u'index': 'index',
      u'indice': 'subscript',
      u'ind': 'subscript',
      u'exposant': 'superscript',
      u'exp': 'superscript',
      u'titre-r\u00E9f\u00E9rence': 'title-reference',
      u'titre': 'title-reference',
      u'pep-r\u00E9f\u00E9rence': 'pep-reference',
      u'rfc-r\u00E9f\u00E9rence': 'rfc-reference',
      u'emphase': 'emphasis',
      u'fort': 'strong',
      u'litt\u00E9ral': 'literal',
      u'nomm\u00E9e-r\u00E9f\u00E9rence': 'named-reference',
      u'anonyme-r\u00E9f\u00E9rence': 'anonymous-reference',
      u'note-r\u00E9f\u00E9rence': 'footnote-reference',
      u'citation-r\u00E9f\u00E9rence': 'citation-reference',
      u'substitution-r\u00E9f\u00E9rence': 'substitution-reference',
      u'lien': 'target',
      u'uri-r\u00E9f\u00E9rence': 'uri-reference',}
"""Mapping of French role names to canonical role names for interpreted text.
"""
