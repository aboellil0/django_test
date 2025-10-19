from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "E-Commerce Admin"
admin.site.site_title = "E-Commerce Admin Portal"
admin.site.index_title = "Welcome to the E-Commerce Admin"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('ecommerce_project.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
