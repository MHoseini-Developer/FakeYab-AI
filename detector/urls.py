from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("analyze/", views.analyze, name="analyze"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("api/analyze/", views.analyze_api, name="analyze_api"),
]