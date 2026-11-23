from django.urls import path

from .views import *

app_name = "events"
urlpatterns = [
    path("create/", EventsCreateView.as_view(), name="create"),
    path("", EventsViewList.as_view(), name="liste"),
    path("update/<int:pk>", EventsUpdateView.as_view(), name="update"),
    path("delete/<int:pk>", EventsDeleteView.as_view(), name="delete"),
]
