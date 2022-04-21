from django.apps import AppConfig


class MastersConfig(AppConfig):
    name = 'masters'

    def ready(self):
        import masters.tasks
        import masters.signals
