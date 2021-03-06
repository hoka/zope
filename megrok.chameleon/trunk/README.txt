================
megrok.chameleon
================

.. NOTE::
   megrok.chameleon has been promoted to grokcore.chameleon and will be a part
   of the Grok from the upcomming Grok release on. The grokcore.chameleon
   package can already be included in your own projects in the meantime. This
   means this package most likely will not see any further updates.

`megrok.chameleon` makes it possible to use Chameleon page templates in Grok.
For more information on Grok and Chameleon page templates see:

- http://pagetemplates.org/
- http://pagetemplates.org/docs/latest/
- http://pypi.python.org/pypi/Chameleon
- http://grok.zope.org/

.. contents::

Installation
============

To use Chameleon page templates with Grok all you need is to install
megrok.chameleon as an egg and include its ZCML. The best place to do
this is to make `megrok.chameleon` a dependency of your application by
adding it to your ``install_requires`` list in ``setup.cfg``. If you
used grokproject to create your application ``setup.py`` is located in the
project root. It should look something like this::

   install_requires=['setuptools',
                     'megrok.chameleon',
                     # Add extra requirements here
                     ],

Note that if you use the ``allow-picked-versions = false`` directive in your
project's ``buildout.cfg``, you will have to add version number specifications
for several packages to your ``[versions]`` section.

Then include ``megrok.chameleon`` in your ``configure.zcml``. If you used
grokproject to create your application it's at
``src/<projectname>/configure.zcml``. Add the include line after the include
line for grok, but before the grokking of the current package. It should look
something like this::

      <include package="grok" />
      <include package="megrok.chameleon" />
      <grok:grok package="." />

If you use ``autoInclude`` in your ``configure.zcml``, you should not
have to do this latter step.

Then run ``bin/buildout`` again. You should now see buildout saying
something like (where version numbers can vary)::

   Getting distribution for 'megrok.chameleon'.
   Got megrok.chameleon 0.5.

That's all. You can now start using Chameleon page templates in your
Grok application.

Usage
=====

``megrok.chameleon`` supports the Grok standard of placing templates in a
templates directory, for example ``app_templates``, so you can use Chameleon
page templates by simply placing the Chameleon page templates in the templates
directory, just as you would with regular ZPT templates.

Although chameleon templates themselves do not have a standard for the file
extensions for templates, Grok needs to have an association between an filename
extension and a template language implementation so it knows which
implementation to use.

`megrok.chameleon` declares to use the extension ``*.cpt`` (``Chameleon page
template``) for Chameleon page templates.

You can also use Chameleon page templates inline. The syntax for this
is::

   from megrok.chameleon.components import ChameleonPageTemplate
   index = ChameleonPageTemplate('<html>the html code</html>')

Or if you use files::

   from megrok.genshi.components import ChameleonPageTemplateFile
   index = ChameleonPageTemplateFile(filename='thefilename.html')
