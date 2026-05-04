from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.urls import reverse_lazy

from .models import Profile
from .forms import CustomUserCreationForm, ProfileForm, CustomAuthenticationForm

from apps.borrowing.models import Borrow
from apps.orders.models import Order, Payment
from apps.reservations.models import Reservation
from apps.catalog.models import Review, Book, Author, Category


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user

        if user.is_staff or user.is_superuser:
            return reverse_lazy('dashboard:index')

        return reverse_lazy('accounts:account')


def register_view(request):
    """Inscription utilisateur"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('dashboard:index')
        return redirect('accounts:account')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            messages.success(request, 'Compte créé avec succès.')
            login(request, user)

            if user.is_staff or user.is_superuser:
                return redirect('dashboard:index')
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def account_view(request):
    """Dashboard utilisateur"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard:index')

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
    """Profil utilisateur"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard:index')

    profile, _ = Profile.objects.get_or_create(user=request.user)

    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    """Édition du profil utilisateur"""
    if request.user.is_staff or request.user.is_superuser:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    context = {
        'form': form,
        'profile': Profile.objects.get_or_create(user=request.user)[0],
    }
    return render(request, 'accounts/profile_edit.html', context)


@staff_member_required(login_url=reverse_lazy('accounts:login'))
def admin_dashboard_view(request):
    """Dashboard admin BiblioNUM"""
    total_books = Book.objects.count()
    total_authors = Author.objects.count()
    total_categories = Category.objects.count()

    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    paid_orders = Order.objects.filter(payment_status='paid').count()

    total_reservations = Reservation.objects.count()
    active_reservations = Reservation.objects.filter(status='active').count()

    total_borrows = Borrow.objects.count()
    active_borrows = Borrow.objects.filter(status='active').count()
    overdue_borrows = Borrow.objects.filter(is_overdue=True).count()

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('order', 'order__user').order_by('-created_at')[:5]
    recent_reservations = Reservation.objects.select_related('user', 'book').order_by('-reservation_date')[:5]
    recent_borrows = Borrow.objects.select_related('user', 'book').order_by('-borrow_date')[:5]

    context = {
        'total_books': total_books,
        'total_authors': total_authors,
        'total_categories': total_categories,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'paid_orders': paid_orders,
        'total_reservations': total_reservations,
        'active_reservations': active_reservations,
        'total_borrows': total_borrows,
        'active_borrows': active_borrows,
        'overdue_borrows': overdue_borrows,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'recent_reservations': recent_reservations,
        'recent_borrows': recent_borrows,
    }
    return render(request, 'admin/dashboard.html', context)


@staff_member_required(login_url=reverse_lazy('accounts:login'))
def admin_users_list_view(request):
    """Liste admin des utilisateurs"""
    User = get_user_model()
    users = User.objects.all().order_by('-date_joined')

    context = {
        'users': users,
    }
    return render(request, 'accounts/admin_users_list.html', context)
