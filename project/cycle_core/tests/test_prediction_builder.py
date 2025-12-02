from django.test import TestCase
from datetime import datetime, timedelta

from cycle_core.models import CycleDetails, CycleWindow
from cycle_core.services import PredictionBuilder


class TestPredictionBuilder(TestCase):

    def setUp(self):
        # Example baseline values
        self.base_menstruation_date = datetime(2025, 1, 1).date()
        self.avg_cycle_duration = 28
        self.avg_menstruation_duration = 5

        self.cd = CycleDetails(
            base_menstruation_date=self.base_menstruation_date,
            avg_cycle_duration=self.avg_cycle_duration,
            avg_menstruation_duration=self.avg_menstruation_duration
        )

    def test_predict_menstruation(self):
        start, end = PredictionBuilder.predictMenstruation(self.cd.base_menstruation_date, self.cd.avg_cycle_duration, self.cd.avg_menstruation_duration)

        expected_start = (self.base_menstruation_date + timedelta(days=self.avg_cycle_duration))
        expected_end = expected_start + timedelta(days=self.avg_menstruation_duration-1)

        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)

    def test_predict_ovulation(self):
        first_day = datetime(2025, 2, 1).date()
        start, end = PredictionBuilder.predictOvulation(first_day)

        expected_start = first_day + timedelta(days=CycleDetails.AVG_MIN_OVULATION_DAY)
        expected_end = first_day + timedelta(days=CycleDetails.AVG_MAX_OVULATION_DAY)

        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)

    def test_generate_prediction(self):
        cwp = PredictionBuilder.generatePrediction(
            self.cd.base_menstruation_date,
            self.cd.avg_cycle_duration,
            self.cd.avg_menstruation_duration,
        )
        # Expected menstruation window
        expected_menstruation_start = self.base_menstruation_date + timedelta(days=self.avg_cycle_duration)
        expected_menstruation_end = expected_menstruation_start + timedelta(days=self.avg_menstruation_duration-1)

        # Expected ovulation window
        expected_ovulation_start = expected_menstruation_start + timedelta(days=CycleDetails.AVG_MIN_OVULATION_DAY)
        expected_ovulation_end = expected_menstruation_start + timedelta(days=CycleDetails.AVG_MAX_OVULATION_DAY)

        self.assertIsInstance(cwp, CycleWindow)
        self.assertEqual(cwp.menstruation_start, expected_menstruation_start)
        self.assertEqual(cwp.menstruation_end, expected_menstruation_end)
        self.assertEqual(cwp.min_ovulation_window, expected_ovulation_start)
        self.assertEqual(cwp.max_ovulation_window, expected_ovulation_end)

    def test_generate_multiple_predictions(self):
        predictions = PredictionBuilder.generateMultiplePredictions(self.cd, 3)

        self.assertEqual(len(predictions), 3)
        
        expected_first_start = self.base_menstruation_date + timedelta(days=self.avg_cycle_duration)
        expected_first_end = expected_first_start + timedelta(days=self.avg_menstruation_duration-1)
        
        self.assertEqual(predictions[0].menstruation_start, expected_first_start)
        self.assertEqual(predictions[0].menstruation_end, expected_first_end)
        
        for i in range(1, len(predictions)):
            expected_start = predictions[i-1].menstruation_start + timedelta(days=self.avg_cycle_duration)
            self.assertEqual(predictions[i].menstruation_start, expected_start)

if __name__ == "__main__":
    TestCase.main()
