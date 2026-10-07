from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from apps.accounts.models import User

class EmployeeIdOrUsernameBackend(ModelBackend):
    """
    Authenticates against either username or employee_id case-insensitively,
    supporting seamless login for newly appointed hospital administrators and clinical staff.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        clean_user = username.strip()
        user = User.objects.filter(
            Q(username__iexact=clean_user) | Q(staff_profile__employee_id__iexact=clean_user)
        ).first()
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
