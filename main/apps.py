from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'main'
    verbose_name = ('main')
    def ready(self):
        import main.signals  # noqa
