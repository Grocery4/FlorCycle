from datetime import date
import calendar

class CycleCalendar(calendar.HTMLCalendar):
    def __init__(self, highlights=None):
        super().__init__(firstweekday=0)
        self.highlights = highlights or {}
        self._year = None
        self._month = None

        self._date_to_class = {}
        for css_class, dates in self.highlights.items():
            for d in dates:
                self._date_to_class[d] = css_class

    def formatmonth(self, theyear, themonth, withyear=True):
        self._year = theyear
        self._month = themonth
        return super().formatmonth(theyear, themonth, withyear)

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'
        
        date_str = f"{self._year:04d}-{self._month:02d}-{day:02d}"
        css_class = self._date_to_class.get(date_str, "")
        
        if css_class:
            return f'<td class="{css_class}">{day}</td>'
        else:
            return f'<td>{day}</td>'

def renderCalendar(year, month, menstruation_dates: dict=None, ovulation_dates: dict=None):
    highlights = {
        'highlight-menstruation' : menstruation_dates or {},
        'highlight-ovulation' : ovulation_dates or {}
    }
    
    return CycleCalendar(highlights=highlights).formatmonth(year, month)

def renderMultipleCalendars(year: int, months: list, menstruation_dates:dict=None, ovulation_dates:dict=None):
    calendar = CycleCalendar(highlights=highlights)
    highlights = {
        'highlight-menstruation' : menstruation_dates or {},
        'highlight-ovulation' : ovulation_dates or {}
    }

    html_calendar = ''
    
    for m in months:
        html_calendar += calendar.formatmonth(year, m)
        html_calendar += '\n'
    
    return html_calendar
        


# idea: pass a set of dates `menstruation_dates` and `ovulation_dates`
# and highlight them.
# to figure out which months to render: get the month of first prediction day and last prediction day
if __name__ == '__main__':

    html_calendar = renderMultipleCalendars(2024, [1,2,3,4], {'2024-02-12'})
    print(html_calendar)