=========
Z3C Table
=========

The goal of the ``z3c.table`` package is to offer a modular table
rendering library. We use the content provider pattern with columns
implemented as adapters.  This gives us a powerfull base concept.


Important Requirements
----------------------

- separate implementation in update render parts, This allows to manipulate
  data after update call and before we render them.

- We can use page templates if needed, but everything is done in
  Python by default.

- We can render batching navigation separately from the table itself.


No skins
--------

This package does not provide any kind of templates or skins. Most of
the time, when you need to render a nice looking table, you will end
up writing your own custom skin or template anyway.  Having no
templates or skins ensures that ``z3c.table`` has very few package
dependencies and is thereby easily reusable.


Note
----

As you probably know, when batching of table rows is combined with
sorting of table columns, a full sort of all the data must be done
before batches can be created.  This can cause performance problems
with large data sets.  It is recommended that when working with large
data sets, you either do not combine batching and sorting, or provide
some intelligent caching method for storing sort order.


Sample Data Setup
-----------------

Tables are often used to display normalized bits of data.  For
example, we might want to display information about files in a folder.
Each file has a title, a size and a file type.  Our table would then
have a row for each file and a column for each normalized bit of data
about the file (title, size, and type).  Thus the context of a table is
always some iterable data structure that represents the rows of the
table.  Let's create a sample folder that we can use as our
iterable context:

  >>> from zope.app.container import btree
  >>> class Folder(btree.BTreeContainer):
  ...     """Sample folder."""
  ...     __name__ = u'folder'
  >>> folder = Folder()

XXX: not sure we need to put the folder anywhere yet.  Nor do we need
to give it a __name__ value.  We shouldn't need to locate it.
and set a parent for the folder:

  >>> root['folder'] = folder

Now we will create a sample ``File`` object to store in our folders.

  >>> class File(object):
  ...     """Sample file."""
  ...     def __init__(self, title, size, type=None):
  ...         self.title = title
  ...         self.number = size
  ...         self.type = type

Now we'll go ahead and set up our folder with some files.

  >>> folder[u'first'] = File('First', 1)
  >>> folder[u'second'] = File('Second', 2)
  >>> folder[u'third'] = File('Third', 3)


Creating Tables
---------------

Now that we have some sample data to work with, we can now create a
table.  Since tables are UI components, they require both a context
and a request.  These are taken as arguments to the ``Table`` class's
constructor.

  >>> from zope.publisher.browser import TestRequest
  >>> from z3c.table import table
  >>> request = TestRequest()
  >>> plainTable = table.Table(folder, request)

Once the table has been instantiated, we can update and render
it. Since we have not specified any columns for the table to render,
the table just renders to an empty string:

  >>> plainTable.update()
  >>> plainTable.render()
  u''

We should also note that the ``Table`` class is an implementation of
the ``ITable`` interface.  It will be more interesting to look at what
``ITable`` provides when we have some columns.

  >>> from z3c.table import interfaces
  >>> from zope.interface.verify import verifyObject
  >>> verifyObject(interfaces.ITable, plainTable)
  True


Creating Columns
----------------

Since we may want the same type of column to appear in many different
tables, the definition for a column lives separately from the table
itself.  Every type of column is represented as its own class
implementing the ``IColumn`` interface.  To help us define a column,
there is the ``Column`` baseclass.  A simple column that displays the
current items title would look something like this:

  >>> from z3c.table import column
  >>> class TitleColumn(column.Column):
  ...
  ...     weight = 10
  ...     header = u'Title'
  ...
  ...     def renderCell(self, item):
  ...         return u'Title: %s' % item.title

The ``header`` attribute is the text that appears in column's header,
typically a ``<th>`` tag.  The ``weight`` attribute specifies the
order of the column in the table, relative to the weights of other
columns.  The ``renderCell`` method does the heavy lifting, returning
the html structure that will appear inside the table cell, typically a
``<td>`` tag.  The ``renderCell`` method must be provided by
subclasses of ``Column``.


Adding a Column to a Table Using Adapters
-----------------------------------------

One way we can add a column to a table is using an adapter.  Although
this may seem like overkill at first, it makes tables easily
pluggable.  Let's register our column as an adapter.

  >>> import zope.component
  >>> zope.component.provideAdapter(TitleColumn,
  ...     (None, None, interfaces.ITable), provides=interfaces.IColumn,
  ...      name='firstColumn')

Now we can render the table again:

  >>> plainTable.update()
  >>> print plainTable.render()
  <table>
    <thead>
      <tr>
        <th>Title</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Title: First</td>
      </tr>
      <tr>
        <td>Title: Second</td>
      </tr>
      <tr>
        <td>Title: Third</td>
      </tr>
    </tbody>
  </table>

We can also use the predefined name column:

  >>> zope.component.provideAdapter(column.NameColumn,
  ...     (None, None, interfaces.ITable), provides=interfaces.IColumn,
  ...      name='secondColumn')

Now we will get a nother additional column:

  >>> plainTable.update()
  >>> print plainTable.render()
  <table>
    <thead>
      <tr>
        <th>Name</th>
        <th>Title</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>first</td>
        <td>Title: First</td>
      </tr>
      <tr>
        <td>second</td>
        <td>Title: Second</td>
      </tr>
      <tr>
        <td>third</td>
        <td>Title: Third</td>
      </tr>
    </tbody>
  </table>


Colspan
-------

Now let's show how we can define a colspan condition of 2 for an column:

  >>> class ColspanColumn(column.NameColumn):
  ...
  ...     weight = 999
  ...
  ...     def getColspan(self, item):
  ...         # colspan condition
  ...         if item.__name__ == 'first':
  ...             return 2
  ...         else:
  ...             return 0
  ...
  ...     def renderHeadCell(self):
  ...         return u'Colspan'
  ...
  ...     def renderCell(self, item):
  ...         return u'colspan: %s' % item.title

Now we register this column adapter as colspanColumn:

  >>> zope.component.provideAdapter(ColspanColumn,
  ...     (None, None, interfaces.ITable), provides=interfaces.IColumn,
  ...      name='colspanColumn')


Now you can see that the colspan of the ColspanAdapter is larger then the table
columns. This wil raise a VlaueError:

  >>> plainTable.update()
  Traceback (most recent call last):
  ...
  ValueError: Colspan for column '<ColspanColumn u'colspanColumn'>' larger then table.

But if we set the column as first row, it weill render the colspan correct:

  >>> class CorrectColspanColumn(ColspanColumn):
  ...     """Colspan with correct weight."""
  ...
  ...     weight = 0

Register and render the table again:

  >>> zope.component.provideAdapter(CorrectColspanColumn,
  ...     (None, None, interfaces.ITable), provides=interfaces.IColumn,
  ...      name='colspanColumn')

  >>> plainTable.update()
  >>> print plainTable.render()
  <table>
    <thead>
      <tr>
        <th>Colspan</th>
        <th>Name</th>
        <th>Title</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td colspan="2">colspan: First</td>
        <td>Title: First</td>
      </tr>
      <tr>
        <td>colspan: Second</td>
        <td>second</td>
        <td>Title: Second</td>
      </tr>
      <tr>
        <td>colspan: Third</td>
        <td>third</td>
        <td>Title: Third</td>
      </tr>
    </tbody>
  </table>

Setup columns
-------------

The existing implementation allows us to define a table in a class without
to use the modular adapter pattern for columns.

First we need to define a column which cna render a value for our items:

  >>> class SimpleColumn(column.Column):
  ...
  ...     weight = 0
  ...
  ...     def renderCell(self, item):
  ...         return item.title

Let's define our table which defines the columns explicit. you can also see,
that we do not return the columns in the correct order:

  >>> class PrivateTable(table.Table):
  ...
  ...     def setUpColumns(self):
  ...         firstColumn = TitleColumn(self.context, self.request, self)
  ...         firstColumn.__name__ = u'title'
  ...         firstColumn.weight = 1
  ...         secondColumn = SimpleColumn(self.context, self.request, self)
  ...         secondColumn.__name__ = u'simple'
  ...         secondColumn.weight = 2
  ...         secondColumn.header = u'The second column'
  ...         return [secondColumn, firstColumn]

Now we can create, update and render the table and see that this renders a nice
table too:

  >>> privateTable = PrivateTable(folder, request)
  >>> privateTable.update()
  >>> print privateTable.render()
  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>The second column</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Title: First</td>
        <td>First</td>
      </tr>
      <tr>
        <td>Title: Second</td>
        <td>Second</td>
      </tr>
      <tr>
        <td>Title: Third</td>
        <td>Third</td>
      </tr>
    </tbody>
  </table>


Cascading Style Sheet
---------------------

Our table and column implementation supports css class assignment. Let's define
a table and columns with some css class values:

  >>> class CSSTable(table.Table):
  ...
  ...     cssClasses = {'table': 'table',
  ...                   'thead': 'thead',
  ...                   'tbody': 'tbody',
  ...                   'th': 'th',
  ...                   'tr': 'tr',
  ...                   'td': 'td'}
  ...
  ...     def setUpColumns(self):
  ...         firstColumn = TitleColumn(self.context, self.request, self)
  ...         firstColumn.__name__ = u'title'
  ...         firstColumn.__parent__ = self
  ...         firstColumn.weight = 1
  ...         firstColumn.cssClasses = {'th':'thCol', 'td':'tdCol'}
  ...         secondColumn = SimpleColumn(self.context, self.request, self)
  ...         secondColumn.__name__ = u'simple'
  ...         secondColumn.__parent__ = self
  ...         secondColumn.weight = 2
  ...         secondColumn.header = u'The second column'
  ...         return [secondColumn, firstColumn]

Now let's see if we got the cs class assigned which we defined in the table and
column. Note that the ``th`` and ``td`` got CSS declarations from the table and
from the column.

  >>> cssTable = CSSTable(folder, request)
  >>> cssTable.update()
  >>> print cssTable.render()
  <table class="table">
    <thead class="thead">
      <tr class="tr">
        <th class="thCol th">Title</th>
        <th class="th">The second column</th>
      </tr>
    </thead>
    <tbody class="tbody">
      <tr class="tr">
        <td class="tdCol td">Title: First</td>
        <td class="td">First</td>
      </tr>
      <tr class="tr">
        <td class="tdCol td">Title: Second</td>
        <td class="td">Second</td>
      </tr>
      <tr class="tr">
        <td class="tdCol td">Title: Third</td>
        <td class="td">Third</td>
      </tr>
    </tbody>
  </table>


Alternating table
-----------------

We offer built in support for alternating table rows based on even and odd CSS
classes. Let's define a table including other CSS classes. For even/odd support,
we only need to define the ``cssClassEven`` and ``cssClassOdd`` CSS classes:

  >>> class AlternatingTable(table.Table):
  ...
  ...     cssClasses = {'table': 'table',
  ...                   'thead': 'thead',
  ...                   'tbody': 'tbody',
  ...                   'th': 'th',
  ...                   'tr': 'tr',
  ...                   'td': 'td'}
  ...
  ...     cssClassEven = u'even'
  ...     cssClassOdd = u'odd'
  ...
  ...     def setUpColumns(self):
  ...         firstColumn = TitleColumn(self.context, self.request, self)
  ...         firstColumn.__name__ = u'title'
  ...         firstColumn.__parent__ = self
  ...         firstColumn.weight = 1
  ...         firstColumn.cssClasses = {'th':'thCol', 'td':'tdCol'}
  ...         secondColumn = SimpleColumn(self.context, self.request, self)
  ...         secondColumn.__name__ = u'simple'
  ...         secondColumn.__parent__ = self
  ...         secondColumn.weight = 2
  ...         secondColumn.header = u'The second column'
  ...         return [secondColumn, firstColumn]

Now update and render the new table. As you can see the given ``tr`` class get
used additional to the even and odd classes:

  >>> alternatingTable = AlternatingTable(folder, request)
  >>> alternatingTable.update()
  >>> print alternatingTable.render()
  <table class="table">
    <thead class="thead">
      <tr class="tr">
        <th class="thCol th">Title</th>
        <th class="th">The second column</th>
      </tr>
    </thead>
    <tbody class="tbody">
      <tr class="even tr">
        <td class="tdCol td">Title: First</td>
        <td class="td">First</td>
      </tr>
      <tr class="odd tr">
        <td class="tdCol td">Title: Second</td>
        <td class="td">Second</td>
      </tr>
      <tr class="even tr">
        <td class="tdCol td">Title: Third</td>
        <td class="td">Third</td>
      </tr>
    </tbody>
  </table>


Sorting Table
-------------

Another table feature is the support for sorting data given from columns. Since
sorting table data is an important feature, we offer this by default. But it
only gets used if there is a sortOn value set. You can set this value at class
level by adding a defaultSortOn value or set it as a request value. We show you
how to do this later. We also need a columns which allows us to do a better
sort sample. Our new sorting column will use the content items number value
for sorting:

  >>> class NumberColumn(column.Column):
  ...
  ...     header = u'Number'
  ...     weight = 20
  ...
  ...     def getSortKey(self, item):
  ...         return item.number
  ...
  ...     def renderCell(self, item):
  ...         return 'number: %s' % item.number


Now let's setup a table:

  >>> class SortingTable(table.Table):
  ...
  ...     def setUpColumns(self):
  ...         firstColumn = TitleColumn(self.context, self.request, self)
  ...         firstColumn.__name__ = u'title'
  ...         firstColumn.__parent__ = self
  ...         secondColumn = NumberColumn(self.context, self.request, self)
  ...         secondColumn.__name__ = u'number'
  ...         secondColumn.__parent__ = self
  ...         return [firstColumn, secondColumn]

We also need some more container items which we can use for sorting:

  >>> folder[u'fourth'] = File('Fourth', 4)
  >>> folder[u'zero'] = File('Zero', 0)

And render them without set a sortOn value:

  >>> sortingTable = SortingTable(folder, request)
  >>> sortingTable.update()
  >>> print sortingTable.render()
  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Title: First</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Title: Fourth</td>
        <td>number: 4</td>
      </tr>
      <tr>
        <td>Title: Second</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Title: Third</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Title: Zero</td>
        <td>number: 0</td>
      </tr>
    </tbody>
  </table>

As you can see this table doesn't provide any explicit order. Let's find out
the index of our column which we like to sort on:

  >>> sortOnId = sortingTable.rows[0][1][1].id
  >>> sortOnId
  u'table-number-1'

And let's ues this id as ``sortOn`` value:

  >>> sortingTable.sortOn = sortOnId

An important thing is to update the table after set an sort on value:

  >>> sortingTable.update()
  >>> print sortingTable.render()
  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Title: Zero</td>
        <td>number: 0</td>
      </tr>
      <tr>
        <td>Title: First</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Title: Second</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Title: Third</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Title: Fourth</td>
        <td>number: 4</td>
      </tr>
    </tbody>
  </table>

We can also reverse the sort order:

  >>> sortingTable.sortOrder = 'reverse'
  >>> sortingTable.update()
  >>> print sortingTable.render()
  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Title: Fourth</td>
        <td>number: 4</td>
      </tr>
      <tr>
        <td>Title: Third</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Title: Second</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Title: First</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Title: Zero</td>
        <td>number: 0</td>
      </tr>
    </tbody>
  </table>

The table implementation is also able to get the sort criteria given from a
request. Let's setup such a request:

  >>> sorterRequest = TestRequest(form={'table-sortOn': 'table-number-1',
  ...                                   'table-sortOrder':'descending'})

and another time, update and render. As you can see the new table get sorted
by the second column and ordered in reverse order:

  >>> requestSortedTable = SortingTable(folder, sorterRequest)
  >>> requestSortedTable.update()
  >>> print requestSortedTable.render()
  <table>
    <thead>
      <tr>
        <th>Title</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Title: Fourth</td>
        <td>number: 4</td>
      </tr>
      <tr>
        <td>Title: Third</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Title: Second</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Title: First</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Title: Zero</td>
        <td>number: 0</td>
      </tr>
    </tbody>
  </table>


Class based Table setup
-----------------------

There is a more elegant way to define table rows at class level. We offer
a method which you can use if you need to define some columns called
``addTable``. Before we define the table. let's define some cell renderer:

  >>> def headCellRenderer():
  ...     return u'My items'

  >>> def cellRenderer(item):
  ...     return u'%s item' % item.title

Now we can define our table and use the custom cell renderer:

  >>> class AddColumnTable(table.Table):
  ...
  ...     cssClasses = {'table': 'table',
  ...                   'thead': 'thead',
  ...                   'tbody': 'tbody',
  ...                   'th': 'th',
  ...                   'tr': 'tr',
  ...                   'td': 'td'}
  ...
  ...     cssClassEven = u'even'
  ...     cssClassOdd = u'odd'
  ...
  ...     def setUpColumns(self):
  ...         return [
  ...             column.addColumn(self, TitleColumn, u'title',
  ...                              cellRenderer=cellRenderer,
  ...                              headCellRenderer=headCellRenderer,
  ...                              weight=1, colspan=0),
  ...             column.addColumn(self, SimpleColumn, name=u'simple',
  ...                              weight=2, header=u'The second column',
  ...                              cssClasses = {'th':'thCol', 'td':'tdCol'})
  ...             ]

  >>> addColumnTable = AddColumnTable(folder, request)
  >>> addColumnTable.update()
  >>> print addColumnTable.render()
  <table class="table">
    <thead class="thead">
      <tr class="tr">
        <th class="th">My items</th>
        <th class="thCol th">The second column</th>
      </tr>
    </thead>
    <tbody class="tbody">
      <tr class="even tr">
        <td class="td">First item</td>
        <td class="tdCol td">First</td>
      </tr>
      <tr class="odd tr">
        <td class="td">Fourth item</td>
        <td class="tdCol td">Fourth</td>
      </tr>
      <tr class="even tr">
        <td class="td">Second item</td>
        <td class="tdCol td">Second</td>
      </tr>
      <tr class="odd tr">
        <td class="td">Third item</td>
        <td class="tdCol td">Third</td>
      </tr>
      <tr class="even tr">
        <td class="td">Zero item</td>
        <td class="tdCol td">Zero</td>
      </tr>
    </tbody>
  </table>

As you can see the table columns provide all attributes we set in the addColumn
method:

  >>> titleColumn = addColumnTable.rows[0][0][1]
  >>> titleColumn
  <TitleColumn u'title'>

  >>> titleColumn.__name__
  u'title'

  >>> titleColumn.__parent__
  <AddColumnTable None>

  >>> titleColumn.colspan
  0

  >>> titleColumn.weight
  1

  >>> titleColumn.header
  u'Title'

  >>> titleColumn.cssClasses
  {}

and the second column

  >>> simpleColumn = addColumnTable.rows[0][1][1]
  >>> simpleColumn
  <SimpleColumn u'simple'>

  >>> simpleColumn.__name__
  u'simple'

  >>> simpleColumn.__parent__
  <AddColumnTable None>

  >>> simpleColumn.colspan
  0

  >>> simpleColumn.weight
  2

  >>> simpleColumn.header
  u'The second column'

  >>> simpleColumn.cssClasses
  {'td': 'tdCol', 'th': 'thCol'}


Batching
--------

Or table implements a concept for batching out of the box. If the amount of
row items is smaller then the given ``startBatchingAt`` size, the table starts
to batch at this size. Let's define a new Table:

We need to configure our batch provider for the next step first. See the
section ``BatchProvider`` below for more infos about batch rendering:

  >>> from zope.configuration.xmlconfig import XMLConfig
  >>> import zope.app.component
  >>> import z3c.table
  >>> XMLConfig('meta.zcml', zope.component)()
  >>> XMLConfig('configure.zcml', z3c.table)()

  >>> class BatchingTable(table.Table):
  ...
  ...     def setUpColumns(self):
  ...         return [
  ...             column.addColumn(self, TitleColumn, u'title',
  ...                              cellRenderer=cellRenderer,
  ...                              headCellRenderer=headCellRenderer,
  ...                              weight=1),
  ...             column.addColumn(self, NumberColumn, name=u'number',
  ...                              weight=2, header=u'Number')
  ...             ]

Now we can create our table:

  >>> batchingTable = BatchingTable(folder, request)

We also need to give the table a location and a name like we normaly setup
in traversing:

  >>> batchingTable.__parent__ = folder
  >>> batchingTable.__name__ = u'batchingTable.html'

And add some more items to our folder:

  >>> folder[u'sixth'] = File('Sixth', 6)
  >>> folder[u'seventh'] = File('Seventh', 7)
  >>> folder[u'eighth'] = File('Eighth', 8)
  >>> folder[u'ninth'] = File('Ninth', 9)
  >>> folder[u'tenth'] = File('Tenth', 10)
  >>> folder[u'eleventh'] = File('Eleventh', 11)
  >>> folder[u'twelfth '] = File('Twelfth', 12)
  >>> folder[u'thirteenth'] = File('Thirteenth', 13)
  >>> folder[u'fourteenth'] = File('Fourteenth', 14)
  >>> folder[u'fifteenth '] = File('Fifteenth', 15)
  >>> folder[u'sixteenth'] = File('Sixteenth', 16)
  >>> folder[u'seventeenth'] = File('Seventeenth', 17)
  >>> folder[u'eighteenth'] = File('Eighteenth', 18)
  >>> folder[u'nineteenth'] = File('Nineteenth', 19)
  >>> folder[u'twentieth'] = File('Twentieth', 20)

Now let's show the full table without batching:

  >>> batchingTable.update()
  >>> print batchingTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Eighteenth item</td>
        <td>number: 18</td>
      </tr>
      <tr>
        <td>Eighth item</td>
        <td>number: 8</td>
      </tr>
      <tr>
        <td>Eleventh item</td>
        <td>number: 11</td>
      </tr>
      <tr>
        <td>Fifteenth item</td>
        <td>number: 15</td>
      </tr>
      <tr>
        <td>First item</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Fourteenth item</td>
        <td>number: 14</td>
      </tr>
      <tr>
        <td>Fourth item</td>
        <td>number: 4</td>
      </tr>
      <tr>
        <td>Nineteenth item</td>
        <td>number: 19</td>
      </tr>
      <tr>
        <td>Ninth item</td>
        <td>number: 9</td>
      </tr>
      <tr>
        <td>Second item</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Seventeenth item</td>
        <td>number: 17</td>
      </tr>
      <tr>
        <td>Seventh item</td>
        <td>number: 7</td>
      </tr>
      <tr>
        <td>Sixteenth item</td>
        <td>number: 16</td>
      </tr>
      <tr>
        <td>Sixth item</td>
        <td>number: 6</td>
      </tr>
      <tr>
        <td>Tenth item</td>
        <td>number: 10</td>
      </tr>
      <tr>
        <td>Third item</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Thirteenth item</td>
        <td>number: 13</td>
      </tr>
      <tr>
        <td>Twelfth item</td>
        <td>number: 12</td>
      </tr>
      <tr>
        <td>Twentieth item</td>
        <td>number: 20</td>
      </tr>
      <tr>
        <td>Zero item</td>
        <td>number: 0</td>
      </tr>
    </tbody>
  </table>

As you can see, the table is not nice ordered and it uses all items. If we like
to use tha batch, we need to set the startBatchingAt size to a lower value then
it is set by default. The default value which a batch is used is set to ``50```:

  >>> batchingTable.startBatchingAt
  50

We will set the batch start to ``5`` for now. This means the first 5 items
do not get used:

  >>> batchingTable.startBatchingAt = 5
  >>> batchingTable.startBatchingAt
  5

There is also a ``batchSize`` value which we need to set to ``5``. By deault
the value get initialized by the ``batchSize`` value:

  >>> batchingTable.batchSize
  50

  >>> batchingTable.batchSize = 5
  >>> batchingTable.batchSize
  5

Now we can update and render the table again. But you will see that we only get
a table size of 5 rows which is correct. But the order doesn't depend on the
numbers we see in cells:

  >>> batchingTable.update()
  >>> print batchingTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Eighteenth item</td>
        <td>number: 18</td>
      </tr>
      <tr>
        <td>Eighth item</td>
        <td>number: 8</td>
      </tr>
      <tr>
        <td>Eleventh item</td>
        <td>number: 11</td>
      </tr>
      <tr>
        <td>Fifteenth item</td>
        <td>number: 15</td>
      </tr>
      <tr>
        <td>First item</td>
        <td>number: 1</td>
      </tr>
    </tbody>
  </table>

I think we should order the table by the second column before we show the next
batch values. We do this by simply set the ``defaultSortOn``:

  >>> batchingTable.sortOn = u'table-number-1'

Now we shuld see a nice ordered and batched table:

  >>> batchingTable.update()
  >>> print batchingTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Zero item</td>
        <td>number: 0</td>
      </tr>
      <tr>
        <td>First item</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Second item</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Third item</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Fourth item</td>
        <td>number: 4</td>
      </tr>
    </tbody>
  </table>

The batch concept allows us to choose from all batches and render the rows
for this batched items. We can do this by set any batch as rows. as you can see
we have ``4`` batched row data available:

  >>> len(batchingTable.rows.batches)
  4

We can set such a batch as row values, then this batch data are used for
rendering. But take care, if we update the table, our rows get overriden
and reset to the previous values. this means you can set any bath as rows
data and only render them. This is possbile since the update method sorted all
items and all batch contain ready to use data. This concept could be important
if you need to cache batches etc.

  >>> batchingTable.rows = batchingTable.rows.batches[1]
  >>> print batchingTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Sixth item</td>
        <td>number: 6</td>
      </tr>
      <tr>
        <td>Seventh item</td>
        <td>number: 7</td>
      </tr>
      <tr>
        <td>Eighth item</td>
        <td>number: 8</td>
      </tr>
      <tr>
        <td>Ninth item</td>
        <td>number: 9</td>
      </tr>
      <tr>
        <td>Tenth item</td>
        <td>number: 10</td>
      </tr>
    </tbody>
  </table>

And like described above, if you call ``update`` our batch to rows setup get
reset:

  >>> batchingTable.update()
  >>> print batchingTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Zero item</td>
        <td>number: 0</td>
      </tr>
      <tr>
        <td>First item</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Second item</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Third item</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Fourth item</td>
        <td>number: 4</td>
      </tr>
    </tbody>
  </table>

This means you can probably update all batches, cache them and use them alter.
but this is not usfull for normal usage in a page without an enhanced concept
which is not a part of this implementation. This also means, there must be
another way to set the batch index. Yes there is, there are two other ways how
we can set the batch position. We can set a batch position by set the
``batchStart`` value in our table or we can use a request variable. Let's show
the first one first:

  >>> batchingTable.batchStart = 6
  >>> batchingTable.update()
  >>> print batchingTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Seventh item</td>
        <td>number: 7</td>
      </tr>
      <tr>
        <td>Eighth item</td>
        <td>number: 8</td>
      </tr>
      <tr>
        <td>Ninth item</td>
        <td>number: 9</td>
      </tr>
      <tr>
        <td>Tenth item</td>
        <td>number: 10</td>
      </tr>
      <tr>
        <td>Eleventh item</td>
        <td>number: 11</td>
      </tr>
    </tbody>
  </table>

We can also set the batch position by using the batchStart value in a request.
Note that we need the table ``prefix`` and column ``__name__`` like we use in
the sorting concept:

  >>> batchingRequest = TestRequest(form={'table-batchStart': '11',
  ...                                     'table-batchSize': '5',
  ...                                     'table-sortOn': 'table-number-1'})
  >>> requestBatchingTable = BatchingTable(folder, batchingRequest)

We also need to give the table a location and a name like we normaly setup
in traversing:

  >>> requestBatchingTable.__parent__ = folder
  >>> requestBatchingTable.__name__ = u'requestBatchingTable.html'

Note; our table needs to start batching at smaller amount of items then we
have by default otherwise we don't get a batch:

  >>> requestBatchingTable.startBatchingAt = 5
  >>> requestBatchingTable.update()
  >>> print requestBatchingTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Twelfth item</td>
        <td>number: 12</td>
      </tr>
      <tr>
        <td>Thirteenth item</td>
        <td>number: 13</td>
      </tr>
      <tr>
        <td>Fourteenth item</td>
        <td>number: 14</td>
      </tr>
      <tr>
        <td>Fifteenth item</td>
        <td>number: 15</td>
      </tr>
      <tr>
        <td>Sixteenth item</td>
        <td>number: 16</td>
      </tr>
    </tbody>
  </table>


BatchProvider
-------------

The batch provider allows us to render the batch HTML independent of our
table. This means by default the batch get not rendered in the render method.
You can change this in your custom table implementation and return the batch
and the table in the render method.

As we can see, our table rows provides IBatch if it come to batching:

  >>> from z3c.batching.interfaces import IBatch
  >>> IBatch.providedBy(requestBatchingTable.rows)
  True

Let's check some batch variables before we render our test. htis let us compare
the rendered result. For more information about batching see the README.txt in
z3c.batching:

  >>> requestBatchingTable.rows.start
  11

  >>> requestBatchingTable.rows.index
  2

  >>> requestBatchingTable.rows.batches
  <z3c.batching.batch.Batches object at ...>

  >>> len(requestBatchingTable.rows.batches)
  4

We use our previous batching table and render the batch with the built in
``renderBatch`` method:

  >>> requestBatchingTable.update()
  >>> print requestBatchingTable.renderBatch()
  <a href="...html?table-batchStart=0&table-batchSize=5" class="first">1</a>
  <a href="...html?table-batchStart=5&table-batchSize=5">2</a>
  <a href="...html?table-batchStart=11&table-batchSize=5" class="current">3</a>
  <a href="...html?table-batchStart=15&table-batchSize=5" class="last">4</a>

Now let's add more items that we can test the skipped links in large batches:

  >>> for i in range(1000):
  ...     idx = i+20
  ...     folder[str(idx)] = File(str(idx), idx)

Now let's test the batching table again with the new amount of items and
the same ``startBatchingAt`` of 5 but starting the batch at item ``100``
and sorted on the second numbered column:

  >>> batchingRequest = TestRequest(form={'table-batchStart': '100',
  ...                                     'table-batchSize': '5',
  ...                                     'table-sortOn': 'table-number-1'})
  >>> requestBatchingTable = BatchingTable(folder, batchingRequest)
  >>> requestBatchingTable.startBatchingAt = 5

We also need to give the table a location and a name like we normaly setup
in traversing:

  >>> requestBatchingTable.__parent__ = folder
  >>> requestBatchingTable.__name__ = u'requestBatchingTable.html'

  >>> requestBatchingTable.update()
  >>> print requestBatchingTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>100 item</td>
        <td>number: 100</td>
      </tr>
      <tr>
        <td>101 item</td>
        <td>number: 101</td>
      </tr>
      <tr>
        <td>102 item</td>
        <td>number: 102</td>
      </tr>
      <tr>
        <td>103 item</td>
        <td>number: 103</td>
      </tr>
      <tr>
        <td>104 item</td>
        <td>number: 104</td>
      </tr>
    </tbody>
  </table>

And test the batch. Note the three dots between the links get rendered by the
batch provider and is not a part of the doctest:

  >>> print requestBatchingTable.renderBatch()
  <a href="...html?table-batchStart=0&table-batchSize=5" class="first">1</a>
  ...
  <a href="...html?table-batchStart=85&table-batchSize=5">18</a>
  <a href="...html?table-batchStart=90&table-batchSize=5">19</a>
  <a href="...html?table-batchStart=95&table-batchSize=5">20</a>
  <a href="...html?table-batchStart=100&table-batchSize=5" class="current">21</a>
  <a href="...html?table-batchStart=105&table-batchSize=5">22</a>
  <a href="...html?table-batchStart=110&table-batchSize=5">23</a>
  <a href="...html?table-batchStart=115&table-batchSize=5">24</a>
  ...
  <a href="...html?table-batchStart=1015&table-batchSize=5" class="last">204</a>

You can change the spacer in the batch provider if you set the ``batchSpacer``
value:

  >>> from z3c.table.batch import BatchProvider
  >>> class XBatchProvider(BatchProvider):
  ...     """Just another batch provider."""
  ...     batchSpacer = u'xxx'

Now register the new batch provider for our batching table:

  >>> import zope.publisher.interfaces.browser
  >>> zope.component.provideAdapter(XBatchProvider,
  ...     (zope.interface.Interface,
  ...      zope.publisher.interfaces.browser.IBrowserRequest,
  ...      BatchingTable), name='batch')

If we update and render our table, the new batch provider should get used.
As you can see the spacer get changed now:

  >>> requestBatchingTable.update()
  >>> print requestBatchingTable.renderBatch()
  <a href="...html?table-batchStart=0&table-batchSize=5" class="first">1</a>
  xxx
  <a href="...html?table-batchStart=85&table-batchSize=5">18</a>
  <a href="...html?table-batchStart=90&table-batchSize=5">19</a>
  <a href="...html?table-batchStart=95&table-batchSize=5">20</a>
  <a href="...html?table-batchStart=100&table-batchSize=5" class="current">21</a>
  <a href="...html?table-batchStart=105&table-batchSize=5">22</a>
  <a href="...html?table-batchStart=110&table-batchSize=5">23</a>
  <a href="...html?table-batchStart=115&table-batchSize=5">24</a>
  xxx
  <a href="...html?table-batchStart=1015&table-batchSize=5" class="last">204</a>

None previous and next batch size. Probably it doesn't make sense but let's
show what happens if we set the previous and next batch size to 0 (zero):

  >>> from z3c.table.batch import BatchProvider
  >>> class ZeroBatchProvider(BatchProvider):
  ...     """Just another batch provider."""
  ...     batchSpacer = u'xxx'
  ...     previousBatchSize = 0
  ...     nextBatchSize = 0

Now register the new batch provider for our batching table:

  >>> import zope.publisher.interfaces.browser
  >>> zope.component.provideAdapter(ZeroBatchProvider,
  ...     (zope.interface.Interface,
  ...      zope.publisher.interfaces.browser.IBrowserRequest,
  ...      BatchingTable), name='batch')

Update the table and render the batch:

  >>> requestBatchingTable.update()
  >>> print requestBatchingTable.renderBatch()
  <a href="...html?table-batchStart=0&table-batchSize=5" class="first">1</a>
  xxx
  <a href="...html?table-batchStart=100&table-batchSize=5" class="current">21</a>
  xxx
  <a href="...html?table-batchStart=1015&table-batchSize=5" class="last">204</a>


SequenceTable
-------------

A sequence table can be used if we need to provide a table for a sequence
of items instead of a mapping. Define the same sequence of items we used before
we added the other 1000 items:

  >>> dataSequence = []
  >>> dataSequence.append(File('Zero', 0))
  >>> dataSequence.append(File('First', 1))
  >>> dataSequence.append(File('Second', 2))
  >>> dataSequence.append(File('Third', 3))
  >>> dataSequence.append(File('Fourth', 4))
  >>> dataSequence.append(File('Fifth', 5))
  >>> dataSequence.append(File('Sixth', 6))
  >>> dataSequence.append(File('Seventh', 7))
  >>> dataSequence.append(File('Eighth', 8))
  >>> dataSequence.append(File('Ninth', 9))
  >>> dataSequence.append(File('Tenth', 10))
  >>> dataSequence.append(File('Eleventh', 11))
  >>> dataSequence.append(File('Twelfth', 12))
  >>> dataSequence.append(File('Thirteenth', 13))
  >>> dataSequence.append(File('Fourteenth', 14))
  >>> dataSequence.append(File('Fifteenth', 15))
  >>> dataSequence.append(File('Sixteenth', 16))
  >>> dataSequence.append(File('Seventeenth', 17))
  >>> dataSequence.append(File('Eighteenth', 18))
  >>> dataSequence.append(File('Nineteenth', 19))
  >>> dataSequence.append(File('Twentieth', 20))

Now let's define a new SequenceTable:

  >>> class SequenceTable(table.SequenceTable):
  ...
  ...     def setUpColumns(self):
  ...         return [
  ...             column.addColumn(self, TitleColumn, u'title',
  ...                              cellRenderer=cellRenderer,
  ...                              headCellRenderer=headCellRenderer,
  ...                              weight=1),
  ...             column.addColumn(self, NumberColumn, name=u'number',
  ...                              weight=2, header=u'Number')
  ...             ]

Now we can create our table adapting our sequence:

  >>> sequenceRequest = TestRequest(form={'table-batchStart': '0',
  ...                                     'table-sortOn': 'table-number-1'})
  >>> sequenceTable = SequenceTable(dataSequence, sequenceRequest)

We also need to give the table a location and a name like we normaly setup
in traversing:

  >>> sequenceTable.__parent__ = folder
  >>> sequenceTable.__name__ = u'sequenceTable.html'

And update and render the sequence table:

  >>> sequenceTable.update()
  >>> print sequenceTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Zero item</td>
        <td>number: 0</td>
      </tr>
      <tr>
        <td>First item</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Second item</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Third item</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Fourth item</td>
        <td>number: 4</td>
      </tr>
      <tr>
        <td>Fifth item</td>
        <td>number: 5</td>
      </tr>
      <tr>
        <td>Sixth item</td>
        <td>number: 6</td>
      </tr>
      <tr>
        <td>Seventh item</td>
        <td>number: 7</td>
      </tr>
      <tr>
        <td>Eighth item</td>
        <td>number: 8</td>
      </tr>
      <tr>
        <td>Ninth item</td>
        <td>number: 9</td>
      </tr>
      <tr>
        <td>Tenth item</td>
        <td>number: 10</td>
      </tr>
      <tr>
        <td>Eleventh item</td>
        <td>number: 11</td>
      </tr>
      <tr>
        <td>Twelfth item</td>
        <td>number: 12</td>
      </tr>
      <tr>
        <td>Thirteenth item</td>
        <td>number: 13</td>
      </tr>
      <tr>
        <td>Fourteenth item</td>
        <td>number: 14</td>
      </tr>
      <tr>
        <td>Fifteenth item</td>
        <td>number: 15</td>
      </tr>
      <tr>
        <td>Sixteenth item</td>
        <td>number: 16</td>
      </tr>
      <tr>
        <td>Seventeenth item</td>
        <td>number: 17</td>
      </tr>
      <tr>
        <td>Eighteenth item</td>
        <td>number: 18</td>
      </tr>
      <tr>
        <td>Nineteenth item</td>
        <td>number: 19</td>
      </tr>
      <tr>
        <td>Twentieth item</td>
        <td>number: 20</td>
      </tr>
    </tbody>
  </table>

As you can see, the items get rendered based on a data sequence. Now we set
the ``start batch at`` size to ``5``:

  >>> sequenceTable.startBatchingAt = 5

And the ``batchSize`` to ``5``.

  >>> sequenceTable.batchSize = 5

Now we can update and render the table again. But you will see that we only get
a table size of 5 rows:

  >>> sequenceTable.update()
  >>> print sequenceTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Zero item</td>
        <td>number: 0</td>
      </tr>
      <tr>
        <td>First item</td>
        <td>number: 1</td>
      </tr>
      <tr>
        <td>Second item</td>
        <td>number: 2</td>
      </tr>
      <tr>
        <td>Third item</td>
        <td>number: 3</td>
      </tr>
      <tr>
        <td>Fourth item</td>
        <td>number: 4</td>
      </tr>
    </tbody>
  </table>

And we set the sort order to ``reverse`` even if we use batching:

  >>> sequenceTable.sortOrder = u'reverse'
  >>> sequenceTable.update()
  >>> print sequenceTable.render()
  <table>
    <thead>
      <tr>
        <th>My items</th>
        <th>Number</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Twentieth item</td>
        <td>number: 20</td>
      </tr>
      <tr>
        <td>Nineteenth item</td>
        <td>number: 19</td>
      </tr>
      <tr>
        <td>Eighteenth item</td>
        <td>number: 18</td>
      </tr>
      <tr>
        <td>Seventeenth item</td>
        <td>number: 17</td>
      </tr>
      <tr>
        <td>Sixteenth item</td>
        <td>number: 16</td>
      </tr>
    </tbody>
  </table>

Headers
-------

We can change the rendering of the header of, e.g, the Title column by
registering a IHeaderColumn adapter. This may be useful for adding links to
column headers for an existing table implementation.

We'll use a fresh almost empty folder.

  >>> folder = Folder()
  >>> root['folder-1'] = folder
  >>> folder[u'first'] = File('First', 1)
  >>> folder[u'second'] = File('Second', 2)
  >>> folder[u'third'] = File('Third', 3)

  >>> class myTableClass(table.Table):
  ...     pass

  >>> myTable = myTableClass(folder, request)

  >>> class TitleColumn(column.Column):
  ...
  ...     header = u'Title'
  ...
  ...     def renderCell(self, item):
  ...         return item.title

Now we can register a column adapter directly to our table class.

  >>> zope.component.provideAdapter(TitleColumn,
  ...     (None, None, myTableClass), provides=interfaces.IColumn,
  ...      name='titleColumn')

And add a registration for a column header - we'll use here the proveded generic
sorting header implementation.

  >>> from z3c.table.header import SortingColumnHeader
  >>> zope.component.provideAdapter(SortingColumnHeader,
  ...     (None, None, interfaces.ITable, interfaces.IColumn),
  ...     provides=interfaces.IColumnHeader)

Now we can render the table and we shall see a link in the header. Note that it
is set to switch to descending as the the table initially will display the first
column as ascending.

  >>> myTable.update()
  >>> print myTable.render()
  <table>
   <thead>
    <tr>
     <th><a
      href="?table-sortOrder=descending&table-sortOn=table-titleColumn-0"
      title="Sort">Title</a></th>
  ...
  </table>

Miscellaneous
-------------

Make coverage report happy and test different things.

Test if the getWeight method returns 0 (zero) on AttributeError:

  >>> from z3c.table.table import getWeight
  >>> getWeight(None)
  0

Try to call a simple table and call renderBatch which should return an empty
string:

  >>> simpleTable = table.Table(folder, request)
  >>> simpleTable.renderBatch()
  u''

Try to render an empty table adapting an empty mapping:

  >>> simpleTable = table.Table({}, request)
  >>> simpleTable.render()
  u''

Let's see if the addColumn raises a ValueError if ther is no Column class:

  >>> column.addColumn(simpleTable, column.Column, u'dummy')
  <Column u'dummy'>

  >>> column.addColumn(simpleTable, None, u'dummy')
  Traceback (most recent call last):
  ...
  ValueError: class_ None must implement IColumn.

Test if we can set additional kws in addColumn


  >>> simpleColumn = column.addColumn(simpleTable, column.Column, u'dummy',
  ...     foo='foo value', bar=u'something else', counter=99)
  >>> simpleColumn.foo
  'foo value'

  >>> simpleColumn.bar
  u'something else'

  >>> simpleColumn.counter
  99

The NoneCell class provides some methods which never get. But this methods must
be there because the interfaces defines them. Let's test the default values
and make coverage report happy.

Let's get an folder item first:

  >>> firstItem = folder[u'first']
  >>> noneCellColumn = column.addColumn(simpleTable, column.NoneCell, u'none')
  >>> noneCellColumn.renderCell(firstItem)
  u''

  >>> noneCellColumn.getColspan(firstItem)
  0

  >>> noneCellColumn.renderHeadCell()
  u''

  >>> noneCellColumn.renderCell(firstItem)
  u''

The default ``Column`` implementation raises an NotImplementedError if we
do not override the renderCell method:

  >>> defaultColumn = column.addColumn(simpleTable, column.Column, u'default')
  >>> defaultColumn.renderCell(firstItem)
  Traceback (most recent call last):
  ...
  NotImplementedError: Subclass must implement renderCell
