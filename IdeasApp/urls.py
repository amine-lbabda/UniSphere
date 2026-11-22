from django.urls import path

from . import views

app_name = 'ideas'

urlpatterns = [
    path('', views.idea_list, name='idea_list'),
    path('create/', views.idea_create, name='idea_create'),
    path('<int:pk>/', views.idea_detail, name='idea_detail'),
    path('<int:pk>/edit/', views.idea_update, name='idea_update'),
    path('<int:pk>/delete/', views.idea_delete, name='idea_delete'),
    path('admin-panel/', views.admin_idea_list, name='admin_idea_list'),
    path('admin-panel/<int:pk>/status/<str:status>/', views.idea_set_status, name='idea_set_status'),
]