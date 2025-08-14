from django.urls import path
from . import views
from . import api


urlpatterns = [
    path('', views.index, name='index'),
    path('generate/', views.generate_story, name='generate_story'),
    path('api/generate/', api.generate_api, name='api_generate'),
]


