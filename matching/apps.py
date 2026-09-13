# matching/apps.py
from django.apps import AppConfig


class MatchingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matching'

    def ready(self):
        """
        Dipanggil Django saat server startup.
        Load model SBERT ke memori supaya request pertama tidak lambat.
        """
        # Import di sini (bukan di atas) untuk hindari circular import
        from . import ml_model
        ml_model.load()