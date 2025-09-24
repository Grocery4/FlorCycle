from django.test import TestCase

from datetime import date
from unittest.mock import patch

from cycle_core.models import CycleWindow, CycleDetails
from guest_mode.services import getMonthsRange, getHighlightedDates, generateCalendars


class GetMonthsRangeTests(TestCase):
    def test_empty_predictions(self):
        self.assertEqual(getMonthsRange([]), [])

    def test_single_month(self):
        cw = CycleWindow(
            menstruation_start=date(2025, 1, 10),
            menstruation_end=date(2025, 1, 15),
            min_ovulation_window=date(2025, 1, 20),
            max_ovulation_window=date(2025, 1, 23),
        )
        self.assertEqual(getMonthsRange([cw]), [(2025, 1)])

    def test_multiple_months(self):
        cw1 = CycleWindow(
            menstruation_start=date(2025, 1, 28),
            menstruation_end=date(2025, 2, 2),
            min_ovulation_window=date(2025, 2, 10),
            max_ovulation_window=date(2025, 2, 12),
        )
        cw2 = CycleWindow(
            menstruation_start=date(2025, 3, 5),
            menstruation_end=date(2025, 4, 7),
            min_ovulation_window=date(2025, 3, 15),
            max_ovulation_window=date(2025, 3, 18),
        )
        result = getMonthsRange([cw1, cw2])
        self.assertEqual(result, [(2025, 1), (2025, 2), (2025, 3), (2025, 4)])

    def test_cross_year(self):
        cw = CycleWindow(
            menstruation_start=date(2025, 12, 25),
            menstruation_end=date(2026, 1, 5),
            min_ovulation_window=date(2026, 1, 10),
            max_ovulation_window=date(2026, 1, 15),
        )
        result = getMonthsRange([cw])
        self.assertEqual(result, [(2025, 12), (2026, 1)])


class GetHighlightedDatesTests(TestCase):
    def test_highlighted_dates(self):
        cw = CycleWindow(
            menstruation_start=date(2025, 1, 1),
            menstruation_end=date(2025, 1, 3),
            min_ovulation_window=date(2025, 1, 10),
            max_ovulation_window=date(2025, 1, 12),
        )
        menstruation, ovulation = getHighlightedDates([cw])
        self.assertEqual(
            menstruation,
            [date(2025, 1, 1).strftime('%Y-%m-%d'), date(2025, 1, 2).strftime('%Y-%m-%d'), date(2025, 1, 3).strftime('%Y-%m-%d')],
        )
        self.assertEqual(
            ovulation,
            [date(2025, 1, 10).strftime('%Y-%m-%d'), date(2025, 1, 11).strftime('%Y-%m-%d'), date(2025, 1, 12).strftime('%Y-%m-%d')],
        )