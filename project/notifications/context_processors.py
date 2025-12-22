def notification_context(request):
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(is_read=False)
        return {
            'unread_notifications_count': unread_notifications.count(),
            'recent_notifications': unread_notifications[:5]
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': []
    }
