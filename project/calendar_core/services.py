from datetime import date
from enum import Enum
import calendar


class CalendarType(Enum):
    STANDARD = 0
    SELECTABLE = 1

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



class SelectableCycleCalendar(CycleCalendar):

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'

        date_str = f"{self._year:04d}-{self._month:02d}-{day:02d}"
        css_class = self._date_to_class.get(date_str, "")

        # Ensure consistent td class string
        td_class = f' class="{css_class}"' if css_class else ""

        # Checkbox ID for <label for="">
        checkbox_id = f"day_{date_str}"

        return (
            f'<td{td_class}>'
            f'  <label class="day-label" for="{checkbox_id}">'
            f'    <input type="checkbox" id="{checkbox_id}" '
            f'           name="selected_days[]" value="{date_str}" />'
            f'    <span class="day-number">{day}</span>'
            f'  </label>'
            f'</td>'
        )

def renderCalendar(year, month, menstruation_dates: dict=None, ovulation_dates: dict=None, calendar_type: CalendarType=CalendarType.STANDARD):
    highlights = {
        'highlight-menstruation' : menstruation_dates or {},
        'highlight-ovulation' : ovulation_dates or {}
    }
    
    if calendar_type == CalendarType.STANDARD:
        return CycleCalendar(highlights=highlights).formatmonth(year, month)
    elif calendar_type == CalendarType.SELECTABLE:
        return SelectableCycleCalendar(highlights=highlights).formatmonth(year,month)

# accepts a list of (year, month)
def renderMultipleCalendars(months: list[tuple[int, int]], menstruation_dates: dict=None, ovulation_dates: dict=None, calendar_type: CalendarType=CalendarType.STANDARD) -> list[str]:
    highlights = {
        'highlight-menstruation': menstruation_dates or {},
        'highlight-ovulation': ovulation_dates or {}
    }

    if calendar_type == CalendarType.STANDARD:
        calendar = CycleCalendar(highlights=highlights)
    elif calendar_type == CalendarType.SELECTABLE:
        calendar = SelectableCycleCalendar(highlights=highlights)

    html_calendars = []
    for year, month in months:
        cal = ''
        cal += calendar.formatmonth(year, month)
        cal += '\n'
        html_calendars.append(cal)

    return html_calendars
        


# idea: pass a set of dates `menstruation_dates` and `ovulation_dates`
# and highlight them.
# to figure out which months to render: get the month of first prediction day and last prediction day
if __name__ == '__main__':

    html_calendar = renderMultipleCalendars(2024, [1,2,3,4], {'2024-02-12'})
    print(html_calendar)