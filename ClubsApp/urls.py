from django.urls import path

from .views import ClubsCreateView, ClubsDeleteView, ClubsUpdateView, ClubsViewList

app_name = "clubs"

urlpatterns = [
    path("", ClubsViewList.as_view(), name="liste"),
    path("create/", ClubsCreateView.as_view(), name="create"),
    path("<int:pk>/update/", ClubsUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", ClubsDeleteView.as_view(), name="delete"),
]
