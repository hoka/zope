"""
Inline templates that are not associated with a view class will
provoke an error:

  >>> grok.grok(__name__)
  Traceback (most recent call last):
  ...
  GrokError: Found the following unassociated template(s) when grokking
  'grok.tests.view.inline_unassociated': club.  Define view classes inheriting
  from grok.View to enable the template(s).

"""
import grok

class Mammoth(grok.Model):
    pass

club = grok.PageTemplate("""\
<html><body><h1>GROK CLUB MAMMOTH!</h1></body></html>
""")
