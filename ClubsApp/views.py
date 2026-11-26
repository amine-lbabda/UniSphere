from django import forms
from django.db import transaction
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from UsersApp.models import Utilisateur

from .models import Clubs, ClubsMembersBoard


class ClubForm(forms.ModelForm):
    class Meta:
        model = Clubs
        fields = ("name", "description", "Active")


class BoardMemberForm(forms.ModelForm):
    member = forms.ModelChoiceField(
        queryset=Utilisateur.objects.all(),
        label="Member",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    board_role = forms.CharField(
        label="Poste",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = ClubsMembersBoard
        fields = ("member", "board_role")


ClubBoardFormSet = inlineformset_factory(
    Clubs,
    ClubsMembersBoard,
    form=BoardMemberForm,
    extra=1,
    can_delete=True,
)


class ClubBoardFormSetMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "board_formset" not in context:
            data = self.request.POST if self.request.method == "POST" else None
            context["board_formset"] = ClubBoardFormSet(
                data=data,
                instance=self.object or Clubs(),
            )
        return context

    def form_valid(self, form):
        board_formset = ClubBoardFormSet(
            self.request.POST,
            instance=form.instance,
        )
        if not board_formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, board_formset=board_formset)
            )

        with transaction.atomic():
            self.object = form.save()
            board_formset.instance = self.object
            board_formset.save()

        return HttpResponseRedirect(self.get_success_url())


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
