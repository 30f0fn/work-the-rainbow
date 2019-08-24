from django.apps import AppConfig


class MainConfig(AppConfig):
    name = 'main'
    verbose_name = ('main')
    def ready(self):
        print("called ready()")
        import worktime.main.signals  # noqa
