from django.db.models import Q

def unread_messages_count(request):
    if request.user.is_authenticated:
        unread_count = request.user.received_messages.filter(is_read=False).count()
    else:
        unread_count = 0
    return {'unread_messages_count': unread_count}
