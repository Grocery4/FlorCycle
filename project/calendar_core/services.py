from datetime import date
from enum import Enum
import calendar
from django.utils.formats import date_format

class CalendarType(Enum):
    STANDARD = 0
    SELECTABLE = 1

class CycleCalendar(calendar.HTMLCalendar):
    def __init__(self, highlights=None):
        super().__init__(firstweekday=0)
        self.highlights = highlights or {}
        self._year = None
        self._month = None

        self._date_to_classes = {}
        for css_class, dates in self.highlights.items():
            for d in dates:
                if d not in self._date_to_classes:
                    self._date_to_classes[d] = []
                self._date_to_classes[d].append(css_class)

    def formatmonthname(self, theyear, themonth, withyear=True):
        """
        Return a month name as a table row.
        """
        if withyear:
            s = '%s %s' % (date_format(date(theyear, themonth, 1), "F"), theyear)
        else:
            s = '%s' % date_format(date(theyear, themonth, 1), "F")
        return '<tr><th colspan="7" class="%s">%s</th></tr>' % (self.cssclass_month_head, s)

    def formatweekday(self, day):
        """
        Return a weekday name as a table header.
        """
        # 2001-01-01 was a Monday
        d = date(2001, 1, 1 + day)
        s = date_format(d, "D")
        return '<th class="%s">%s</th>' % (self.cssclasses[day], s)

    def formatmonth(self, theyear, themonth, withyear=True):
        self._year = theyear
        self._month = themonth
        return super().formatmonth(theyear, themonth, withyear)

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'
        
        date_str = f"{self._year:04d}-{self._month:02d}-{day:02d}"
        css_classes = self._date_to_classes.get(date_str, [])
        
        css_class_str = " ".join(css_classes)
        
        if css_class_str:
            return f'<td class="{css_class_str}" data-date="{date_str}"><div class="day-content">{day}</div></td>'
        else:
            return f'<td data-date="{date_str}"><div class="day-content">{day}</div></td>'



class SelectableCycleCalendar(CycleCalendar):

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'

        date_str = f"{self._year:04d}-{self._month:02d}-{day:02d}"
        current_date = date(self._year, self._month, day)
        css_classes = self._date_to_classes.get(date_str, [])
        css_class_str = " ".join(css_classes)

        td_class = f' class="{css_class_str}"' if css_class_str else ""

        checkbox_id = f"day_{date_str}"

        is_future = current_date > date.today()
        disabled_attr = ' disabled' if is_future else ''

        return (
            f'<td{td_class}>'
            f'  <label class="day-label" for="{checkbox_id}">'
            f'    <input type="checkbox" id="{checkbox_id}" '
            f'           name="selected_days" value="{date_str}"{disabled_attr} />'
            f'    <span class="day-number">{day}</span>'
            f'  </label>'
            f'</td>'
        )

def render_calendar(dt: date, menstruation_dates: dict=None, ovulation_dates: dict=None, log_dates: dict=None, calendar_type: CalendarType=CalendarType.STANDARD):
    highlights = {
        'highlight-menstruation' : menstruation_dates or {},
        'highlight-ovulation' : ovulation_dates or {},
        'has-log': log_dates or {}
    }
    
    if calendar_type == CalendarType.STANDARD:
        return CycleCalendar(highlights=highlights).formatmonth(dt.year, dt.month)
    elif calendar_type == CalendarType.SELECTABLE:
        return SelectableCycleCalendar(highlights=highlights).formatmonth(dt.year, dt.month)

def render_multiple_calendars(months: list[date], menstruation_dates: dict=None, ovulation_dates: dict=None, log_dates: dict=None, calendar_type: CalendarType=CalendarType.STANDARD) -> list[str]:
    highlights = {
        'highlight-menstruation': menstruation_dates or {},
        'highlight-ovulation': ovulation_dates or {},
        'has-log': log_dates or {}
    }

    if calendar_type == CalendarType.STANDARD:
        calendar = CycleCalendar(highlights=highlights)
    elif calendar_type == CalendarType.SELECTABLE:
        calendar = SelectableCycleCalendar(highlights=highlights)

    html_calendars = []
    for dt in months:
        cal = calendar.formatmonth(dt.year, dt.month)
        html_calendars.append(cal)

    return html_calendars