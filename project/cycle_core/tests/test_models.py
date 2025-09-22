from django.test import TestCase
from django.core.exceptions import ValidationError

from cycle_core.models import CycleDetails, CycleWindow
import datetime


class TestCycleDetailsModel(TestCase):
    def setUp(self):
        self.DATE = datetime.datetime.strptime("2025-09-24", "%Y-%m-%d").date()
        self.AVG_CYCLE_DURATION = 30
        self.AVG_MENSTRUATION_DURATION = 5

    def test_successful_insert(self):
        obj = CycleDetails.objects.create(last_menstruation_date=self.DATE, avg_cycle_duration=self.AVG_CYCLE_DURATION, avg_menstruation_duration=self.AVG_MENSTRUATION_DURATION)
        self.assertEqual(obj.last_menstruation_date, self.DATE)
        self.assertEqual(obj.avg_cycle_duration, self.AVG_CYCLE_DURATION)
        self.assertEqual(obj.avg_menstruation_duration, self.AVG_MENSTRUATION_DURATION)

    def test_invalid_avg_cycle_duration(self):
        invalid_value = -1
        obj = CycleDetails.objects.create(
            last_menstruation_date=self.DATE,
            avg_cycle_duration=invalid_value,
            avg_menstruation_duration=self.AVG_MENSTRUATION_DURATION
        )
        with self.assertRaises(ValidationError):
            obj.full_clean()

        invalid_value = 999
        obj = CycleDetails.objects.create(
            last_menstruation_date=self.DATE,
            avg_cycle_duration=invalid_value,
            avg_menstruation_duration=self.AVG_MENSTRUATION_DURATION
        )
        with self.assertRaises(ValidationError):
            obj.full_clean()
            

    def test_invalid_avg_menstruation_duration(self):
        invalid_value = -1
        obj = CycleDetails.objects.create(last_menstruation_date=self.DATE,
        avg_cycle_duration=self.AVG_CYCLE_DURATION,
        avg_menstruation_duration=invalid_value
        )
        with self.assertRaises(ValidationError):
            obj.full_clean()

        invalid_value = 999
        obj = CycleDetails.objects.create(last_menstruation_date=self.DATE,
        avg_cycle_duration=self.AVG_CYCLE_DURATION,
        avg_menstruation_duration=invalid_value
        )
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_as_cycle_window(self):
        cd = CycleDetails(
            last_menstruation_date=self.DATE,
            avg_cycle_duration=self.AVG_CYCLE_DURATION,
            avg_menstruation_duration=self.AVG_MENSTRUATION_DURATION
        )

        cw, created = cd.asCycleWindow()

        expected_menstruation_start = self.DATE
        expected_menstruation_end = self.DATE + datetime.timedelta(days=self.AVG_MENSTRUATION_DURATION)
        expected_ovulation_start = self.DATE + datetime.timedelta(days=CycleDetails.AVG_MIN_OVULATION_DAY)
        expected_ovulation_end = self.DATE + datetime.timedelta(days=CycleDetails.AVG_MAX_OVULATION_DAY)
        expected_created = True

        self.assertIsInstance(cw, CycleWindow)
        self.assertEqual(cw.menstruation_start, expected_menstruation_start)
        self.assertEqual(cw.menstruation_end, expected_menstruation_end)
        self.assertEqual(cw.min_ovulation_window, expected_ovulation_start)
        self.assertEqual(cw.max_ovulation_window, expected_ovulation_end)
        self.assertEqual(created, expected_created)

        cw2, created2 = cd.asCycleWindow()
        expected_created = False

        self.assertIsInstance(cw2, CycleWindow)
        self.assertEqual(created2, expected_created)


class TestCycleWindowPrediction(TestCase):
    def setUp(self):
        # Common base dates
        self.start = datetime.date(2025, 7, 1)
        self.end = datetime.date(2025, 7, 5)
        self.ovul_min = datetime.date(2025, 7, 10)
        self.ovul_max = datetime.date(2025, 7, 14)

    def test_get_menstruation_dates_as_list(self):
        data = CycleWindow(
            menstruation_start=self.start,
            menstruation_end=self.end,
            min_ovulation_window=self.ovul_min,
            max_ovulation_window=self.ovul_max
        )
        expected = [self.start + datetime.timedelta(days=i) for i in range(5)]
        self.assertEqual(data.getMenstruationDatesAsList(), expected)
        

    def test_get_ovulation_dates_as_list(self):
        data = CycleWindow(
            menstruation_start=self.start,
            menstruation_end=self.end,
            min_ovulation_window=self.ovul_min,
            max_ovulation_window=self.ovul_max
        )
        expected = [self.ovul_min + datetime.timedelta(days=i) for i in range(5)]
        self.assertEqual(data.getOvulationDatesAsList(), expected)

    def test_menstruation_dates_missing_period_start(self):
        data = CycleWindow(
            menstruation_start=None,
            menstruation_end=self.end,
            min_ovulation_window=self.ovul_min,
            max_ovulation_window=self.ovul_max
        )
        with self.assertRaises(ValueError):
            data.getMenstruationDatesAsList()

    def test_ovulation_dates_missing_min(self):
        data = CycleWindow(
            menstruation_start=self.start,
            menstruation_end=self.end,
            min_ovulation_window=None,
            max_ovulation_window=self.ovul_max
        )
        with self.assertRaises(ValueError):
            data.getOvulationDatesAsList()

    def test_menstruation_duration(self):
        data = CycleWindow(
            menstruation_start=self.start,
            menstruation_end=self.end,
            min_ovulation_window=self.ovul_min,
            max_ovulation_window=self.ovul_max
        )

        expected = (self.end - self.start) + datetime.timedelta(days=1)
        self.assertEqual(data.getMenstruationDuration(), expected)

    def test_ovulation_duration(self):
        data = CycleWindow(
            menstruation_start=self.start,
            menstruation_end=self.end,
            min_ovulation_window=self.ovul_min,
            max_ovulation_window=self.ovul_max
        )

        expected = (self.end - self.start) + datetime.timedelta(days=1)
        self.assertEqual(data.getOvulationDuration(), expected)


if __name__ == '__main__':
    TestCase.main()