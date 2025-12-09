from django.test import TestCase
from django.contrib.auth import get_user_model
from cycle_core.models import CycleWindow, CycleStats, CycleDetails
from cycle_core.services import calculate_ovulation_timing_from_logs, update_ovulation_stats
from log_core.models import DailyLog
from datetime import date, timedelta

User = get_user_model()

class OvulationPredictionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.cycle_details = CycleDetails.objects.create(user=self.user)
        # Get or create CycleStats to avoid IntegrityError
        self.stats, created = CycleStats.objects.get_or_create(user=self.user)
        self.stats.log_count = 6
        self.stats.save()
    
    def test_ovulation_timing_with_positive_tests(self):
        """Test ovulation calculation with positive ovulation tests"""
        # Create 6 cycles with logs - each cycle needs its own positive test day
        for i in range(6):
            start = date(2025, 1, 1) + timedelta(days=i*28)
            end = start + timedelta(days=4)
            cycle = CycleWindow.objects.create(
                user=self.user,
                menstruation_start=start,
                menstruation_end=end,
                min_ovulation_window=start + timedelta(days=12),
                max_ovulation_window=start + timedelta(days=16),
                is_prediction=False
            )
            
            # Add positive ovulation test on day 14 of this cycle
            positive_day = start + timedelta(days=14)
            log, created = DailyLog.objects.get_or_create(
                user=self.user,
                date=positive_day,
                defaults={'cycle_window': cycle, 'ovulation_test': 'POSITIVE'}
            )
            # If it already existed, update it
            if not created:
                log.cycle_window = cycle
                log.ovulation_test = 'POSITIVE'
                log.save()
        
        # Verify cycles were created
        cycles = CycleWindow.objects.filter(user=self.user, is_prediction=False)
        self.assertEqual(cycles.count(), 6)
        
        # Verify positive tests were created
        positive_logs = DailyLog.objects.filter(user=self.user, ovulation_test='POSITIVE')
        self.assertEqual(positive_logs.count(), 6)
        
        # Calculate ovulation timing
        result = calculate_ovulation_timing_from_logs(self.user)
        self.assertIsNotNone(result, f"Expected ovulation timing to be calculated, got None. Logs: {DailyLog.objects.filter(user=self.user).count()}")
        # Should be around day 12-16 (14 ± 2)
        self.assertEqual(result[0], 12)
        self.assertEqual(result[1], 16)
    
    def test_ovulation_stats_update(self):
        """Test that update_ovulation_stats correctly updates CycleStats"""
        update_ovulation_stats(self.stats)
        self.stats.refresh_from_db()
        # Should have values (either calculated or defaults)
        self.assertIsNotNone(self.stats.avg_ovulation_start_day)
        self.assertIsNotNone(self.stats.avg_ovulation_end_day)
    
    def test_insufficient_logs_returns_none(self):
        """Test that insufficient logs returns None"""
        result = calculate_ovulation_timing_from_logs(self.user, min_logs=6)
        self.assertIsNone(result)  # Only 0 cycles, need 6
    
    def test_no_positive_tests_uses_defaults(self):
        """Test that lack of positive tests falls back to defaults"""
        # Create 6 cycles but NO positive ovulation tests
        for i in range(6):
            start = date(2025, 1, 1) + timedelta(days=i*28)
            CycleWindow.objects.create(
                user=self.user,
                menstruation_start=start,
                menstruation_end=start + timedelta(days=4),
                min_ovulation_window=start + timedelta(days=12),
                max_ovulation_window=start + timedelta(days=16),
                is_prediction=False
            )
        
        result = calculate_ovulation_timing_from_logs(self.user)
        self.assertIsNone(result)  # No positive tests = None
        
        # But update_ovulation_stats should set defaults
        update_ovulation_stats(self.stats)
        self.stats.refresh_from_db()
        self.assertEqual(self.stats.avg_ovulation_start_day, 12)  # Default
        self.assertEqual(self.stats.avg_ovulation_end_day, 16)    # Default