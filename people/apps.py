from django.apps import AppConfig

class PeopleConfig(AppConfig):
    name = 'people'
    verbose_name = ('people')
    def ready(self):
        import people.signals  # noqa
