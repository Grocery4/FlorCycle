from django.test import TestCase
from datetime import timedelta, date

from users.models import CustomUser, UserProfile
from users.services import activatePremiumSubscription, deactivatePremiumSubscription


class HasActivePremiumPropertyTestCase(TestCase):
    """Test suite for the has_active_premium property using subscription_status"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.profile = UserProfile.objects.get(user=self.user)
    
    def test_non_premium_user_has_no_active_premium(self):
        """Test that non-premium users return False for has_active_premium"""
        self.assertFalse(self.profile.is_premium)
        self.assertFalse(self.profile.has_active_premium)
    
    def test_active_subscription_returns_true(self):
        """Test that active premium subscription returns True"""
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        
        self.assertTrue(self.profile.is_premium)
        self.assertEqual(self.profile.subscription_status, 'ACTIVE')
        self.assertTrue(self.profile.has_active_premium)
    
    def test_expired_status_returns_false(self):
        """Test that EXPIRED subscription_status returns False"""
        # Activate subscription
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        
        # Manually set status to EXPIRED (as management command would do)
        self.profile.subscription_status = 'EXPIRED'
        self.profile.is_premium = False
        self.profile.save()
        self.profile.refresh_from_db()
        
        self.assertFalse(self.profile.is_premium)
        self.assertEqual(self.profile.subscription_status, 'EXPIRED')
        self.assertFalse(self.profile.has_active_premium)
    
    def test_premium_true_but_status_expired_returns_false(self):
        """Test that is_premium=True with EXPIRED status returns False"""
        # Edge case: is_premium not updated but status is EXPIRED
        self.profile.is_premium = True
        self.profile.subscription_status = 'EXPIRED'
        self.profile.save()
        self.profile.refresh_from_db()
        
        # Should be False because status is not ACTIVE
        self.assertFalse(self.profile.has_active_premium)
    
    def test_premium_true_but_status_canceled_returns_false(self):
        """Test that is_premium=True with CANCELED status returns False"""
        self.profile.is_premium = True
        self.profile.subscription_status = 'CANCELED'
        self.profile.save()
        self.profile.refresh_from_db()
        
        # Should be False because status is not ACTIVE
        self.assertFalse(self.profile.has_active_premium)
    
    def test_premium_true_but_no_status_returns_false(self):
        """Test that is_premium=True with None status returns False"""
        self.profile.is_premium = True
        self.profile.subscription_status = None
        self.profile.save()
        self.profile.refresh_from_db()
        
        # Should be False because status is not ACTIVE
        self.assertFalse(self.profile.has_active_premium)
    
    def test_deactivated_subscription_returns_false(self):
        """Test that deactivated subscription returns False"""
        # Activate then deactivate
        activatePremiumSubscription(self.user, 'MONTHLY')
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.has_active_premium)
        
        deactivatePremiumSubscription(self.user)
        self.profile.refresh_from_db()
        
        self.assertFalse(self.profile.is_premium)
        # CANCELED status is now preserved for historical tracking
        self.assertEqual(self.profile.subscription_status, 'CANCELED')
        self.assertFalse(self.profile.has_active_premium)
    
    def test_both_conditions_required(self):
        """Test that BOTH is_premium and subscription_status='ACTIVE' are required"""
        # Test 1: is_premium=False, status=ACTIVE
        self.profile.is_premium = False
        self.profile.subscription_status = 'ACTIVE'
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.has_active_premium)
        
        # Test 2: is_premium=True, status=None
        self.profile.is_premium = True
        self.profile.subscription_status = None
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.has_active_premium)
        
        # Test 3: Both True and ACTIVE
        self.profile.is_premium = True
        self.profile.subscription_status = 'ACTIVE'
        self.profile.save()
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.has_active_premium)
