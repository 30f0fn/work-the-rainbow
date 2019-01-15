from django.apps import AppConfig

class PeopleConfig(AppConfig):
    name = 'worktime.people'
    verbose_name = ('people')
    def ready(self):
        import worktime.people.signals  # noqa


