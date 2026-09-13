# matching/urls.py
from django.urls import path
from . import views

app_name = 'matching'

urlpatterns = [
    # Skill Matching & Smart Grading
    path('',         views.skill_matching_view, name='matching'),
    path('grading/', views.smart_grading_view,  name='grading'),
    path('history/', views.history_view,         name='history'),
    path('sjt/',                views.sjt_kerjakan_view,  name='sjt_kerjakan'),
    path('sjt/hasil/<int:pk>/', views.sjt_hasil_view,     name='sjt_hasil'),
    path('sjt/soal/tambah/',    views.sjt_soal_form_view, name='sjt_soal_form'),
]