'''tzinfo timezone information for EST.'''
from pytz.tzinfo import DstTzInfo
from pytz.tzinfo import memorized_datetime as d
from pytz.tzinfo import memorized_ttinfo as i

class EST(DstTzInfo):
    '''EST timezone definition. See datetime.tzinfo for details'''

    zone = 'EST'

    _utc_transition_times = [
d(1,1,1,0,0,0),
d(1908,4,22,5,19,36),
        ]

    _transition_info = [
i(-19200,0,'CMT'),
i(-18000,0,'EST'),
        ]

EST = EST()

