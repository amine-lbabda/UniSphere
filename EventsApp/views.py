import typing

from django import forms
from django.db import transaction
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from UsersApp.models import Utilisateur

from .models import Evenements


class EventsForm(forms.ModelForm):
    class Meta:
        model = Evenements
        fields = ("title", "description", "start_date", "end_date", "type_evenement")
        widgets: typing.ClassVar = {
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }


class EventParticipantForm(forms.Form):
    participant = forms.ModelChoiceField(
        queryset=Utilisateur.objects.all(),
        label="Participant",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


EventParticipantFormSet = formset_factory(EventParticipantForm, extra=1)


class EventParticipantFormSetMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "participant_formset" not in context:
            data = self.request.POST if self.request.method == "POST" else None
            initial = []
            if self.object and self.object.pk:
                initial = [
                    {"participant": participant.pk}
                    for participant in self.object.participants.all()
                ]
            context["participant_formset"] = EventParticipantFormSet(
                data=data,
                initial=initial,
                prefix="participants",
            )
        return context

    def form_valid(self, form):
        participant_formset = EventParticipantFormSet(
            self.request.POST,
            prefix="participants",
        )
        if not participant_formset.is_valid():
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    participant_formset=participant_formset,
                )
            )

        with transaction.atomic():
            self.object = form.save()
            self.object.participants.set(
                participant_form.cleaned_data["participant"]
                for participant_form in participant_formset
                if participant_form.cleaned_data.get("participant")
            )

        return HttpResponseRedirect(self.get_success_url())


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
