from django.apps import AppConfig


class LogCoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'log_core'

    def ready(self):
        from .services import initialize_log_data
        import sys

        # Avoid running during management commands that don't need the DB populated
        # or when the database is not yet ready (e.g. during migrations)
        if 'runserver' in sys.argv:
            try:
                initialize_log_data()
            except Exception:
                # Silently fail if DB is not ready; it will run again on next start
                pass
