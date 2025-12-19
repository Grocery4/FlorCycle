from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser, UserProfile, ModeratorProfile
from forum_core.models import Thread, Comment

class ForumEditDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = CustomUser.objects.create_user(
            username='author', email='author@example.com', password='password123', user_type='PREMIUM'
        )
        self.other_user = CustomUser.objects.create_user(
            username='other', email='other@example.com', password='password123', user_type='PREMIUM'
        )
        self.moderator = CustomUser.objects.create_user(
            username='mod', email='mod@example.com', password='password123', user_type='MODERATOR'
        )
        
        # Configure profiles
        for u in [self.author, self.other_user]:
            p, _ = UserProfile.objects.get_or_create(user=u)
            p.is_configured = True
            p.is_premium = True
            p.save()
            
        # Moderator needs ModeratorProfile to keep user_type='MODERATOR'
        mp, _ = ModeratorProfile.objects.get_or_create(
            user=self.moderator, 
            defaults={'can_suspend_users': True, 'can_edit_posts': True, 'is_verified': True}
        )
        mp.save()

        # Create a thread and a comment
        self.thread = Thread.objects.create(
            title='Initial Title', content='Initial content', created_by=self.author
        )
        self.comment = Comment.objects.create(
            content='Initial comment', thread=self.thread, created_by=self.author
        )

    def test_author_can_edit_thread(self):
        self.client.force_login(self.author)
        data = {'title': 'Updated Title', 'content': 'Updated content'}
        response = self.client.post(reverse('forum_core:edit_thread', args=[self.thread.id]), data)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, 'Initial Title')  # Title should NOT change
        self.assertEqual(self.thread.content, 'Updated content')
        self.assertRedirects(response, reverse('forum_core:thread', args=[self.thread.id]), fetch_redirect_response=False)

    def test_other_cannot_edit_thread(self):
        self.client.force_login(self.other_user)
        data = {'title': 'Hacked Title', 'content': 'Hacked content'}
        response = self.client.post(reverse('forum_core:edit_thread', args=[self.thread.id]), data)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, 'Initial Title')
        self.assertRedirects(response, reverse('forum_core:thread', args=[self.thread.id]), fetch_redirect_response=False)

    def test_moderator_can_edit_thread(self):
        self.client.force_login(self.moderator)
        data = {'title': 'Mod Edited', 'content': 'Mod Content'}
        response = self.client.post(reverse('forum_core:edit_thread', args=[self.thread.id]), data)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.title, 'Initial Title') # Should not change
        self.assertEqual(self.thread.content, 'Mod Content')

    def test_author_can_delete_thread(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse('forum_core:delete_thread', args=[self.thread.id]))
        self.assertFalse(Thread.objects.filter(id=self.thread.id).exists())
        self.assertRedirects(response, reverse('forum_core:home'), fetch_redirect_response=False)

    def test_other_cannot_delete_thread(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('forum_core:delete_thread', args=[self.thread.id]))
        self.assertTrue(Thread.objects.filter(id=self.thread.id).exists())

    def test_author_can_edit_comment(self):
        self.client.force_login(self.author)
        data = {'content': 'Updated comment content'}
        response = self.client.post(reverse('forum_core:edit_comment', args=[self.comment.id]), data)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Updated comment content')

    def test_other_cannot_edit_comment(self):
        self.client.force_login(self.other_user)
        data = {'content': 'Hacked comment'}
        self.client.post(reverse('forum_core:edit_comment', args=[self.comment.id]), data)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, 'Initial comment')

    def test_moderator_can_delete_comment(self):
        self.client.force_login(self.moderator)
        response = self.client.post(reverse('forum_core:delete_comment', args=[self.comment.id]))
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())
