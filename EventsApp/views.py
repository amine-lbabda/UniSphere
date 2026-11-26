from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import *


class EventsCreateView(EventParticipantFormSetMixin, CreateView):
    model = Evenements
    form_class = EventsForm
    template_name = "Events/form.html"
    context_object_name = "event"
    success_url = reverse_lazy("events:liste")


class EventsViewList(ListView):
    model = Evenements
    template_name = "Events/list.html"
    context_object_name = "events"


class EventsUpdateView(EventParticipantFormSetMixin, UpdateView):
    model = Evenements
    form_class = EventsForm
    template_name = "Events/form.html"
    context_object_name = "event"
    success_url = reverse_lazy("events:liste")


class EventsDeleteView(DeleteView):
    model = Evenements
    template_name = "Events/confirm_delete.html"
    context_object_name = "event"
    success_url = reverse_lazy("events:liste")
