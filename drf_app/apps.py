from django.apps import AppConfig


class Drf_appConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'drf_app'

    def ready(self):
        from . import signals  # turn on signals
