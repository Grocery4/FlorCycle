from datetime import date

from calendar_core.services import render_multiple_calendars


#TODO - refactor to use relativedelta
#TODO - might move into calendar_core
# returns a list of date objects
def get_months_range(predictions: list) -> list[date]:
    if not predictions:
        return []

    first_date = min(p.menstruation_start for p in predictions)
    last_date = max(p.menstruation_end for p in predictions)

    months = []
    current = date(first_date.year, first_date.month, 1)

    while current <= date(last_date.year, last_date.month, 1):
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return months


def get_highlighted_dates(predictions:list) -> tuple[list, list]:
    menstruation_highlights = []
    ovulation_highlights = []
    for elem in predictions:
        menstruation_highlights.extend(elem.getMenstruationDatesAsList())
        ovulation_highlights.extend(elem.getOvulationDatesAsList())

    return (menstruation_highlights, ovulation_highlights)


def generate_calendars(predictions):
        months = get_months_range(predictions)
        menstruation_highlights, ovulation_highlights = get_highlighted_dates(predictions)
        return render_multiple_calendars(months, menstruation_highlights, ovulation_highlights)
