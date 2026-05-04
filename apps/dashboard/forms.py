from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from apps.borrowing.models import Borrow
from apps.catalog.models import Author, Book, Category
from apps.orders.models import Invoice, Order, Payment
from apps.reservations.models import Reservation


class DashboardModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{css} dashboard-input'.strip()


class BookForm(DashboardModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'slug', 'isbn', 'author', 'category', 'description', 'price',
            'cover_image', 'publication_date', 'publisher', 'pages', 'language',
            'total_copies', 'available_copies', 'status',
        ]
        widgets = {
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'cover_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug') or slugify(self.cleaned_data.get('title', ''))
        if not slug:
            raise forms.ValidationError('Le slug est obligatoire.')
        queryset = Book.objects.filter(slug=slug)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('Ce slug est deja utilise.')
        return slug

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get('total_copies')
        available = cleaned.get('available_copies')
        if total is not None and available is not None and available > total:
            self.add_error('available_copies', 'Le stock disponible ne peut pas depasser le stock total.')
        return cleaned


class CategoryForm(DashboardModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class AuthorForm(DashboardModelForm):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name', 'biography', 'birth_date', 'nationality', 'website']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'biography': forms.Textarea(attrs={'rows': 4}),
        }


class StockUpdateForm(forms.Form):
    total_copies = forms.IntegerField(label='Stock total', min_value=0)
    available_copies = forms.IntegerField(label='Stock disponible', min_value=0)
    reason = forms.ChoiceField(label='Motif', choices=[
        ('manual', 'Ajustement manuel'),
        ('purchase', 'Approvisionnement'),
        ('correction', 'Correction'),
        ('loss', 'Perte'),
        ('return', 'Retour'),
    ])
    note = forms.CharField(label='Note', required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        self.book = kwargs.pop('book', None)
        super().__init__(*args, **kwargs)
        if self.book and not self.is_bound:
            self.initial.update({
                'total_copies': self.book.total_copies,
                'available_copies': self.book.available_copies,
            })
        for field in self.fields.values():
            field.widget.attrs['class'] = 'dashboard-input'

    def clean(self):
        cleaned = super().clean()
        total = cleaned.get('total_copies')
        available = cleaned.get('available_copies')
        if total is not None and available is not None and available > total:
            self.add_error('available_copies', 'Le stock disponible ne peut pas depasser le stock total.')
        return cleaned


class OrderStatusForm(DashboardModelForm):
    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'shipping_address', 'notes']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class PaymentForm(DashboardModelForm):
    class Meta:
        model = Payment
        fields = ['order', 'amount', 'payment_method', 'status', 'transaction_id', 'completed_at']
        widgets = {'completed_at': forms.DateTimeInput(attrs={'type': 'datetime-local'})}


class InvoiceForm(DashboardModelForm):
    class Meta:
        model = Invoice
        fields = ['order', 'invoice_number', 'billing_address', 'notes']
        widgets = {
            'billing_address': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class BorrowAdminForm(DashboardModelForm):
    class Meta:
        model = Borrow
        fields = ['user', 'book', 'due_date', 'status', 'fine_amount', 'fine_paid', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ReservationAdminForm(DashboardModelForm):
    class Meta:
        model = Reservation
        fields = ['user', 'book', 'expiration_date', 'pickup_date', 'status', 'queue_position', 'notes']
        widgets = {
            'expiration_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'pickup_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class UserAdminForm(DashboardModelForm):
    class Meta:
        model = get_user_model()
        fields = [
            'username', 'email', 'first_name', 'last_name', 'role',
            'is_active', 'is_staff', 'is_superuser', 'phone', 'address',
            'is_active_member',
        ]
        widgets = {'address': forms.Textarea(attrs={'rows': 3})}
