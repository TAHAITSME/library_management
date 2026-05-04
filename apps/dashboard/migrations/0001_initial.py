# Generated manually for the BiblioNUM dashboard.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalog', '0002_wishlist_wishlistitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_total', models.PositiveIntegerField()),
                ('new_total', models.PositiveIntegerField()),
                ('previous_available', models.PositiveIntegerField()),
                ('new_available', models.PositiveIntegerField()),
                ('reason', models.CharField(choices=[('manual', 'Ajustement manuel'), ('purchase', 'Approvisionnement'), ('correction', 'Correction'), ('loss', 'Perte'), ('return', 'Retour')], default='manual', max_length=20)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_movements', to='catalog.book')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Mouvement de stock',
                'verbose_name_plural': 'Mouvements de stock',
                'ordering': ['-created_at'],
            },
        ),
    ]
