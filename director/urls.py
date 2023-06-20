from django.conf.urls import url,include
from django.contrib import admin
from director import views

urlpatterns = [
    url(r'^login/', views.login),

    url(r'^home/$', views.home),
    url(r'^manage/$', views.manage),
    url(r'^check/$', views.check),
    url(r'^history/$', views.history),
    url(r'^person/$', views.person),

    url(r'^logout/$', views.logout),           #注销
]

