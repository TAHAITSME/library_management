from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Sum

from .models import Profile
from .forms import CustomUserCreationForm, ProfileForm

from apps.borrowing.models import Borrow
from apps.orders.models import Order
from apps.reservations.models import Reservation
from apps.catalog.models import Review


def register_view(request):
    """Vue d'enregistrement d'un nouvel utilisateur"""
    if request.user.is_authenticated:
        return redirect('accounts:account')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            messages.success(request, 'Compte créé avec succès!')
            login(request, user)
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def account_view(request):
    """Dashboard utilisateur complet avec statistiques"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user = request.user

    active_borrows = Borrow.objects.filter(user=user, status='active').count()
    total_borrows = Borrow.objects.filter(user=user).count()
    overdue_borrows = Borrow.objects.filter(user=user, is_overdue=True, status='active').count()

    total_orders = Order.objects.filter(user=user).count()
    pending_orders = Order.objects.filter(user=user, status='pending').count()
    delivered_orders = Order.objects.filter(user=user, status='delivered').count()

    active_reservations = Reservation.objects.filter(user=user, status='active').count()
    user_reviews = Review.objects.filter(user=user).count()

    total_spent = (
        Order.objects.filter(user=user, payment_status='paid')
        .aggregate(Sum('total'))['total__sum'] or 0
    )

    recent_borrows = Borrow.objects.filter(user=user).order_by('-borrow_date')[:5]
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]

    context = {
        'profile': profile,
        'user': user,
        'active_borrows': active_borrows,
        'total_borrows': total_borrows,
        'overdue_borrows': overdue_borrows,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'active_reservations': active_reservations,
        'user_reviews': user_reviews,
        'total_spent': total_spent,
        'recent_borrows': recent_borrows,
        'recent_orders': recent_orders,
    }
    return render(request, 'accounts/account.html', context)


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    """Vue d'édition du profil utilisateur"""
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès!')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'accounts/profile_edit.html', context)