from .common import *

class Venue(RowsModule):
    module_id='core.venue'
    provides=('venues',)
    identity=('venue_id',)
    row_schema=obj(dict(venue_id=S,name=S,timezone=S))
    def validate(self,c,g):
        super().validate(c,g)
        from zoneinfo import ZoneInfo
        for r in self.rows(c):ZoneInfo(r['timezone'])

    def calculate(self,c):return {r['venue_id']:r for r in self.rows(c)}
