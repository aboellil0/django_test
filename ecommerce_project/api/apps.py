from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ecommerce_project.api'
    verbose_name = 'E-commerce API'
    
    def ready(self):
        import ecommerce_project.api.signals
