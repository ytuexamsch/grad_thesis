from django.urls import path
from .views import *
urlpatterns = [
    path('', home),
    path('upload', upload),
    path('describe', describe),
    path('schedule', schedule),
    path('schedule_2', schedule_2),
    path('schedule_3', schedule_3),
]
