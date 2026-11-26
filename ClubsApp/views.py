from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import *


class ClubsViewList(ListView):
    model = Clubs
    template_name = "clubs/list.html"
    context_object_name = "clubs"


class ClubsCreateView(ClubBoardFormSetMixin, CreateView):
    model = Clubs
    template_name = "clubs/form.html"
    form_class = ClubForm
    success_url = reverse_lazy("clubs:liste")


class ClubsUpdateView(ClubBoardFormSetMixin, UpdateView):
    model = Clubs
    form_class = ClubForm
    template_name = "clubs/form.html"
    context_object_name = "club"
    success_url = reverse_lazy("clubs:liste")


class ClubsDeleteView(DeleteView):
    model = Clubs
    template_name = "clubs/confirm_delete.html"
    context_object_name = "club"
    success_url = reverse_lazy("clubs:liste")
