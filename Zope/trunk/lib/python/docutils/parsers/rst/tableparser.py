# Author: David Goodger
# Contact: goodger@users.sourceforge.net
# Revision: $Revision: 1.2 $
# Date: $Date: 2003/02/01 09:26:07 $
# Copyright: This module has been placed in the public domain.

"""
This module defines table parser classes,which parse plaintext-graphic tables
and produce a well-formed data structure suitable for building a CALS table.

:Classes:
    - `GridTableParser`: Parse fully-formed tables represented with a grid.
    - `SimpleTableParser`: Parse simple tables, delimited by top & bottom
      borders.

:Exception class: `TableMarkupError`

:Function:
    `update_dict_of_lists()`: Merge two dictionaries containing list values.
"""

__docformat__ = 'reStructuredText'


import re
import sys
from docutils import DataError


class TableMarkupError(DataError): pass


class TableParser:

    """
    Abstract superclass for the common parts of the syntax-specific parsers.
    """

    head_body_separator_pat = None
    """Matches the row separator between head rows and body rows."""

    def parse(self, block):
        """
        Analyze the text `block` and return a table data structure.

        Given a plaintext-graphic table in `block` (list of lines of text; no
        whitespace padding), parse the table, construct and return the data
        necessary to construct a CALS table or equivalent.

        Raise `TableMarkupError` if there is any problem with the markup.
        """
        self.setup(block)
        self.find_head_body_sep()
        self.parse_table()
        structure = self.structure_from_cells()
        return structure

    def find_head_body_sep(self):
        """Look for a head/body row separator line; store the line index."""
        for i in range(len(self.block)):
            line = self.block[i]
            if self.head_body_separator_pat.match(line):
                if self.head_body_sep:
                    raise TableMarkupError(
                        'Multiple head/body row separators in table (at line '
                        'offset %s and %s); only one allowed.'
                        % (self.head_body_sep, i))
                else:
                    self.head_body_sep = i
                    self.block[i] = line.replace('=', '-')
        if self.head_body_sep == 0 or self.head_body_sep == (len(self.block)
                                                             - 1):
            raise TableMarkupError('The head/body row separator may not be '
                                   'the first or last line of the table.')


class GridTableParser(TableParser):

    """
    Parse a grid table using `parse()`.

    Here's an example of a grid table::

        +------------------------+------------+----------+----------+
        | Header row, column 1   | Header 2   | Header 3 | Header 4 |
        +========================+============+==========+==========+
        | body row 1, column 1   | column 2   | column 3 | column 4 |
        +------------------------+------------+----------+----------+
        | body row 2             | Cells may span columns.          |
        +------------------------+------------+---------------------+
        | body row 3             | Cells may  | - Table cells       |
        +------------------------+ span rows. | - contain           |
        | body row 4             |            | - body elements.    |
        +------------------------+------------+---------------------+

    Intersections use '+', row separators use '-' (except for one optional
    head/body row separator, which uses '='), and column separators use '|'.

    Passing the above table to the `parse()` method will result in the
    following data structure::

        ([24, 12, 10, 10],
         [[(0, 0, 1, ['Header row, column 1']),
           (0, 0, 1, ['Header 2']),
           (0, 0, 1, ['Header 3']),
           (0, 0, 1, ['Header 4'])]],
         [[(0, 0, 3, ['body row 1, column 1']),
           (0, 0, 3, ['column 2']),
           (0, 0, 3, ['column 3']),
           (0, 0, 3, ['column 4'])],
          [(0, 0, 5, ['body row 2']),
           (0, 2, 5, ['Cells may span columns.']),
           None,
           None],
          [(0, 0, 7, ['body row 3']),
           (1, 0, 7, ['Cells may', 'span rows.', '']),
           (1, 1, 7, ['- Table cells', '- contain', '- body elements.']),
           None],
          [(0, 0, 9, ['body row 4']), None, None, None]])

    The first item is a list containing column widths (colspecs). The second
    item is a list of head rows, and the third is a list of body rows. Each
    row contains a list of cells. Each cell is either None (for a cell unused
    because of another cell's span), or a tuple. A cell tuple contains four
    items: the number of extra rows used by the cell in a vertical span
    (morerows); the number of extra columns used by the cell in a horizontal
    span (morecols); the line offset of the first line of the cell contents;
    and the cell contents, a list of lines of text.
    """

    head_body_separator_pat = re.compile(r'\+=[=+]+=\+ *$')

    def setup(self, block):
        self.block = list(block)        # make a copy; it may be modified
        self.bottom = len(block) - 1
        self.right = len(block[0]) - 1
        self.head_body_sep = None
        self.done = [-1] * len(block[0])
        self.cells = []
        self.rowseps = {0: [0]}
        self.colseps = {0: [0]}

    def parse_table(self):
        """
        Start with a queue of upper-left corners, containing the upper-left
        corner of the table itself. Trace out one rectangular cell, remember
        it, and add its upper-right and lower-left corners to the queue of
        potential upper-left corners of further cells. Process the queue in
        top-to-bottom order, keeping track of how much of each text column has
        been seen.

        We'll end up knowing all the row and column boundaries, cell positions
        and their dimensions.
        """
        corners = [(0, 0)]
        while corners:
            top, left = corners.pop(0)
            if top == self.bottom or left == self.right \
                  or top <= self.done[left]:
                continue
            result = self.scan_cell(top, left)
            if not result:
                continue
            bottom, right, rowseps, colseps = result
            update_dict_of_lists(self.rowseps, rowseps)
            update_dict_of_lists(self.colseps, colseps)
            self.mark_done(top, left, bottom, right)
            cellblock = self.get_cell_block(top, left, bottom, right)
            self.cells.append((top, left, bottom, right, cellblock))
            corners.extend([(top, right), (bottom, left)])
            corners.sort()
        if not self.check_parse_complete():
            raise TableMarkupError('Malformed table; parse incomplete.')

    def mark_done(self, top, left, bottom, right):
        """For keeping track of how much of each text column has been seen."""
        before = top - 1
        after = bottom - 1
        for col in range(left, right):
            assert self.done[col] == before
            self.done[col] = after

    def check_parse_complete(self):
        """Each text column should have been completely seen."""
        last = self.bottom - 1
        for col in range(self.right):
            if self.done[col] != last:
                return None
        return 1

    def get_cell_block(self, top, left, bottom, right):
        """Given the corners, extract the text of a cell."""
        cellblock = []
        margin = right
        for lineno in range(top + 1, bottom):
            line = self.block[lineno][left + 1 : right].rstrip()
            cellblock.append(line)
            if line:
                margin = min(margin, len(line) - len(line.lstrip()))
        if 0 < margin < right:
            cellblock = [line[margin:] for line in cellblock]
        return cellblock

    def scan_cell(self, top, left):
        """Starting at the top-left corner, start tracing out a cell."""
        assert self.block[top][left] == '+'
        result = self.scan_right(top, left)
        return result

    def scan_right(self, top, left):
        """
        Look for the top-right corner of the cell, and make note of all column
        boundaries ('+').
        """
        colseps = {}
        line = self.block[top]
        for i in range(left + 1, self.right + 1):
            if line[i] == '+':
                colseps[i] = [top]
                result = self.scan_down(top, left, i)
                if result:
                    bottom, rowseps, newcolseps = result
                    update_dict_of_lists(colseps, newcolseps)
                    return bottom, i, rowseps, colseps
            elif line[i] != '-':
                return None
        return None

    def scan_down(self, top, left, right):
        """
        Look for the bottom-right corner of the cell, making note of all row
        boundaries.
        """
        rowseps = {}
        for i in range(top + 1, self.bottom + 1):
            if self.block[i][right] == '+':
                rowseps[i] = [right]
                result = self.scan_left(top, left, i, right)
                if result:
                    newrowseps, colseps = result
                    update_dict_of_lists(rowseps, newrowseps)
                    return i, rowseps, colseps
            elif self.block[i][right] != '|':
                return None
        return None

    def scan_left(self, top, left, bottom, right):
        """
        Noting column boundaries, look for the bottom-left corner of the cell.
        It must line up with the starting point.
        """
        colseps = {}
        line = self.block[bottom]
        for i in range(right - 1, left, -1):
            if line[i] == '+':
                colseps[i] = [bottom]
            elif line[i] != '-':
                return None
        if line[left] != '+':
            return None
        result = self.scan_up(top, left, bottom, right)
        if result is not None:
            rowseps = result
            return rowseps, colseps
        return None

    def scan_up(self, top, left, bottom, right):
        """
        Noting row boundaries, see if we can return to the starting point.
        """
        rowseps = {}
        for i in range(bottom - 1, top, -1):
            if self.block[i][left] == '+':
                rowseps[i] = [left]
            elif self.block[i][left] != '|':
                return None
        return rowseps

    def structure_from_cells(self):
        """
        From the data colledted by `scan_cell()`, convert to the final data
        structure.
        """
        rowseps = self.rowseps.keys()   # list of row boundaries
        rowseps.sort()
        rowindex = {}
        for i in range(len(rowseps)):
            rowindex[rowseps[i]] = i    # row boundary -> row number mapping
        colseps = self.colseps.keys()   # list of column boundaries
        colseps.sort()
        colindex = {}
        for i in range(len(colseps)):
            colindex[colseps[i]] = i    # column boundary -> col number map
        colspecs = [(colseps[i] - colseps[i - 1] - 1)
                    for i in range(1, len(colseps))] # list of column widths
        # prepare an empty table with the correct number of rows & columns
        onerow = [None for i in range(len(colseps) - 1)]
        rows = [onerow[:] for i in range(len(rowseps) - 1)]
        # keep track of # of cells remaining; should reduce to zero
        remaining = (len(rowseps) - 1) * (len(colseps) - 1)
        for top, left, bottom, right, block in self.cells:
            rownum = rowindex[top]
            colnum = colindex[left]
            assert rows[rownum][colnum] is None, (
                  'Cell (row %s, column %s) already used.'
                  % (rownum + 1, colnum + 1))
            morerows = rowindex[bottom] - rownum - 1
            morecols = colindex[right] - colnum - 1
            remaining -= (morerows + 1) * (morecols + 1)
            # write the cell into the table
            rows[rownum][colnum] = (morerows, morecols, top + 1, block)
        assert remaining == 0, 'Unused cells remaining.'
        if self.head_body_sep:          # separate head rows from body rows
            numheadrows = rowindex[self.head_body_sep]
            headrows = rows[:numheadrows]
            bodyrows = rows[numheadrows:]
        else:
            headrows = []
            bodyrows = rows
        return (colspecs, headrows, bodyrows)


class SimpleTableParser(TableParser):

    """
    Parse a simple table using `parse()`.

    Here's an example of a simple table::

        =====  =====
        col 1  col 2
        =====  =====
        1      Second column of row 1.
        2      Second column of row 2.
               Second line of paragraph.
        3      - Second column of row 3.

               - Second item in bullet
                 list (row 3, column 2).
        4 is a span
        ------------
        5
        =====  =====

    Top and bottom borders use '=', column span underlines use '-', column
    separation is indicated with spaces.

    Passing the above table to the `parse()` method will result in the
    following data structure, whose interpretation is the same as for
    `GridTableParser`::

        ([5, 25],
         [[(0, 0, 1, ['col 1']),
           (0, 0, 1, ['col 2'])]],
         [[(0, 0, 3, ['1']),
           (0, 0, 3, ['Second column of row 1.'])],
          [(0, 0, 4, ['2']),
           (0, 0, 4, ['Second column of row 2.',
                      'Second line of paragraph.'])],
          [(0, 0, 6, ['3']),
           (0, 0, 6, ['- Second column of row 3.',
                      '',
                      '- Second item in bullet',
                      '  list (row 3, column 2).'])],
          [(0, 1, 10, ['4 is a span'])],
          [(0, 0, 12, ['5']),
           (0, 0, 12, [''])]])
    """

    head_body_separator_pat = re.compile('=[ =]*$')
    span_pat = re.compile('-[ -]*$')

    def setup(self, block):
        self.block = list(block)        # make a copy; it will be modified
        # Convert top & bottom borders to column span underlines:
        self.block[0] = self.block[0].replace('=', '-')
        self.block[-1] = self.block[-1].replace('=', '-')
        self.head_body_sep = None
        self.columns = []
        self.border_end = None
        self.table = []
        self.done = [-1] * len(block[0])
        self.rowseps = {0: [0]}
        self.colseps = {0: [0]}

    def parse_table(self):
        """
        First determine the column boundaries from the top border, then
        process rows.  Each row may consist of multiple lines; accumulate
        lines until a row is complete.  Call `self.parse_row` to finish the
        job.
        """
        # Top border must fully describe all table columns.
        self.columns = self.parse_columns(self.block[0], 0)
        self.border_end = self.columns[-1][1]
        firststart, firstend = self.columns[0]
        block = self.block[1:]
        offset = 0
        # Container for accumulating text lines until a row is complete:
        rowlines = []
        while block:
            line = block.pop(0)
            offset += 1
            if self.span_pat.match(line):
                # Column span underline or border; row is complete.
                self.parse_row(rowlines, (line.rstrip(), offset))
                rowlines = []
            elif line[firststart:firstend].strip():
                # First column not blank, therefore it's a new row.
                if rowlines:
                    self.parse_row(rowlines)
                rowlines = [(line.rstrip(), offset)]
            else:
                # Accumulate lines of incomplete row.
                rowlines.append((line.rstrip(), offset))

    def parse_columns(self, line, offset):
        """
        Given a column span underline, return a list of (begin, end) pairs.
        """
        cols = []
        end = 0
        while 1:
            begin = line.find('-', end)
            end = line.find(' ', begin)
            if begin < 0:
                break
            if end < 0:
                end = len(line)
            cols.append((begin, end))
        if self.columns:
            if cols[-1][1] != self.border_end:
                raise TableMarkupError('Column span incomplete at line '
                                       'offset %s.' % offset)
            # Allow for an unbounded rightmost column:
            cols[-1] = (cols[-1][0], self.columns[-1][1])
        return cols

    def init_row(self, colspec, offset):
        i = 0
        cells = []
        for start, end in colspec:
            morecols = 0
            try:
                assert start == self.columns[i][0]
                while end != self.columns[i][1]:
                    i += 1
                    morecols += 1
            except (AssertionError, IndexError):
                raise TableMarkupError('Column span alignment problem at '
                                       'line offset %s.' % offset)
            cells.append((0, morecols, offset, []))
            i += 1
        return cells

    def parse_row(self, lines, spanline=None):
        """
        Given the text `lines` of a row, parse it and append to `self.table`.

        The row is parsed according to the current column spec (either
        `spanline` if provided or `self.columns`).  For each column, extract
        text from each line, and check for text in column margins.  Finally,
        adjust for insigificant whitespace.
        """
        while lines and not lines[-1][0]:
            lines.pop()                 # Remove blank trailing lines.
        if lines:
            offset = lines[0][1]
        elif spanline:
            offset = spanline[1]
        else:
            # No new row, just blank lines.
            return
        if spanline:
            columns = self.parse_columns(*spanline)
        else:
            columns = self.columns[:]
        row = self.init_row(columns, offset)
        # "Infinite" value for a dummy last column's beginning, used to
        # check for text overflow:
        columns.append((sys.maxint, None))
        lastcol = len(columns) - 2
        for i in range(len(columns) - 1):
            start, end = columns[i]
            nextstart = columns[i+1][0]
            block = []
            margin = sys.maxint
            for line, offset in lines:
                if i == lastcol and line[end:].strip():
                    text = line[start:].rstrip()
                    columns[lastcol] = (start, start + len(text))
                    self.adjust_last_column(start + len(text))
                elif line[end:nextstart].strip():
                    raise TableMarkupError('Text in column margin at line '
                                           'offset %s.' % offset)
                else:
                    text = line[start:end].rstrip()
                block.append(text)
                if text:
                    margin = min(margin, len(text) - len(text.lstrip()))
            if 0 < margin < sys.maxint:
                block = [line[margin:] for line in block]
            row[i][3].extend(block)
        self.table.append(row)

    def adjust_last_column(self, new_end):
        start, end = self.columns[-1]
        if new_end > end:
            self.columns[-1] = (start, new_end)

    def structure_from_cells(self):
        colspecs = [end - start for start, end in self.columns]
        first_body_row = 0
        if self.head_body_sep:
            for i in range(len(self.table)):
                if self.table[i][0][2] > self.head_body_sep:
                    first_body_row = i
                    break
        return (colspecs, self.table[:first_body_row],
                self.table[first_body_row:])


def update_dict_of_lists(master, newdata):
    """
    Extend the list values of `master` with those from `newdata`.

    Both parameters must be dictionaries containing list values.
    """
    for key, values in newdata.items():
        master.setdefault(key, []).extend(values)
