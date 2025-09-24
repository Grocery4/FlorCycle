from datetime import date

from calendar_core.services import renderMultipleCalendars


# returns a list of (year, month)
def getMonthsRange(predictions: list) -> list[tuple[int,int]]:
    if not predictions:
        return []

    first_date = min(p.menstruation_start for p in predictions)
    last_date = max(p.menstruation_end for p in predictions)

    months = []
    current = date(first_date.year, first_date.month, 1)

    while current <= date(last_date.year, last_date.month, 1):
        months.append((current.year, current.month))
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return months


def getHighlightedDates(predictions:list) -> tuple[list, list]:
    menstruation_highlights = []
    ovulation_highlights = []
    for elem in predictions:
        menstruation_highlights.extend(elem.getMenstruationDatesAsList())
        ovulation_highlights.extend(elem.getOvulationDatesAsList())

    return (menstruation_highlights, ovulation_highlights)


def generateCalendars(predictions):
        months = getMonthsRange(predictions)
        menstruation_highlights, ovulation_highlights = getHighlightedDates(predictions)
        print(menstruation_highlights, ovulation_highlights)
        return renderMultipleCalendars(months, menstruation_highlights, ovulation_highlights)
