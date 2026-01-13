from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model

from cycle_core.services import generate_prediction_based_on_log_count
from cycle_core.models import CycleStats, CycleDetails, MIN_LOG_FOR_STATS

User = get_user_model()

class TestGeneratePredictionBasedOnLogCount(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='testuser', password='password')
        # Create CycleDetails for the user
        self.cycle_details = CycleDetails.objects.create(
            user=self.user,
            avg_cycle_duration=28,
            avg_menstruation_duration=5
        )
        # CycleStats is automatically created via signal when CycleDetails is created
        self.cycle_stats = CycleStats.objects.get(user=self.user)

    @patch('cycle_core.services.PredictionBuilder.generateMultiplePredictions')
    def test_uses_stats_when_log_count_sufficient(self, mock_predict):
        # Case: CycleStats exists and log_count >= MIN_LOG_FOR_STATS
        self.cycle_stats.log_count = MIN_LOG_FOR_STATS
        self.cycle_stats.save()
        self.user.refresh_from_db()

        generate_prediction_based_on_log_count(self.user)

        # Should use cycle_stats as source
        mock_predict.assert_called_with(self.cycle_stats, user=self.user)

    @patch('cycle_core.services.PredictionBuilder.generateMultiplePredictions')
    def test_uses_details_when_log_count_insufficient(self, mock_predict):
        # Case: CycleStats exists but log_count < MIN_LOG_FOR_STATS
        self.cycle_stats.log_count = MIN_LOG_FOR_STATS - 1
        self.cycle_stats.save()
        self.user.refresh_from_db()
        
        generate_prediction_based_on_log_count(self.user)
        
        # Should use cycle_details as source
        mock_predict.assert_called_with(self.cycle_details, user=self.user)

    @patch('cycle_core.services.PredictionBuilder.generateMultiplePredictions')
    def test_uses_details_when_stats_missing(self, mock_predict):
        # Case: CycleStats does not exist
        self.cycle_stats.delete()
        self.user.refresh_from_db()
        
        generate_prediction_based_on_log_count(self.user)
        
        # Should fallback to cycle_details
        mock_predict.assert_called_with(self.cycle_details, user=self.user)

    def test_raises_value_error_if_no_stats_or_details(self):
        # Case: Neither CycleStats nor CycleDetails exist
        self.cycle_stats.delete()
        self.cycle_details.delete()
        self.user.refresh_from_db()

        with self.assertRaises(ValueError):
            generate_prediction_based_on_log_count(self.user)
