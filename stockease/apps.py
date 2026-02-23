from django.apps import AppConfig


class StockeaseConfig(AppConfig):
    name = 'stockease'

    def ready(self):
        import stockease.signals
