from django.apps import AppConfig

class SystemSettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sys_setting'  # Updated to match folder name on disk
    verbose_name = 'System Settings Engine'
