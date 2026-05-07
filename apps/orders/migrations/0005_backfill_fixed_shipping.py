from decimal import Decimal

from django.db import migrations


def apply_fixed_shipping(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    for order in Order.objects.all():
        order.shipping_cost = Decimal('10.00')
        order.tax = Decimal('0.00')
        order.total = order.subtotal + order.shipping_cost - order.discount
        if order.total < 0:
            order.total = Decimal('0.00')
        order.save(update_fields=['shipping_cost', 'tax', 'total'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_alter_order_status'),
    ]

    operations = [
        migrations.RunPython(apply_fixed_shipping, migrations.RunPython.noop),
    ]
