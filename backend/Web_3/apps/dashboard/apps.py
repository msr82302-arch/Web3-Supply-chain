from django.apps import AppConfig

class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'  # Absolute path to prevent registry import collisions [18]
    verbose_name = 'Enterprise Operations Dashboard'