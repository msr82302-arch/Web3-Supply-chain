from django.apps import AppConfig

class CompaniesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.companies'

    def ready(self):
        """
        Initializes corporate profile moderation and validation gateway triggers on runtime boot.
        Handles: Company Approved onboarding statuses.
        """
        import apps.companies.signals 