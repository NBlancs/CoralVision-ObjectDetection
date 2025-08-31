from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('video_feed', views.video_feed, name='video_feed'),
    # control APIs
    path('api/use_webcam', views.api_use_webcam, name='api_use_webcam'),
    path('api/use_video', views.api_use_video, name='api_use_video'),
    path('api/use_camera', views.api_use_camera, name='api_use_camera'),
    path('api/start_recording', views.api_start_recording, name='api_start_recording'),
    path('api/stop_recording', views.api_stop_recording, name='api_stop_recording'),
]
