from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import IdeaForm
from .models import Idea


def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
def idea_list(request):
    """2.2 Consulter mes idées."""
    ideas = Idea.objects.filter(author=request.user)
    return render(request, 'IdeasApp/idea_list.html', {'ideas': ideas})


@login_required
def idea_detail(request, pk):
    idea = get_object_or_404(Idea, pk=pk, author=request.user)
    return render(request, 'IdeasApp/idea_detail.html', {'idea': idea})


@login_required
def idea_create(request):
    """2.1 Soumettre une suggestion ou une réclamation."""
    if request.method == 'POST':
        form = IdeaForm(request.POST)
        if form.is_valid():
            idea = form.save(commit=False)
            idea.author = request.user
            idea.save()
            messages.success(request, "Votre idée a été soumise avec succès.")
            return redirect('ideas:idea_list')
    else:
        form = IdeaForm()
    return render(request, 'IdeasApp/idea_form.html', {'form': form, 'title': 'Soumettre une idée'})


@login_required
def idea_update(request, pk):
    """2.3 Modifier mes idées."""
    idea = get_object_or_404(Idea, pk=pk, author=request.user)
    if request.method == 'POST':
        form = IdeaForm(request.POST, instance=idea)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre idée a été modifiée.")
            return redirect('ideas:idea_list')
    else:
        form = IdeaForm(instance=idea)
    return render(request, 'IdeasApp/idea_form.html', {'form': form, 'title': 'Modifier mon idée'})


@login_required
def idea_delete(request, pk):
    """2.4 Supprimer mes idées."""
    idea = get_object_or_404(Idea, pk=pk, author=request.user)
    if request.method == 'POST':
        idea.delete()
        messages.success(request, "Votre idée a été supprimée.")
        return redirect('ideas:idea_list')
    return render(request, 'IdeasApp/idea_confirm_delete.html', {'idea': idea})


# ---------- Administrateur (2.9, 2.10) ----------

@user_passes_test(is_admin)
def admin_idea_list(request):
    """2.9 Consulter toutes les idées + 2.10 filtres simples."""
    ideas = Idea.objects.select_related('author')
    idea_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    if idea_type:
        ideas = ideas.filter(type=idea_type)
    if status:
        ideas = ideas.filter(status=status)
    context = {
        'ideas': ideas,
        'type_choices': Idea.TYPE_CHOICES,
        'status_choices': Idea.STATUS_CHOICES,
        'selected_type': idea_type,
        'selected_status': status,
    }
    return render(request, 'IdeasApp/admin_idea_list.html', context)

from django.views.decorators.http import require_POST

@user_passes_test(is_admin)
@require_POST
def idea_set_status(request, pk, status):
    """2.11 / 2.12 / 2.13 : changer le statut d'une idée."""
    if status not in dict(Idea.STATUS_CHOICES):
        messages.error(request, "Statut invalide.")
        return redirect('ideas:admin_idea_list')
    idea = get_object_or_404(Idea, pk=pk)
    idea.status = status
    idea.save()
    messages.success(request, f"Statut de « {idea.title} » mis à jour : {idea.get_status_display()}.")
    return redirect('ideas:admin_idea_list')