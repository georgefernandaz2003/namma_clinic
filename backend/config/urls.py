from django.contrib import admin
from django.urls import path, include
from config.health import healthz, readyz

urlpatterns = [
    path('healthz', healthz, name='healthz'),
    path('healthz/', healthz),
    path('readyz', readyz, name='readyz'),
    path('readyz/', readyz),
    path('admin/', admin.site.urls),
    path('api/v1/', include('config.api_v1_urls')),
    path('api/', include('config.api_urls')),
]
