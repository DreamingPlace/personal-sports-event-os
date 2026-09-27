from collections import defaultdict
from decimal import Decimal, InvalidOperation
from datetime import timedelta
from zoneinfo import ZoneInfo
import re
from ...models import assert_model,ModelError,sellable,canonical
from ...models.core import moment,seating_key,_shape
from ...models.schema import HOLD_FIELDS
from ...revenue import calculate,product_details
from ..gate import approved,CONTENT_SCHEMAS,RULES

def check(data,g,start,end,releasing,sessions,seatmap,year):
    for seat in data['seating']:
        sid,tier=seat['session_id'],seat['tier']
        rates=[data['scenarios'][k]['session_rates'][sid]*data['scenarios'][k]['tier_rates'][tier] for k in ('low','mid','high')]
        if rates!=sorted(rates):g.add('Q026','BLOCK',f'scenarios/{sid}/{tier}','low <= mid <= high',rates)
    paid=[data['scenarios'][k]['paid_rights_rate'] for k in ('low','mid','high')]
    if paid!=sorted(paid):g.add('Q026','BLOCK','scenarios/paid_rights_rate','low <= mid <= high',paid)
