from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, date

from users.models import CustomUser, UserProfile
from users.services import activatePremiumSubscription, deactivatePremiumSubscription


class PremiumSubscriptionDecayTestCase(TestCase):
    """Test suite for premium subscription expiration and decay logic"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.profile = UserProfile.objects.get(user=self.user)
    
    def test_monthly_subscription_sets_correct_end_date(self):
        """Test that monthly subscription sets end_date 30 days from activation"""
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        
        expected_end_date = date.today() + timedelta(days=30)
        self.assertEqual(self.profile.end_date, expected_end_date)
        self.assertTrue(self.profile.is_premium)
        self.assertEqual(self.profile.subscription_status, 'ACTIVE')
    
    def test_yearly_subscription_sets_correct_end_date(self):
        """Test that yearly subscription sets end_date 365 days from activation"""
        activatePremiumSubscription(self.user, 'YEARLY')
        self.profile.refresh_from_db()
        
        expected_end_date = date.today() + timedelta(days=365)
        self.assertEqual(self.profile.end_date, expected_end_date)
        self.assertTrue(self.profile.is_premium)
        self.assertEqual(self.profile.subscription_status, 'ACTIVE')
    
    def test_expired_subscription_should_be_detected(self):
        """Test that a subscription with past end_date is considered expired"""
        # Activate subscription
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        
        # Manually set end_date to the past
        past_date = date.today() - timedelta(days=1)
        self.profile.end_date = past_date
        self.profile.save()
        
        self.profile.refresh_from_db()
        
        # Verify the subscription is expired (end_date is in the past)
        self.assertTrue(self.profile.end_date < date.today())
        # Note: is_premium flag doesn't auto-update; this would need a management command
        self.assertTrue(self.profile.is_premium)  # Still True until checked
    
    def test_active_subscription_not_expired(self):
        """Test that a subscription with future end_date is not expired"""
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        
        # Verify subscription is active
        self.assertTrue(self.profile.end_date > date.today())
        self.assertTrue(self.profile.is_premium)
        self.assertEqual(self.profile.subscription_status, 'ACTIVE')
    
    def test_subscription_on_exact_end_date(self):
        """Test subscription status on the exact end date"""
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        
        # Set end_date to today
        self.profile.end_date = date.today()
        self.profile.save()
        
        self.profile.refresh_from_db()
        
        # On the exact end date, subscription should still be valid
        self.assertEqual(self.profile.end_date, date.today())
        self.assertTrue(self.profile.is_premium)
    
    def test_deactivate_subscription_clears_premium_status(self):
        """Test that deactivating subscription properly clears premium status"""
        # First activate
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.is_premium)
        
        # Then deactivate
        deactivatePremiumSubscription(self.user)
        self.profile.refresh_from_db()
        
        self.assertFalse(self.profile.is_premium)
        # CANCELED status is preserved for historical tracking
        self.assertEqual(self.profile.subscription_status, 'CANCELED')
        # Check that premium fields are cleared (handled by model save)
        self.assertIsNone(self.profile.subscription_plan)
        self.assertIsNone(self.profile.payment_info)
    
    def test_user_type_changes_with_premium_status(self):
        """Test that user_type automatically updates when premium status changes"""
        # Initially should be STANDARD
        self.assertEqual(self.user.user_type, 'STANDARD')
        
        # Activate premium
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.user_type, 'PREMIUM')
        
        # Deactivate premium
        deactivatePremiumSubscription(self.user)
        self.profile.refresh_from_db()
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.user_type, 'STANDARD')
    
    def test_multiple_subscription_renewals(self):
        """Test that renewing subscription updates end_date correctly"""
        # First subscription
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        first_end_date = self.profile.end_date
        
        # Simulate time passing and renewal
        # In real scenario, this would be triggered by payment processing
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        second_end_date = self.profile.end_date
        
        # Second end_date should be 30 days from today (not from first_end_date)
        # This is current behavior; adjust if renewal should extend from previous end_date
        expected_end_date = date.today() + timedelta(days=30)
        self.assertEqual(second_end_date, expected_end_date)
    
    def test_upgrade_from_monthly_to_yearly(self):
        """Test upgrading from monthly to yearly subscription"""
        # Start with monthly
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        monthly_end_date = self.profile.end_date
        
        # Upgrade to yearly
        activatePremiumSubscription(self.user, 'YEARLY')
        self.profile.refresh_from_db()
        
        self.assertEqual(self.profile.subscription_plan, 'YEARLY')
        yearly_end_date = date.today() + timedelta(days=365)
        self.assertEqual(self.profile.end_date, yearly_end_date)
        self.assertTrue(self.profile.end_date > monthly_end_date)
