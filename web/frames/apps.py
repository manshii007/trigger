from django.apps import AppConfig


class FramesConfig(AppConfig):
    name = 'frames'

    def ready(self):
        import frames.signals
        import frames.tasks