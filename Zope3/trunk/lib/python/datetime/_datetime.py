"""Concrete date/time and related types -- prototype implemented in Python.

See http://www.zope.org/Members/fdrake/DateTimeWiki/FrontPage

See also http://dir.yahoo.com/Reference/calendars/
"""

import time as _time
import math as _math

MINYEAR = 1     # XXX The design doc says 0
MAXYEAR = 9999  # XXX The design doc says 65535

# Utility functions, adapted from Python's Demo/classes/Dates.py, which
# also assumes the current Gregorian calendar indefinitely extended in
# both directions.  Difference:  Dates.py calls January 1 of year 0 day
# number 1.  The code here calls January 1 of year 1 day number 1.  This is
# to match the definition of the "proleptic Gregorian" calendar in Dershowitz
# and Reingold's "Calendrical Calculations", where it's the base calendar
# for all computations.  See the book for algorithms for converting between
# proleptic Gregorian ordinals and many other calendar systems.

_DAYS_IN_MONTH = [None, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

_DAYS_BEFORE_MONTH = [None]
dbm = 0
for dim in _DAYS_IN_MONTH[1:]:
    _DAYS_BEFORE_MONTH.append(dbm)
    dbm += dim
del dbm, dim

def _is_leap(year):
    "year -> 1 if leap year, else 0."
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def _days_in_year(year):
    "year -> number of days in year (366 if a leap year, else 365)."
    return 365 + _is_leap(year)

def _days_before_year(year):
    "year -> number of days before January 1st of year."
    y = year - 1
    return y*365 + y//4 - y//100 + y//400

def _days_in_month(year, month):
    "year, month -> number of days in that month in that year."
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]

def _days_before_month(year, month):
    "year, month -> number of days in year preceeding first day of month."
    if not 1 <= month <= 12:
        raise ValueError('month must be in 1..12', month)
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))

def _ymd2ord(year, month, day):
    "year, month, day -> ordinal, considering 01-Jan-0001 as day 1."
    if not 1 <= month <= 12:
        raise ValueError('month must be in 1..12', month)
    dim = _days_in_month(year, month)
    if not 1 <= day <= dim:
        raise ValueError('day must be in 1..%d' % dim, day)
    return (_days_before_year(year) +
            _days_before_month(year, month) +
            day)

_DI400Y = _days_before_year(401)    # number of days in 400 years
_DI100Y = _days_before_year(101)    #    "    "   "   " 100   "
_DI4Y   = _days_before_year(5)      #    "    "   "   "   4   "

# A 4-year cycle has an extra leap day over what we'd get from pasting
# together 4 single years.
assert _DI4Y == 4 * 365 + 1

# Similarly, a 400-year cycle has an extra leap day over what we'd get from
# pasting together 4 100-year cycles.
assert _DI400Y == 4 * _DI100Y + 1

# OTOH, a 100-year cycle has one fewer leap day than we'd get from
# pasting together 25 4-year cycles.
assert _DI100Y == 25 * _DI4Y - 1

def _ord2ymd(n):
    "ordinal -> (year, month, day), considering 01-Jan-0001 as day 1."

    # n is a 1-based index, starting at 1-Jan-1.  The pattern of leap years
    # repeats exactly every 400 years.  The basic strategy is to find the
    # closest 400-year boundary at or before n, then work with the offset
    # from that boundary to n.  Life is much clearer if we subtract 1 from
    # n first -- then the values of n at 400-year boundaries are exactly
    # those divisible by _DI400Y:
    #
    #     D  M   Y            n              n-1
    #     -- --- ----        ----------     ----------------
    #     31 Dec -400        -_DI400Y       -_DI400Y -1
    #      1 Jan -399         -_DI400Y +1   -_DI400Y      400-year boundary
    #     ...
    #     30 Dec  000        -1             -2
    #     31 Dec  000         0             -1
    #      1 Jan  001         1              0            400-year boundary
    #      2 Jan  001         2              1
    #      3 Jan  001         3              2
    #     ...
    #     31 Dec  400         _DI400Y        _DI400Y -1
    #      1 Jan  401         _DI400Y +1     _DI400Y      400-year boundary
    n -= 1
    n400, n = divmod(n, _DI400Y)
    year = n400 * 400 + 1   # ..., -399, 1, 401, ...

    # Now n is the (non-negative) offset, in days, from January 1 of year, to
    # the desired date.  Now compute how many 100-year cycles precede n.
    # Note that it's possible for n100 to equal 4!  In that case 4 full
    # 100-year cycles precede the desired day, which implies the desired
    # day is December 31 at the end of a 400-year cycle.
    n100, n = divmod(n, _DI100Y)

    # Now compute how many 4-year cycles precede it.
    n4, n = divmod(n, _DI4Y)

    # And now how many single years.  Again n1 can be 4, and again meaning
    # that the desired day is December 31 at the end of the 4-year cycle.
    n1, n = divmod(n, 365)

    year += n100 * 100 + n4 * 4 + n1
    if n1 == 4 or n100 == 4:
        assert n == 0
        return year-1, 12, 31

    # Now the year is correct, and n is the offset from January 1.  We find
    # the month via an estimate that's either exact or one too large.
    leapyear = n1 == 3 and (n4 != 24 or n100 == 3)
    assert leapyear == _is_leap(year)
    month = (n + 50) >> 5
    preceding = _DAYS_BEFORE_MONTH[month] + (month > 2 and leapyear)
    if preceding > n:  # estimate is too large
        month -= 1
        preceding -= _DAYS_IN_MONTH[month] + (month == 2 and leapyear)
    n -= preceding
    assert 0 <= n < _days_in_month(year, month)

    # Now the year and month are correct, and n is the offset from the
    # start of that month:  we're done!
    return year, month, n+1

# Month and day names.  For localized versions, see the calendar module.
_MONTHNAMES = [None, "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_DAYNAMES = [None, "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _build_struct_time(y, m, d, hh, mm, ss, dstflag):
    wday = (_ymd2ord(y, m, d) + 6) % 7
    dnum = _days_before_month(y, m) + d
    return _time.struct_time((y, m, d, hh, mm, ss, wday, dnum, dstflag))

def _format_time(hh, mm, ss, us):
    # Skip trailing microseconds when us==0.
    result = "%02d:%02d:%02d" % (hh, mm, ss)
    if us:
        result += ".%06d" % us
    return result

# Correctly substitute for %z and %Z escapes in strftime formats.
def _wrap_strftime(object, format, timetuple):
    # Don't call utcoffset() or tzname() unless actually needed.
    zreplace = None # the string to use for %z
    Zreplace = None # the string to use for %Z

    # Scan format for %z and %Z escapes, replacing as needed.
    newformat = []
    push = newformat.append
    i, n = 0, len(format)
    while i < n:
        ch = format[i]
        i += 1
        if ch == '%':
            if i < n:
                ch = format[i]
                i += 1
                if ch == 'z':
                    if zreplace is None:
                        zreplace = ""
                        if hasattr(object, "utcoffset"):
                            offset = object.utcoffset()
                            if offset is not None:
                                sign = '+'
                                if offset < 0:
                                    offset = -offset
                                    sign = '-'
                                h, m = divmod(offset, 60)
                                zreplace = '%c%02d%02d' % (sign, h, m)
                    assert '%' not in zreplace
                    newformat.append(zreplace)
                elif ch == 'Z':
                    if Zreplace is None:
                        Zreplace = ""
                        if hasattr(object, "tzname"):
                            s = object.tzname()
                            if s is not None:
                                # strftime is going to have at this: escape %
                                Zreplace = s.replace('%', '%%')
                    newformat.append(Zreplace)
                else:
                    push('%')
                    push(ch)
            else:
                push('%')
        else:
            push(ch)
    newformat = "".join(newformat)
    return _time.strftime(newformat, timetuple)

def _call_tzinfo_method(self, tzinfo, methname):
    if tzinfo is None:
        return None
    return getattr(tzinfo, methname)(self)

def _check_utc_offset(name, offset):
    if offset is None:
        return
    if not isinstance(offset, (int, long)):
        raise TypeError("%s() must return None, int or long, not %s" %
                        (name, type(offset)))
    if -1440 < offset < 1440:
        return
    raise ValueError("%s()=%d, must be in -1439..1439" % (name, offset))

# This is a start at a struct tm workalike.  Goals:
#
# + Works the same way across platforms.
# + Handles all the fields datetime needs handled, without 1970-2038 glitches.
#
# Note:  I suspect it's best if this flavor of tm does *not* try to
# second-guess timezones or DST.  Instead fold whatever adjustments you want
# into the minutes argument (and the constructor will normalize).

_ORD1970 = _ymd2ord(1970, 1, 1) # base ordinal for UNIX epoch

class tmxxx:

    ordinal = None

    def __init__(self, year, month, day, hour=0, minute=0, second=0,
                 microsecond=0):
        # Normalize all the inputs, and store the normalized values.
        if not 0 <= microsecond <= 999999:
            carry, microsecond = divmod(microsecond, 1000000)
            second += carry
        if not 0 <= second <= 59:
            carry, second = divmod(second, 60)
            minute += carry
        if not 0 <= minute <= 59:
            carry, minute = divmod(minute, 60)
            hour += carry
        if not 0 <= hour <= 23:
            carry, hour = divmod(hour, 24)
            day += carry

        # That was easy.  Now it gets muddy:  the proper range for day
        # can't be determined without knowing the correct month and year,
        # but if day is, e.g., plus or minus a million, the current month
        # and year values make no sense (and may also be out of bounds
        # themselves).
        # Saying 12 months == 1 year should be non-controversial.
        if not 1 <= month <= 12:
            carry, month = divmod(month-1, 12)
            year += carry
            month += 1
            assert 1 <= month <= 12

        # Now only day can be out of bounds (year may also be out of bounds
        # for a datetime object, but we don't care about that here).
        # If day is out of bounds, what to do is arguable, but at least the
        # method here is principled and explainable.
        dim = _days_in_month(year, month)
        if not 1 <= day <= dim:
            # Move day-1 days from the first of the month.  First try to
            # get off cheap if we're only one day out of range (adjustments
            # for timezone alone can't be worse than that).
            if day == 0:    # move back a day
                month -= 1
                if month > 0:
                    day = _days_in_month(year, month)
                else:
                    year, month, day = year-1, 12, 31
            elif day == dim + 1:    # move forward a day
                month += 1
                day = 1
                if month > 12:
                    month = 1
                    year += 1
            else:
                self.ordinal = _ymd2ord(year, month, 1) + (day - 1)
                year, month, day = _ord2ymd(self.ordinal)

        self.year, self.month, self.day = year, month, day
        self.hour, self.minute, self.second = hour, minute, second
        self.microsecond = microsecond

    def toordinal(self):
        """Return proleptic Gregorian ordinal for the year, month and day.

        January 1 of year 1 is day 1.  Only the year, month and day values
        contribute to the result.
        """
        if self.ordinal is None:
            self.ordinal = _ymd2ord(self.year, self.month, self.day)
        return self.ordinal

    def time(self):
        "Return Unixish timestamp, as a float (assuming UTC)."
        days = self.toordinal() - _ORD1970   # convert to UNIX epoch
        seconds = ((days * 24. + self.hour)*60. + self.minute)*60.
        return seconds + self.second + self.microsecond / 1e6

    def ctime(self):
        "Return ctime() style string."
        weekday = self.toordinal() % 7 or 7
        return "%s %s %2d %02d:%02d:%02d %04d" % (
            _DAYNAMES[weekday],
            _MONTHNAMES[self.month],
            self.day,
            self.hour, self.minute, self.second,
            self.year)

class timedelta(object):
    """Represent the difference between two datetime objects.

    Supported operators:

    - add, subtract timedelta
    - unary plus, minus, abs
    - compare to timedelta
    - multiply, divide by int/long

    In addition, datetime supports subtraction of two datetime objects
    returning a timedelta, and addition or subtraction of a datetime
    and a timedelta giving a datetime.

    Representation: (days, seconds, microseconds).  Why?  Because I
    felt like it.
    """

    def __init__(self, days=0, seconds=0, microseconds=0,
                 # XXX The following should only be used as keyword args:
                 milliseconds=0, minutes=0, hours=0, weeks=0):
        # Doing this efficiently and accurately in C is going to be difficult
        # and error-prone, due to ubiquitous overflow possibilities, and that
        # C double doesn't have enough bits of precision to represent
        # microseconds over 10K years faithfully.  The code here tries to make
        # explicit where go-fast assumptions can be relied on, in order to
        # guide the C implementation; it's way more convoluted than speed-
        # ignoring auto-overflow-to-long idiomatic Python could be.

        # XXX Check that all inputs are ints, longs or floats.

        # Final values, all integer.
        # s and us fit in 32-bit signed ints; d isn't bounded.
        d = s = us = 0

        # Normalize everything to days, seconds, microseconds.
        days += weeks*7
        seconds += minutes*60 + hours*3600
        microseconds += milliseconds*1000

        # Get rid of all fractions, and normalize s and us.
        # Take a deep breath <wink>.
        if isinstance(days, float):
            dayfrac, days = _math.modf(days)
            daysecondsfrac, daysecondswhole = _math.modf(dayfrac * (24.*3600.))
            assert daysecondswhole == int(daysecondswhole)  # can't overflow
            s = int(daysecondswhole)
            assert days == long(days)
            d = long(days)
        else:
            daysecondsfrac = 0.0
            d = days
        assert isinstance(daysecondsfrac, float)
        assert abs(daysecondsfrac) <= 1.0
        assert isinstance(d, (int, long))
        assert abs(s) <= 24 * 3600
        # days isn't referenced again before redefinition

        if isinstance(seconds, float):
            secondsfrac, seconds = _math.modf(seconds)
            assert seconds == long(seconds)
            seconds = long(seconds)
            secondsfrac += daysecondsfrac
            assert abs(secondsfrac) <= 2.0
        else:
            secondsfrac = daysecondsfrac
        # daysecondsfrac isn't referenced again
        assert isinstance(secondsfrac, float)
        assert abs(secondsfrac) <= 2.0

        assert isinstance(seconds, (int, long))
        days, seconds = divmod(seconds, 24*3600)
        d += days
        s += int(seconds)    # can't overflow
        assert isinstance(s, int)
        assert abs(s) <= 2 * 24 * 3600
        # seconds isn't referenced again before redefinition

        usdouble = secondsfrac * 1e6
        assert abs(usdouble) < 2.1e6    # exact value not critical
        # secondsfrac isn't referenced again

        if isinstance(microseconds, float):
            microseconds += usdouble
            microseconds = round(microseconds)
            seconds, microseconds = divmod(microseconds, 1e6)
            assert microseconds == int(microseconds)
            assert seconds == long(seconds)
            days, seconds = divmod(seconds, 24.*3600.)
            assert days == long(days)
            assert seconds == int(seconds)
            d += long(days)
            s += int(seconds)   # can't overflow
            assert isinstance(s, int)
            assert abs(s) <= 3 * 24 * 3600
        else:
            seconds, microseconds = divmod(microseconds, 1000000)
            days, seconds = divmod(seconds, 24*3600)
            d += days
            s += int(seconds)    # can't overflow
            assert isinstance(s, int)
            assert abs(s) <= 3 * 24 * 3600
            microseconds = float(microseconds)
            microseconds += usdouble
            microseconds = round(microseconds)
        assert abs(s) <= 3 * 24 * 3600
        assert abs(microseconds) < 3.1e6

        # Just a little bit of carrying possible for microseconds and seconds.
        assert isinstance(microseconds, float)
        assert int(microseconds) == microseconds
        us = int(microseconds)
        seconds, us = divmod(us, 1000000)
        s += seconds    # cant't overflow
        assert isinstance(s, int)
        days, s = divmod(s, 24*3600)
        d += days

        assert isinstance(d, (int, long))
        assert isinstance(s, int) and 0 <= s < 24*3600
        assert isinstance(us, int) and 0 <= us < 1000000
        self.__days = d
        self.__seconds = s
        self.__microseconds = us
        if abs(d) > 999999999:
            raise OverflowError("timedelta # of days is too large: %d" % d)

    def __repr__(self):
        if self.__microseconds:
            return "%s(%d, %d, %d)" % ('datetime.' + self.__class__.__name__,
                                       self.__days,
                                       self.__seconds,
                                       self.__microseconds)
        if self.__seconds:
            return "%s(%d, %d)" % ('datetime.' + self.__class__.__name__,
                                   self.__days,
                                   self.__seconds)
        return "%s(%d)" % ('datetime.' + self.__class__.__name__, self.__days)

    def __str__(self):
        mm, ss = divmod(self.__seconds, 60)
        hh, mm = divmod(mm, 60)
        s = "%d:%02d:%02d" % (hh, mm, ss)
        if self.__days:
            def plural(n):
                return n, abs(n) != 1 and "s" or ""
            s = ("%d day%s, " % plural(self.__days)) + s
        if self.__microseconds:
            s = s + ".%06d" % self.__microseconds
        return s

    days = property(lambda self: self.__days, doc="days")
    seconds = property(lambda self: self.__seconds, doc="seconds")
    microseconds = property(lambda self: self.__microseconds,
                            doc="microseconds")

    def __add__(self, other):
        if isinstance(other, timedelta):
            return self.__class__(self.__days + other.__days,
                                  self.__seconds + other.__seconds,
                                  self.__microseconds + other.__microseconds)
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, timedelta):
            return self + -other
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, timedelta):
            return -self + other
        return NotImplemented

    def __neg__(self):
        return self.__class__(-self.__days,
                              -self.__seconds,
                              -self.__microseconds)

    def __pos__(self):
        return self

    def __abs__(self):
        if self.__days < 0:
            return -self
        else:
            return self

    def __mul__(self, other):
        if isinstance(other, (int, long)):
            return self.__class__(self.__days * other,
                                  self.__seconds * other,
                                  self.__microseconds * other)
        return NotImplemented

    __rmul__ = __mul__

    def __div__(self, other):
        if isinstance(other, (int, long)):
            usec = ((self.__days * (24*3600L) + self.__seconds) * 1000000 +
                    self.__microseconds)
            return self.__class__(0, 0, usec // other)
        return NotImplemented

    __floordiv__ = __div__

    def __cmp__(self, other):
        if not isinstance(other, timedelta):
            raise TypeError, ("can't compare timedelta to %s instance" %
                              type(other).__name__)
        return cmp(self.__getstate__(), other.__getstate__())

    def __hash__(self):
        return hash(self.__getstate__())

    def __nonzero__(self):
        return (self.__days != 0 or
                self.__seconds != 0 or
                self.__microseconds != 0)

    # Pickle support.
    # This magic class attr is necessary for pickle compatibility with the
    # C implementation.
    __safe_for_unpickling__ = True

    def __reduce__(self):
        return type(self), (), self.__getstate__()

    def __getstate__(self):
        return (self.__days, self.__seconds, self.__microseconds)

    def __setstate__(self, tup):
        self.__days, self.__seconds, self.__microseconds = tup

timedelta.min = timedelta(-999999999)
timedelta.max = timedelta(days=999999999, hours=23, minutes=59, seconds=59,
                          microseconds=999999)
timedelta.resolution = timedelta(microseconds=1)

class date(object):
    """Concrete date type.

    Constructors:

    __init__()
    fromtimestamp()
    today()
    fromordinal()

    Operators:

    __repr__, __str__
    __cmp__, __hash__
    __add__, __radd__, __sub__ (add/radd only with timedelta arg)

    Methods:

    timetuple()
    toordinal()
    weekday()
    isoweekday(), isocalendar(), isoformat()
    ctime()
    strftime()

    Properties (readonly):
    year, month, day
    """

    def __init__(self, year, month, day):
        """Constructor.

        Arguments:

        year, month, day (required, base 1)
        """
        if not MINYEAR <= year <= MAXYEAR:
            raise ValueError('year must be in %d..%d' % (MINYEAR, MAXYEAR),
                             year)
        if not 1 <= month <= 12:
            raise ValueError('month must be in 1..12', month)
        dim = _days_in_month(year, month)
        if not 1 <= day <= dim:
            raise ValueError('day must be in 1..%d' % dim, day)
        self.__year = year
        self.__month = month
        self.__day = day

    # Additional constructors

    def fromtimestamp(cls, t):
        "Construct a date from a POSIX timestamp (like time.time())."
        y, m, d, hh, mm, ss, weekday, jday, dst = _time.localtime(t)
        return cls(y, m, d)
    fromtimestamp = classmethod(fromtimestamp)

    def today(cls):
        "Construct a date from time.time()."
        t = _time.time()
        return cls.fromtimestamp(t)
    today = classmethod(today)

    def fromordinal(cls, n):
        """Contruct a date from a proleptic Gregorian ordinal.

        January 1 of year 1 is day 1.  Only the year, month and day are
        non-zero in the result.
        """
        y, m, d = _ord2ymd(n)
        return cls(y, m, d)
    fromordinal = classmethod(fromordinal)

    # Conversions to string

    def __repr__(self):
        "Convert to formal string, for repr()."
        return "%s(%d, %d, %d)" % ('datetime.' + self.__class__.__name__,
                                   self.__year,
                                   self.__month,
                                   self.__day)
    # XXX These shouldn't depend on time.localtime(), because that
    # clips the usable dates to [1970 .. 2038).  At least ctime() is
    # easily done without using strftime() -- that's better too because
    # strftime("%c", ...) is locale specific.

    def ctime(self):
        "Format a la ctime()."
        return tmxxx(self.__year, self.__month, self.__day).ctime()

    def strftime(self, fmt):
        "Format using strftime()."
        return _wrap_strftime(self, fmt, self.timetuple())

    def isoformat(self):
        """Return the date formatted according to ISO.

        This is 'YYYY-MM-DD'.

        References:
        - http://www.w3.org/TR/NOTE-datetime
        - http://www.cl.cam.ac.uk/~mgk25/iso-time.html
        """
        return "%04d-%02d-%02d" % (self.__year, self.__month, self.__day)

    __str__ = isoformat

    # Read-only field accessors
    year = property(lambda self: self.__year,
                    doc="year (%d-%d)" % (MINYEAR, MAXYEAR))
    month = property(lambda self: self.__month, doc="month (1-12)")
    day = property(lambda self: self.__day, doc="day (1-31)")

    # Standard conversions, __cmp__, __hash__ (and helpers)

    def timetuple(self):
        "Return local time tuple compatible with time.localtime()."
        return _build_struct_time(self.__year, self.__month, self.__day,
                                  0, 0, 0, -1)

    def toordinal(self):
        """Return proleptic Gregorian ordinal for the year, month and day.

        January 1 of year 1 is day 1.  Only the year, month and day values
        contribute to the result.
        """
        return _ymd2ord(self.__year, self.__month, self.__day)

    def __cmp__(self, other):
        "Three-way comparison."
        if isinstance(other, date):
            y, m, d = self.__year, self.__month, self.__day
            y2, m2, d2 = other.__year, other.__month, other.__day
            return cmp((y, m, d), (y2, m2, d2))
        else:
            raise TypeError, ("can't compare date to %s instance" %
                              type(other).__name__)

    def __hash__(self):
        "Hash."
        return hash(self.__getstate__())

    # Computations

    def _checkOverflow(self, year):
        if not MINYEAR <= year <= MAXYEAR:
            raise OverflowError("date +/-: result year %d not in %d..%d" %
                                (year, MINYEAR, MAXYEAR))

    def __add__(self, other):
        "Add a date to a timedelta."
        if isinstance(other, timedelta):
            t = tmxxx(self.__year,
                      self.__month,
                      self.__day + other.days)
            self._checkOverflow(t.year)
            result = self.__class__(t.year, t.month, t.day)
            return result
        raise TypeError
        # XXX Should be 'return NotImplemented', but there's a bug in 2.2...

    __radd__ = __add__

    def __sub__(self, other):
        """Subtract two dates, or a date and a timedelta."""
        if isinstance(other, timedelta):
            return self + timedelta(-other.days)
        if isinstance(other, date):
            days1 = self.toordinal()
            days2 = other.toordinal()
            return timedelta(days1 - days2)
        return NotImplemented

    def weekday(self):
        "Return day of the week, where Monday == 0 ... Sunday == 6."
        return (self.toordinal() + 6) % 7

    # Day-of-the-week and week-of-the-year, according to ISO

    def isoweekday(self):
        "Return day of the week, where Monday == 1 ... Sunday == 7."
        # 1-Jan-0001 is a Monday
        return self.toordinal() % 7 or 7

    def isocalendar(self):
        """Return a 3-tuple containing ISO year, week number, and weekday.

        The first ISO week of the year is the (Mon-Sun) week
        containing the year's first Thursday; everything else derives
        from that.

        The first week is 1; Monday is 1 ... Sunday is 7.

        ISO calendar algorithm taken from
        http://www.phys.uu.nl/~vgent/calendar/isocalendar.htm
        """
        year = self.__year
        week1monday = _isoweek1monday(year)
        today = _ymd2ord(self.__year, self.__month, self.__day)
        # Internally, week and day have origin 0
        week, day = divmod(today - week1monday, 7)
        if week < 0:
            year -= 1
            week1monday = _isoweek1monday(year)
            week, day = divmod(today - week1monday, 7)
        elif week >= 52:
            if today >= _isoweek1monday(year+1):
                year += 1
                week = 0
        return year, week+1, day+1

    # Pickle support.

    def __getstate__(self):
        yhi, ylo = divmod(self.__year, 256)
        return "%c%c%c%c" % (yhi, ylo, self.__month, self.__day)

    def __setstate__(self, string):
        assert len(string) == 4
        yhi, ylo, self.__month, self.__day = map(ord, string)
        self.__year = yhi * 256 + ylo

date.min = date(1, 1, 1)
date.max = date(9999, 12, 31)
date.resolution = timedelta(days=1)


class time(object):
    """Concrete time type.

    Constructors:

    __init__()

    Operators:

    __repr__, __str__
    __cmp__, __hash__

    Methods:

    strftime()
    isoformat()

    Properties (readonly):
    hour, minute, second, microsecond
    """

    def __init__(self, hour=0, minute=0, second=0, microsecond=0):
        """Constructor.

        Arguments:

        hour, minute (required)
        second, microsecond (default to zero)
        """
        if not 0 <= hour <= 23:
            raise ValueError('hour must be in 0..23', hour)
        if not 0 <= minute <= 59:
            raise ValueError('minute must be in 0..59', minute)
        if not 0 <= second <= 59:
            raise ValueError('second must be in 0..59', second)
        if not 0 <= microsecond <= 999999:
            raise ValueError('microsecond must be in 0..999999', microsecond)
        self.__hour = hour
        self.__minute = minute
        self.__second = second
        self.__microsecond = microsecond

    # Read-only field accessors
    hour = property(lambda self: self.__hour, doc="hour (0-23)")
    minute = property(lambda self: self.__minute, doc="minute (0-59)")
    second = property(lambda self: self.__second, doc="second (0-59)")
    microsecond = property(lambda self: self.__microsecond,
                           doc="microsecond (0-999999)")

    # Standard conversions, __cmp__, __hash__ (and helpers)

    def __cmp__(self, other):
        """Three-way comparison."""
        if isinstance(other, time):
            return cmp((self.__hour, self.__minute, self.__second,
                        self.__microsecond),
                       (other.__hour, other.__minute, other.__second,
                        other.__microsecond))
        raise TypeError, ("can't compare time to %s instance" %
                          type(other).__name__)

    def __hash__(self):
        """Hash."""
        # Force use of time.__getstate__().  If self is of a subclass
        # type, we want the hash of its projection onto time, not the
        # hash of all the extra stuff it may contain.
        return hash(time.__getstate__(self))

    # Conversions to string

    def __repr__(self):
        """Convert to formal string, for repr()."""
        if self.__microsecond != 0:
            s = ", %d, %d" % (self.__second, self.__microsecond)
        elif self.__second != 0:
            s = ", %d" % self.__second
        else:
            s = ""
        return "%s(%d, %d%s)" % ('datetime.' + self.__class__.__name__,
                                 self.__hour, self.__minute, s)

    def isoformat(self):
        """Return the time formatted according to ISO.

        This is 'HH:MM:SS.mmmmmm', or 'HH:MM:SS' if self.microsecond == 0.
        """
        return _format_time(self.__hour, self.__minute, self.__second,
                            self.__microsecond)

    __str__ = isoformat

    def strftime(self, fmt):
        """Format using strftime().  The date part of the timestamp passed
        to underlying strftime should not be used.
        """
        timetuple = (0, 0, 0,
                     self.__hour, self.__minute, self.__second,
                     0, 0, -1)
        return _wrap_strftime(self, fmt, timetuple)

    def __nonzero__(self):
        return (self.__hour != 0 or
                self.__minute != 0 or
                self.__second != 0 or
                self.__microsecond != 0)

    # Pickle support.

    def __getstate__(self):
        us2, us3 = divmod(self.__microsecond, 256)
        us1, us2 = divmod(us2, 256)
        return ("%c" * 6) % (self.__hour, self.__minute, self.__second,
                             us1, us2, us3)

    def __setstate__(self, string):
        assert len(string) == 6
        self.__hour, self.__minute, self.__second, us1, us2, us3 = \
                                                            map(ord, string)
        self.__microsecond = (((us1 << 8) | us2) << 8) | us3

time.min = time(0, 0, 0)
time.max = time(23, 59, 59, 999999)
time.resolution = timedelta(microseconds=1)

class tzinfo(object):
    """Abstract base class for time zone info classes.

    Subclasses must override the name(), utcoffset() and dst() methods.
    """

    def tzname(self, dt):
        "datetime -> string name of time zone."
        raise NotImplementedError("tzinfo subclass must override tzname()")

    def utcoffset(self, dt):
        "datetime -> minutes east of UTC (negative for west of UTC)"
        raise NotImplementedError("tzinfo subclass must override utcoffset()")

    def dst(self, dt):
        """datetime -> DST offset in minutes east of UTC.

        Return 0 if DST not in effect.  utcoffset() must include the DST
        offset.
        """
        raise NotImplementedError("tzinfo subclass must override dst()")

    # pickle support

    __safe_for_unpickling__ = True

    def __reduce__(self):
        return type(self), (), self.__dict__

class timetz(time):
    """Time with time zone.

    Constructors:

    __init__()

    Operators:

    __repr__, __str__
    __cmp__, __hash__

    Methods:

    strftime()
    isoformat()
    utcoffset()
    tzname()
    dst()

    Properties (readonly):
    hour, minute, second, microsecond, tzinfo
    """

    def __init__(self, hour=0, minute=0, second=0, microsecond=0, tzinfo=None):
        """Constructor.

        Arguments:

        hour, minute (required)
        second, microsecond (default to zero)
        tzinfo (default to None)
        """
        import datetime
        if tzinfo is not None and not isinstance(tzinfo, datetime.tzinfo):
            raise TypeError("tzinfo argument must be None or of a tzinfo "
                            "subclass")
        super(timetz, self).__init__(hour, minute, second, microsecond)
        self.__tzinfo = tzinfo

    # Read-only field accessors
    tzinfo = property(lambda self: self.__tzinfo, doc="timezone info object")

    # Standard conversions, __cmp__, __hash__ (and helpers)

    def __cmp__(self, other):
        """Three-way comparison."""
        if not isinstance(other, time):
            raise TypeError("can't compare timetz to %s instance" %
                            type(other).__name__)
        superself = super(timetz, self)
        supercmp = superself.__cmp__
        mytz = self.__tzinfo
        ottz = None
        if isinstance(other, timetz):
            ottz = other.__tzinfo
        if mytz is ottz:
            return supercmp(other)
        myoff = otoff = None
        if mytz is not None:
            myoff = mytz.utcoffset(self)
        if ottz is not None:
            otoff = ottz.utcoffset(other)
        if myoff == otoff:
            return supercmp(other)
        if myoff is None or otoff is None:
            raise TypeError, "cannot mix naive and timezone-aware time"
        myhhmm = self.hour * 60 + self.minute - myoff
        othhmm = other.hour * 60 + other.minute - otoff
        return cmp((myhhmm, self.second, self.microsecond),
                   (othhmm, other.second, other.microsecond))

    def __hash__(self):
        """Hash."""
        tzoff = self.utcoffset()
        if not tzoff: # zero or None!
            return super(timetz, self).__hash__()
        h, m = divmod(self.hour * 60 + self.minute - tzoff, 60)
        if 0 <= h < 24:
            return hash(time(h, m, self.second, self.microsecond))
        # Unfortunately it is not possible to construct a new time object
        # and use super().__hash__(), since hour is out-of-bounds.
        return hash((h, m, self.second, self.microsecond))

    # Conversion to string

    def _tzstr(self, sep=":"):
        """Return formatted timezone offset (+xx:xx) or None."""
        off = self.utcoffset()
        if off is not None:
            if off < 0:
                sign = "-"
                off = -off
            else:
                sign = "+"
            hh, mm = divmod(off, 60)
            if hh >= 24:
                raise ValueError("utcoffset must be in -1439 .. 1439")
            off = "%s%02d%s%02d" % (sign, hh, sep, mm)
        return off

    def __repr__(self):
        """Convert to formal string, for repr()."""
        s = super(timetz, self).__repr__()
        if self.__tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self.__tzinfo + ")"
        return s

    def isoformat(self):
        """Return the time formatted according to ISO.

        This is 'HH:MM:SS.mmmmmm+zz:zz', or 'HH:MM:SS+zz:zz' if
        self.microsecond == 0.
        """
        s = super(timetz, self).isoformat()
        tz = self._tzstr()
        if tz: s += tz
        return s

    __str__ = isoformat

    # Timezone functions

    def utcoffset(self):
        """Return the timezone offset in minutes east of UTC (negative west of
        UTC)."""
        offset = _call_tzinfo_method(self, self.__tzinfo, "utcoffset")
        _check_utc_offset("utcoffset", offset)
        return offset

    def tzname(self):
        """Return the timezone name.

        Note that the name is 100% informational -- there's no requirement that
        it mean anything in particular. For example, "GMT", "UTC", "-500",
        "-5:00", "EDT", "US/Eastern", "America/New York" are all valid replies.
        """
        name = _call_tzinfo_method(self, self.__tzinfo, "tzname")
        return name

    def dst(self):
        """Return 0 if DST is not in effect, or the DST offset (in minutes
        eastward) if DST is in effect.

        This is purely informational; the DST offset has already been added to
        the UTC offset returned by utcoffset() if applicable, so there's no
        need to consult dst() unless you're interested in displaying the DST
        info.
        """
        offset = _call_tzinfo_method(self, self.__tzinfo, "dst")
        _check_utc_offset("dst", offset)
        return offset

    def __nonzero__(self):
        if self.second or self.microsecond:
            return 1
        offset = self.utcoffset() or 0
        return self.hour * 60 + self.minute - offset != 0

    # Pickle support.

    def __getstate__(self):
        basestate = time.__getstate__(self)
        if self.__tzinfo is None:
            return (basestate,)
        else:
            return (basestate, self.__tzinfo)

    def __setstate__(self, state):
        if not isinstance(state, tuple):
            raise TypeError("timetz.__setstate__() requires a tuple arg")
        if not 1 <= len(state) <= 2:
            raise TypeError("timetz.__setstate__() requires a 1-tuple or "
                            "2-tuple argument")
        time.__setstate__(self, state[0])
        if len(state) == 1:
            self.__tzinfo = None
        else:
            self.__tzinfo = state[1]

timetz.min = timetz(0, 0, 0)
timetz.max = timetz(23, 59, 59, 999999)
timetz.resolution = timedelta(microseconds=1)


class datetime(date):
    """Concrete date/time type, inheriting from date.

    Constructors:

    __init__()
    now(), utcnow()
    fromtimestamp(), utcfromtimestamp()
    fromordinal()

    Operators:

    __repr__, __str__
    __cmp__, __hash__
    __add__, __radd__, __sub__ (add/radd only with timedelta arg)

    Methods:

    timetuple()
    toordinal()
    weekday()
    isoweekday(), isocalendar(), isoformat()
    ctime()
    strftime()

    Properties (readonly):
    year, month, day, hour, minute, second, microsecond
    """

    def __init__(self, year, month, day, hour=0, minute=0, second=0,
                 microsecond=0):
        """Constructor.

        Arguments:

        year, month, day (required, base 1)
        hour, minute, second, microsecond (default to zero)
        """
        super(datetime, self).__init__(year, month, day)
        if not 0 <= hour <= 23:
            raise ValueError('hour must be in 0..23', hour)
        if not 0 <= minute <= 59:
            raise ValueError('minute must be in 0..59', minute)
        if not 0 <= second <= 59:
            raise ValueError('second must be in 0..59', second)
        if not 0 <= microsecond <= 999999:
            raise ValueError('microsecond must be in 0..999999', microsecond)
        # XXX This duplicates __year, __month, __day for convenience :-(
        self.__year = year
        self.__month = month
        self.__day = day
        self.__hour = hour
        self.__minute = minute
        self.__second = second
        self.__microsecond = microsecond

    # Additional constructors

    def fromtimestamp(cls, t):
        "Construct a datetime from a POSIX timestamp (like time.time())."
        y, m, d, hh, mm, ss, weekday, jday, dst = _time.localtime(t)
        us = int((t % 1.0) * 1000000)
        return cls(y, m, d, hh, mm, ss, us)
    fromtimestamp = classmethod(fromtimestamp)

    # XXX This is supposed to do better than we *can* do by using time.time(),
    # XXX if the platform supports a more accurate way.  The C implementation
    # XXX uses gettimeofday on platforms that have it, but that isn't
    # XXX available from Python.  So now() may return different results
    # XXX across the implementations.
    def now(cls):
        "Construct a datetime from time.time()."
        t = _time.time()
        return cls.fromtimestamp(t)
    now = classmethod(now)

    def utcfromtimestamp(cls, t):
        "Construct a UTC datetime from a POSIX timestamp (like time.time())."
        y, m, d, hh, mm, ss, weekday, jday, dst = _time.gmtime(t)
        us = int((t % 1.0) * 1000000)
        return cls(y, m, d, hh, mm, ss, us)
    utcfromtimestamp = classmethod(utcfromtimestamp)

    def utcnow(cls):
        "Construct a UTC datetime from time.time()."
        t = _time.time()
        return cls.utcfromtimestamp(t)
    utcnow = classmethod(utcnow)

    def combine(cls, date, time):
        "Construct a datetime from a given date and a given time."
        import datetime
        if not isinstance(date, datetime.date):
            raise TypeError("combine's first argument must be a date")
        if not isinstance(time, datetime.time):
            raise TypeError("combine's second argument must be a time")
        return cls(date.year, date.month, date.day,
                   time.hour, time.minute, time.second, time.microsecond)
    combine = classmethod(combine)

    # Conversions to string.

    def __repr__(self):
        "Convert to formal string, for repr()."
        L = [self.__year, self.__month, self.__day, # These are never zero
             self.__hour, self.__minute, self.__second, self.__microsecond]
        while L[-1] == 0:
            del L[-1]
        s = ", ".join(map(str, L))
        return "%s(%s)" % ('datetime.' + self.__class__.__name__, s)

    def __str__(self):
        "Convert to string, for str()."
        return self.isoformat(sep=' ')

    # Read-only field accessors
    hour = property(lambda self: self.__hour, doc="hour (0-23)")
    minute = property(lambda self: self.__minute, doc="minute (0-59)")
    second = property(lambda self: self.__second, doc="second (0-59)")
    microsecond = property(lambda self: self.__microsecond,
                           doc="microsecond (0-999999)")

    # Standard conversions, __cmp__, __hash__ (and helpers)

    def timetuple(self):
        "Return local time tuple compatible with time.localtime()."
        return _build_struct_time(self.__year, self.__month, self.__day,
                                  self.__hour, self.__minute, self.__second,
                                  -1)

    def date(self):
        "Return the date part."
        return date(self.__year, self.__month, self.__day)

    def time(self):
        "Return the time part."
        return time(self.__hour, self.__minute, self.__second,
                    self.__microsecond)

    def __cmp__(self, other):
        "Three-way comparison."
        if isinstance(other, datetime):
            return cmp((self.__year, self.__month, self.__day,
                        self.__hour, self.__minute, self.__second,
                        self.__microsecond),
                       (other.__year, other.__month, other.__day,
                        other.__hour, other.__minute, other.__second,
                        other.__microsecond))
        raise TypeError, ("can't compare datetime to %s instance" %
                          type(other).__name__)

    def __hash__(self):
        "Hash."
        import datetime
        # Force use of datetime.__getstate__().  If self is of a subclass
        # type, we want the hash of its projection onto datetime, not the
        # hash of all the extra stuff it may contain.
        return hash(datetime.datetime.__getstate__(self))

    # Formatting methods

    # XXX These shouldn't depend on time.localtime(), because that
    # clips the usable dates to [1970 .. 2038).  At least ctime() is
    # easily done without using strftime() -- that's better too because
    # strftime("%c", ...) is locale specific.

    # XXX An additional question is whether ctime() should renormalize
    # to local time, or display the time as entered (which may be
    # confusing since it doesn't show the timezone).

    def ctime(self):
        "Format a la ctime()."
        t = tmxxx(self.__year, self.__month, self.__day, self.__hour,
                  self.__minute, self.__second)
        return t.ctime()

    # Computations

    def __add__(self, other):
        "Add a datetime to a timedelta."
        if isinstance(other, timedelta):
            t = tmxxx(self.__year,
                      self.__month,
                      self.__day + other.days,
                      self.__hour,
                      self.__minute,
                      self.__second + other.seconds,
                      self.__microsecond + other.microseconds)
            self._checkOverflow(t.year)
            result = self.__class__(t.year, t.month, t.day,
                                    t.hour, t.minute, t.second,
                                    t.microsecond)
            return result
        raise TypeError
        # XXX Should be 'return NotImplemented', but there's a bug in 2.2...

    __radd__ = __add__

    def __sub__(self, other):
        """Subtract two datetimes, or a datetime and a timedelta.

        An int/long/float argument is also allowed, interpreted as seconds.
        """
        if isinstance(other, timedelta):
            return self + -other
        if isinstance(other, datetime):
            days1 = self.toordinal()
            days2 = other.toordinal()
            secs1 = (self.__second + self.__minute * 60 + self.__hour * 3600)
            secs2 = (other.__second +
                     (other.__minute) * 60 +
                     other.__hour * 3600)
            return timedelta(days1 - days2,
                             secs1 - secs2,
                             self.__microsecond - other.__microsecond)
        return NotImplemented

    # ISO formats including time

    def isoformat(self, sep='T'):
        """Return the time formatted according to ISO.

        This is 'YYYY-MM-DD HH:MM:SS.mmmmmm', or 'YYYY-MM-DD HH:MM:SS' if
        self.microsecond == 0.

        Optional argument sep specifies the separator between date and
        time, default 'T'.
        """
        return ("%04d-%02d-%02d%c" % (self.__year, self.__month, self.__day,
                                      sep) +
                _format_time(self.__hour, self.__minute, self.__second,
                             self.__microsecond))

    # Pickle support.

    def __getstate__(self):
        yhi, ylo = divmod(self.__year, 256)
        us2, us3 = divmod(self.__microsecond, 256)
        us1, us2 = divmod(us2, 256)
        return ("%c" * 10) % (yhi, ylo, self.__month, self.__day, self.__hour,
                              self.__minute, self.__second, us1, us2, us3)

    def __setstate__(self, string):
        assert len(string) == 10
        (yhi, ylo, self.__month, self.__day, self.__hour,
         self.__minute, self.__second, us1, us2, us3) = map(ord, string)
        self.__year = yhi * 256 + ylo
        self.__microsecond = (((us1 << 8) | us2) << 8) | us3

datetime.min = datetime(1, 1, 1)
datetime.max = datetime(9999, 12, 31, 23, 59, 59, 999999)
datetime.resolution = timedelta(microseconds=1)


class datetimetz(datetime):

    # XXX needs docstrings and conversion APIs
    # See http://www.zope.org/Members/fdrake/DateTimeWiki/TimeZoneInfo

    def __init__(self, year, month, day, hour=0, minute=0, second=0,
                 microsecond=0, tzinfo=None):
        import datetime
        if tzinfo is not None and not isinstance(tzinfo, datetime.tzinfo):
            raise TypeError("tzinfo argument must be None or of a tzinfo "
                            "subclass")
        super(datetimetz, self).__init__(year, month, day,
                                         hour, minute, second, microsecond)
        self.__tzinfo = tzinfo

    tzinfo = property(lambda self: self.__tzinfo, doc="timezone info object")

    def fromtimestamp(cls, t, tzinfo=None):
        """Construct a datetimetz from a POSIX timestamp (like time.time()).

        A timezone info object may be passed in as well.
        """
        y, m, d, hh, mm, ss, weekday, jday, dst = _time.localtime(t)
        us = int((t % 1.0) * 1000000)
        return cls(y, m, d, hh, mm, ss, us, tzinfo)
    fromtimestamp = classmethod(fromtimestamp)

    def now(cls, tzinfo=None):
        "Construct a datetime from time.time() and optional time zone info."
        t = _time.time()
        return cls.fromtimestamp(t, tzinfo)
    now = classmethod(now)

    def combine(cls, date, time):
        "Construct a datetime from a given date and a given time."
        return cls(date.year, date.month, date.day,
                   time.hour, time.minute, time.second, time.microsecond,
                   getattr(time, 'tzinfo', None))
    combine = classmethod(combine)

    def timetuple(self):
        "Return local time tuple compatible with time.localtime()."
        dst = self.dst()
        if dst is None:
            dst = -1
        elif dst:
            dst = 1
        return _build_struct_time(self.year, self.month, self.day,
                                  self.hour, self.minute, self.second,
                                  dst)

    def utctimetuple(self):
        "Return UTC time tuple compatible with time.gmtime()."
        y, m, d = self.year, self.month, self.day
        hh, mm, ss = self.hour, self.minute, self.second
        offset = self.utcoffset()
        if offset:  # neither None nor 0
            tm = tmxxx(y, m, d, hh, mm - offset)
            y, m, d = tm.year, tm.month, tm.day
            hh, mm = tm.hour, tm.minute
        return _build_struct_time(y, m, d, hh, mm, ss, 0)

    def timetz(self):
        "Return the time part."
        return timetz(self.hour, self.minute, self.second, self.microsecond,
                      self.__tzinfo)

    def isoformat(self, sep='T'):
        s = super(datetimetz, self).isoformat(sep)
        off = self.utcoffset()
        if off is not None:
            if off < 0:
                sign = "-"
                off = -off
            else:
                sign = "+"
            hh, mm = divmod(off, 60)
            s += "%s%02d:%02d" % (sign, hh, mm)
        return s

    def __repr__(self):
        s = super(datetimetz, self).__repr__()
        if self.__tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self.__tzinfo + ")"
        return s

    def utcoffset(self):
        """Return the timezone offset in minutes east of UTC (negative west of
        UTC)."""
        offset = _call_tzinfo_method(self, self.__tzinfo, "utcoffset")
        _check_utc_offset("utcoffset", offset)
        return offset

    def tzname(self):
        """Return the timezone name.

        Note that the name is 100% informational -- there's no requirement that
        it mean anything in particular. For example, "GMT", "UTC", "-500",
        "-5:00", "EDT", "US/Eastern", "America/New York" are all valid replies.
        """
        name = _call_tzinfo_method(self, self.__tzinfo, "tzname")
        return name

    def dst(self):
        """Return 0 if DST is not in effect, or the DST offset (in minutes
        eastward) if DST is in effect.

        This is purely informational; the DST offset has already been added to
        the UTC offset returned by utcoffset() if applicable, so there's no
        need to consult dst() unless you're interested in displaying the DST
        info.
        """
        offset = _call_tzinfo_method(self, self.__tzinfo, "dst")
        _check_utc_offset("dst", offset)
        return offset

    def __add__(self, other):
        result = super(datetimetz, self).__add__(other)
        assert isinstance(result, datetimetz)
        result.__tzinfo = self.__tzinfo
        return result

    __radd__ = __add__

    def __sub__(self, other):
        supersub = super(datetimetz, self).__sub__
        if not isinstance(other, datetime):
            return supersub(other) # XXX should set tzinfo on result
        mytz = self.__tzinfo
        ottz = None
        if isinstance(other, datetimetz):
            ottz = other.__tzinfo
        if mytz is ottz:
            return supersub(other)
        myoff = self.utcoffset()
        otoff = other.utcoffset()
        if myoff == otoff:
            return supersub(other)
        if myoff is None or otoff is None:
            raise TypeError, "cannot mix naive and timezone-aware time"
        return supersub(other) + timedelta(minutes=otoff-myoff)

    def __cmp__(self, other):
        if not isinstance(other, datetime):
            raise TypeError("can't compare datetime to %s instance" %
                            type(other).__name__)
        superself = super(datetimetz, self)
        supercmp = superself.__cmp__
        myoff = self.utcoffset()
        otoff = None
        if isinstance(other, datetimetz):
            otoff = other.utcoffset()
        if myoff == otoff:
            return supercmp(other)
        if myoff is None or otoff is None:
            raise TypeError, "cannot mix naive and timezone-aware time"
        # XXX What follows could be done more efficiently...
        diff = superself.__sub__(other) + timedelta(minutes=otoff-myoff)
        if diff.days < 0:
            return -1
        if diff == timedelta():
            return 0
        return 1

    def __hash__(self):
        tzoff = self.utcoffset()
        if tzoff is None:
            return super(datetimetz, self).__hash__()
        days = _ymd2ord(self.year, self.month, self.day)
        seconds = self.hour * 3600 + (self.minute - tzoff) * 60 + self.second
        return hash(timedelta(days, seconds, self.microsecond))

    def __getstate__(self):
        basestate = datetime.__getstate__(self)
        if self.__tzinfo is None:
            return (basestate,)
        else:
            return (basestate, self.__tzinfo)

    def __setstate__(self, state):
        if not isinstance(state, tuple):
            raise TypeError("datetimetz.__setstate__() requires a tuple arg")
        if not 1 <= len(state) <= 2:
            raise TypeError("datetimetz.__setstate__() requires a 1-tuple or "
                            "2-tuple argument")
        datetime.__setstate__(self, state[0])
        if len(state) == 1:
            self.__tzinfo = None
        else:
            self.__tzinfo = state[1]


datetimetz.min = datetimetz(1, 1, 1)
datetimetz.max = datetimetz(9999, 12, 31, 23, 59, 59, 999999)
datetimetz.resolution = timedelta(microseconds=1)


def _isoweek1monday(year):
    # Helper to calculate the day number of the Monday starting week 1
    # XXX This could be done more efficiently
    THURSDAY = 3
    firstday = _ymd2ord(year, 1, 1)
    firstweekday = (firstday + 6) % 7 # See weekday() above
    week1monday = firstday - firstweekday
    if firstweekday > THURSDAY:
        week1monday += 7
    return week1monday

# Pickle support.  __getstate__ and __setstate__ work fine on their own,
# but only because the classes here are implemented in Python.  The C
# implementation had to get much trickier, and the code following emulates
# what the C code had to do, so that pickles produced by the Python
# implementation can be read by the C implementation, and vice versa.
# XXX This isn't entirely successful yet.  The Python implementation can
# XXX read pickles written by the C implementation now, but the
# XXX C implementation can't read timetz, datetimetz, or timedelta
# XXX pickles written by the Python implementation.  See doc.txt.

def _date_pickler(date):
    state = date.__getstate__()
    return _date_unpickler, (state,)

def _date_unpickler(state):
    self = date(1, 1, 1)
    self.__setstate__(state)
    return self

def _datetime_pickler(dt):
    state = dt.__getstate__()
    return _datetime_unpickler, (state,)

def _datetime_unpickler(state):
    self = datetime(1, 1, 1)
    self.__setstate__(state)
    return self

def _time_pickler(t):
    state = t.__getstate__()
    return _time_unpickler, (state,)

def _time_unpickler(state):
    self = time()
    self.__setstate__(state)
    return self

def _tzinfo_pickler(tz):
    return _tzinfo_unpickler, ()

def _tzinfo_unpickler():
    self = tzinfo()
    return self

def _timetz_pickler(tz):
    state = tz.__getstate__()
    return _timetz_unpickler, (state,)

def _timetz_unpickler(state):
    self = timetz()
    self.__setstate__(state)
    return self

def _datetimetz_pickler(dtz):
    state = dtz.__getstate__()
    return _datetimetz_unpickler, (state,)

def _datetimetz_unpickler(state):
    self = datetimetz(1, 1, 1)
    self.__setstate__(state)
    return self

# Register pickle/unpickle functions.
from copy_reg import pickle
pickle(date, _date_pickler, _date_unpickler)
pickle(datetime, _datetime_pickler, _datetime_unpickler)
pickle(time, _time_pickler, _time_unpickler)
pickle(tzinfo, _tzinfo_pickler, _tzinfo_unpickler)
pickle(timetz, _timetz_pickler, _timetz_unpickler)
pickle(datetimetz, _datetimetz_pickler, _datetimetz_unpickler)
del pickle

def _test():
    import test_datetime
    test_datetime.test_main()

if __name__ == "__main__":
    _test()
