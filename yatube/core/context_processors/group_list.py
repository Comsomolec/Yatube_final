from posts.models import Group


def group_list(request):
    return {
        'group_list': Group.objects.all()
    }
