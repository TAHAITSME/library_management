from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.views.generic import TemplateView

from apps.borrowing.models import Borrow
from apps.catalog.models import Author, Book, Category
from apps.orders.models import Order
from apps.reservations.models import Reservation


def format_metric(value):
    if value >= 1000:
        rounded = value / 1000
        return f"{rounded:.1f}K".replace(".0K", "K")
    return str(value)


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stock = Book.objects.aggregate(
            available=Sum("available_copies"),
            total=Sum("total_copies"),
        )
        available_copies = stock["available"] or 0
        total_copies = stock["total"] or 0
        stock_rate = round(min((available_copies / total_copies) * 100, 100)) if total_copies else 0

        featured_books = list(
            Book.objects.select_related("author", "category")
            .filter(status="available")
            .order_by("-rating", "-created_at")[:6]
        )

        context.update(
            {
                "home_stats": {
                    "books": format_metric(Book.objects.count()),
                    "authors": format_metric(Author.objects.count()),
                    "categories": format_metric(Category.objects.count()),
                    "readers": format_metric(get_user_model().objects.count()),
                    "borrows": format_metric(Borrow.objects.count()),
                    "orders": format_metric(Order.objects.count()),
                    "reservations": format_metric(Reservation.objects.count()),
                    "available_copies": format_metric(available_copies),
                    "stock_rate": f"{stock_rate}%",
                },
                "featured_books": featured_books,
                "active_borrows": Borrow.objects.filter(status="active").count(),
                "pending_orders": Order.objects.filter(status__in=["pending", "processing"]).count(),
                "active_reservations": Reservation.objects.filter(status="active").count(),
            }
        )
        return context
