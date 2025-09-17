from django.test import TestCase
from django.core.exceptions import ValidationError

from cycle_core.models import CycleDetails
import datetime


class TestCycleDetailsModel(TestCase):
    def setUp(self):
        self.DATE = datetime.datetime.strptime("2025-09-24", "%Y-%m-%d")
        self.AVG_CYCLE_DURATION = 5
        self.AVG_MENSTRUATION_DURATION = 30

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
