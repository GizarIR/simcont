from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        UserModel = get_user_model()
        try:
            email = kwargs.get('email', None)
            if email is None:
                email = kwargs.get('username', None)
            user = UserModel.objects.get(email=email)
            if user.check_password(kwargs.get('password', None)):
                return user
        except UserModel.DoesNotExist:
            return None
        return None

    # Added from https://proproprogs.ru/django4/django4-avtorizaciya-cherez-email-profayl-polzovatelya
    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None
