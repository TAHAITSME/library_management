import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from apps.borrowing.models import Borrow
from apps.catalog.models import Author, Book, Category
from apps.orders.models import Invoice, Order, OrderItem, Payment
from apps.reservations.models import Reservation

from .forms import (
    AuthorForm,
    BookForm,
    BorrowAdminForm,
    CategoryForm,
    InvoiceForm,
    OrderStatusForm,
    PaymentForm,
    ReservationAdminForm,
    StockUpdateForm,
    UserAdminForm,
)
from .models import StockMovement


class StaffRequiredMixin(UserPassesTestMixin):
    login_url = reverse_lazy('accounts:login')

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class DashboardContextMixin:
    section = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dashboard_section'] = self.section
        return context


def _monthly_totals(queryset, date_field, amount_field=None):
    monthly_data = {}
    fields = [date_field]
    if amount_field:
        fields.append(amount_field)

    for row in queryset.order_by(date_field).values(*fields):
        date_value = row.get(date_field)
        if not date_value:
            continue
        if timezone.is_aware(date_value):
            date_value = timezone.localtime(date_value)
        key = date_value.strftime('%Y-%m')
        label = date_value.strftime('%b %Y')
        value = row.get(amount_field) if amount_field else 1

        if key not in monthly_data:
            monthly_data[key] = {'label': label, 'value': 0}
        monthly_data[key]['value'] += float(value or 0)

    return [monthly_data[key] for key in sorted(monthly_data)]


class DashboardHomeView(StaffRequiredMixin, DashboardContextMixin, TemplateView):
    template_name = 'dashboard/index.html'
    section = 'home'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        twelve_months_ago = month_start - timedelta(days=365)
        paid_orders = Order.objects.filter(payment_status='paid')
        stripe_payments = Payment.objects.filter(payment_method='stripe', status='completed')

        context.update({
            'total_users': get_user_model().objects.count(),
            'total_books': Book.objects.count(),
            'total_orders': Order.objects.count(),
            'total_payments': Payment.objects.count(),
            'stripe_payments_count': stripe_payments.count(),
            'stripe_revenue': stripe_payments.aggregate(total=Sum('amount'))['total'] or 0,
            'failed_payments': Payment.objects.filter(status='failed').count(),
            'pending_payments': Payment.objects.filter(status='pending').count(),
            'total_invoices': Invoice.objects.count(),
            'total_borrows': Borrow.objects.count(),
            'total_reservations': Reservation.objects.count(),
            'total_revenue': paid_orders.aggregate(total=Sum('total'))['total'] or 0,
            'month_revenue': paid_orders.filter(created_at__gte=month_start).aggregate(total=Sum('total'))['total'] or 0,
            'books_sold': OrderItem.objects.filter(order__payment_status='paid').aggregate(total=Sum('quantity'))['total'] or 0,
            'books_borrowed': Borrow.objects.count(),
            'stock_total': Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0,
            'low_stock': Book.objects.filter(available_copies__lte=2).count(),
            'recent_orders': Order.objects.select_related('user').order_by('-created_at')[:6],
            'recent_payments': Payment.objects.select_related('order', 'order__user').order_by('-created_at')[:6],
            'recent_users': get_user_model().objects.order_by('-date_joined')[:6],
            'orders_by_month': json.dumps(_monthly_totals(Order.objects.filter(created_at__gte=twelve_months_ago), 'created_at')),
            'revenue_by_month': json.dumps(_monthly_totals(paid_orders.filter(created_at__gte=twelve_months_ago), 'created_at', 'total')),
            'top_books': json.dumps([
                {'label': row['book__title'], 'value': row['sold'] or 0}
                for row in OrderItem.objects.filter(order__payment_status='paid')
                .values('book__title').annotate(sold=Sum('quantity')).order_by('-sold')[:8]
            ]),
        })
        return context


class BookListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Book
    template_name = 'dashboard/books/list.html'
    context_object_name = 'books'
    paginate_by = 15
    section = 'books'

    def get_queryset(self):
        queryset = Book.objects.select_related('author', 'category').order_by('-created_at')
        query = self.request.GET.get('q')
        category = self.request.GET.get('category')
        if query:
            queryset = queryset.filter(title__icontains=query) | queryset.filter(isbn__icontains=query)
        if category and category.isdigit():
            queryset = queryset.filter(category_id=category)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


class BookCreateView(StaffRequiredMixin, DashboardContextMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'dashboard/form.html'
    success_url = reverse_lazy('dashboard:books')
    section = 'books'
    extra_title = 'Ajouter un livre'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.extra_title
        return context


class BookUpdateView(BookCreateView, UpdateView):
    extra_title = 'Modifier le livre'


class BookDeleteView(StaffRequiredMixin, DashboardContextMixin, DeleteView):
    model = Book
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:books')
    section = 'books'


class CategoryListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Category
    template_name = 'dashboard/categories/list.html'
    context_object_name = 'categories'
    section = 'categories'


class CategoryCreateView(StaffRequiredMixin, DashboardContextMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/form.html'
    success_url = reverse_lazy('dashboard:categories')
    section = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Categorie'
        return context


class CategoryUpdateView(CategoryCreateView, UpdateView):
    pass


class CategoryDeleteView(StaffRequiredMixin, DashboardContextMixin, DeleteView):
    model = Category
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:categories')
    section = 'categories'


class AuthorListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Author
    template_name = 'dashboard/authors/list.html'
    context_object_name = 'authors'
    section = 'authors'


class AuthorCreateView(StaffRequiredMixin, DashboardContextMixin, CreateView):
    model = Author
    form_class = AuthorForm
    template_name = 'dashboard/form.html'
    success_url = reverse_lazy('dashboard:authors')
    section = 'authors'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Auteur'
        return context


class AuthorUpdateView(AuthorCreateView, UpdateView):
    pass


class AuthorDeleteView(StaffRequiredMixin, DashboardContextMixin, DeleteView):
    model = Author
    template_name = 'dashboard/confirm_delete.html'
    success_url = reverse_lazy('dashboard:authors')
    section = 'authors'


class StockListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Book
    template_name = 'dashboard/stock/list.html'
    context_object_name = 'books'
    paginate_by = 20
    section = 'stock'

    def get_queryset(self):
        queryset = Book.objects.select_related('author', 'category').order_by('available_copies', 'title')
        if self.request.GET.get('low') == '1':
            queryset = queryset.filter(available_copies__lte=2)
        return queryset


class StockUpdateView(StaffRequiredMixin, DashboardContextMixin, UpdateView):
    model = Book
    form_class = StockUpdateForm
    template_name = 'dashboard/stock/form.html'
    success_url = reverse_lazy('dashboard:stock')
    section = 'stock'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['book'] = self.object
        return kwargs

    def form_valid(self, form):
        book = self.object
        with transaction.atomic():
            StockMovement.objects.create(
                book=book,
                previous_total=book.total_copies,
                new_total=form.cleaned_data['total_copies'],
                previous_available=book.available_copies,
                new_available=form.cleaned_data['available_copies'],
                reason=form.cleaned_data['reason'],
                note=form.cleaned_data['note'],
                created_by=self.request.user,
            )
            book.total_copies = form.cleaned_data['total_copies']
            book.available_copies = form.cleaned_data['available_copies']
            book.status = 'available' if book.available_copies > 0 else 'unavailable'
            book.save(update_fields=['total_copies', 'available_copies', 'status', 'updated_at'])
        messages.success(self.request, 'Stock mis a jour.')
        return redirect(self.success_url)


class OrderListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Order
    template_name = 'dashboard/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    section = 'orders'

    def get_queryset(self):
        queryset = Order.objects.select_related('user').prefetch_related('items__book').order_by('-created_at')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class OrderDetailView(StaffRequiredMixin, DashboardContextMixin, DetailView):
    model = Order
    template_name = 'dashboard/orders/detail.html'
    context_object_name = 'order'
    section = 'orders'

    def get_queryset(self):
        return Order.objects.select_related('user').prefetch_related('items__book')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice'] = Invoice.objects.filter(order=self.object).first()
        return context


class OrderUpdateView(StaffRequiredMixin, DashboardContextMixin, UpdateView):
    model = Order
    form_class = OrderStatusForm
    template_name = 'dashboard/form.html'
    section = 'orders'

    def get_success_url(self):
        return reverse_lazy('dashboard:order_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Mettre a jour la commande'
        return context


class PaymentListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Payment
    template_name = 'dashboard/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 20
    section = 'payments'

    def get_queryset(self):
        queryset = Payment.objects.select_related('order', 'order__user').order_by('-created_at')
        status = self.request.GET.get('status')
        user = self.request.GET.get('user')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if status:
            queryset = queryset.filter(status=status)
        if user:
            queryset = queryset.filter(order__user__username__icontains=user)
        parsed_date_from = parse_date(date_from) if date_from else None
        parsed_date_to = parse_date(date_to) if date_to else None
        if parsed_date_from:
            queryset = queryset.filter(created_at__date__gte=parsed_date_from)
        if parsed_date_to:
            queryset = queryset.filter(created_at__date__lte=parsed_date_to)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context.update({
            'stripe_total': queryset.filter(payment_method='stripe').count(),
            'stripe_revenue': queryset.filter(payment_method='stripe', status='completed').aggregate(total=Sum('amount'))['total'] or 0,
            'completed_count': queryset.filter(status='completed').count(),
            'failed_count': queryset.filter(status='failed').count(),
            'pending_count': queryset.filter(status='pending').count(),
        })
        return context


class PaymentUpdateView(StaffRequiredMixin, DashboardContextMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'dashboard/form.html'
    success_url = reverse_lazy('dashboard:payments')
    section = 'payments'


class InvoiceListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Invoice
    template_name = 'dashboard/invoices/list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    section = 'invoices'

    def get_queryset(self):
        return Invoice.objects.select_related('order', 'order__user').order_by('-created_at')


class InvoiceDetailView(StaffRequiredMixin, DashboardContextMixin, DetailView):
    model = Invoice
    template_name = 'dashboard/invoices/detail.html'
    context_object_name = 'invoice'
    section = 'invoices'

    def get_queryset(self):
        return Invoice.objects.select_related('order', 'order__user').prefetch_related('order__items__book')


class InvoiceCreateView(StaffRequiredMixin, DashboardContextMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'dashboard/form.html'
    success_url = reverse_lazy('dashboard:invoices')
    section = 'invoices'


@require_POST
def generate_invoice(request, order_pk):
    user = request.user
    if not user.is_authenticated or not (user.is_staff or user.is_superuser):
        raise PermissionDenied
    order = get_object_or_404(Order, pk=order_pk)
    invoice, created = Invoice.objects.get_or_create(
        order=order,
        defaults={
            'invoice_number': Invoice().generate_invoice_number(),
            'billing_address': order.shipping_address,
        },
    )
    messages.success(request, 'Facture generee.' if created else 'La facture existe deja.')
    return redirect('dashboard:invoice_detail', pk=invoice.pk)


class BorrowListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Borrow
    template_name = 'dashboard/borrows/list.html'
    context_object_name = 'borrows'
    paginate_by = 20
    section = 'borrows'

    def get_queryset(self):
        queryset = Borrow.objects.select_related('user', 'book').order_by('-borrow_date')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class BorrowUpdateView(StaffRequiredMixin, DashboardContextMixin, UpdateView):
    model = Borrow
    form_class = BorrowAdminForm
    template_name = 'dashboard/form.html'
    success_url = reverse_lazy('dashboard:borrows')
    section = 'borrows'


@require_POST
def mark_borrow_returned(request, pk):
    user = request.user
    if not user.is_authenticated or not (user.is_staff or user.is_superuser):
        raise PermissionDenied
    borrow = get_object_or_404(Borrow.objects.select_related('book'), pk=pk)
    if borrow.status != 'returned':
        with transaction.atomic():
            borrow.return_date = timezone.now()
            borrow.status = 'returned'
            borrow.calculate_fine()
            borrow.save()
            borrow.book.available_copies += 1
            borrow.book.save(update_fields=['available_copies', 'updated_at'])
        messages.success(request, 'Livre marque comme retourne.')
    return redirect('dashboard:borrows')


class ReservationListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = Reservation
    template_name = 'dashboard/reservations/list.html'
    context_object_name = 'reservations'
    paginate_by = 20
    section = 'reservations'

    def get_queryset(self):
        queryset = Reservation.objects.select_related('user', 'book').order_by('-reservation_date')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class ReservationUpdateView(StaffRequiredMixin, DashboardContextMixin, UpdateView):
    model = Reservation
    form_class = ReservationAdminForm
    template_name = 'dashboard/form.html'
    success_url = reverse_lazy('dashboard:reservations')
    section = 'reservations'


@require_POST
def reservation_action(request, pk, action):
    user = request.user
    if not user.is_authenticated or not (user.is_staff or user.is_superuser):
        raise PermissionDenied
    reservation = get_object_or_404(Reservation, pk=pk)
    if action == 'complete':
        reservation.status = 'completed'
        reservation.pickup_date = timezone.now()
    elif action == 'cancel':
        reservation.status = 'cancelled'
    else:
        raise PermissionDenied
    reservation.save()
    messages.success(request, 'Reservation mise a jour.')
    return redirect('dashboard:reservations')


class UserListView(StaffRequiredMixin, DashboardContextMixin, ListView):
    model = get_user_model()
    template_name = 'dashboard/users/list.html'
    context_object_name = 'users_list'
    paginate_by = 20
    section = 'users'

    def get_queryset(self):
        queryset = get_user_model().objects.order_by('-date_joined')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(username__icontains=query) | queryset.filter(email__icontains=query)
        return queryset.distinct()


class UserDetailView(StaffRequiredMixin, DashboardContextMixin, DetailView):
    model = get_user_model()
    template_name = 'dashboard/users/detail.html'
    context_object_name = 'managed_user'
    section = 'users'


class UserUpdateView(StaffRequiredMixin, DashboardContextMixin, UpdateView):
    model = get_user_model()
    form_class = UserAdminForm
    template_name = 'dashboard/form.html'
    success_url = reverse_lazy('dashboard:users')
    section = 'users'

    def form_valid(self, form):
        if self.object == self.request.user and not form.cleaned_data.get('is_active'):
            form.add_error('is_active', 'Vous ne pouvez pas desactiver votre propre compte.')
            return self.form_invalid(form)
        return super().form_valid(form)
