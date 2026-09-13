# prismata/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/',    admin.site.urls),
    path('matching/', include('matching.urls', namespace='matching')),
    # tambahkan app lain di bawah sini
]