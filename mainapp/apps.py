from django.apps import AppConfig
from django.db.models.signals import post_migrate

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainapp'

    def ready(self):
        from .views import create_default_developer_user
        post_migrate.connect(self.create_user_after_migrate, sender=self)

    def create_user_after_migrate(self, **kwargs):
        from .views import create_default_developer_user
        create_default_developer_user()
