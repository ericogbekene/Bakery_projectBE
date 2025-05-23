# Generated by Django 5.1.4 on 2025-05-24 14:27

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_number', models.CharField(db_index=True, editable=False, max_length=20, unique=True)),
                ('first_name', models.CharField(db_index=True, max_length=100)),
                ('last_name', models.CharField(db_index=True, max_length=100)),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('address', models.CharField(max_length=250)),
                ('city', models.CharField(max_length=100)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('paid', models.BooleanField(db_index=True, default=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], db_index=True, default='pending', max_length=20)),
                ('total_cost', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ],
            options={
                'ordering': ['-created'],
                'indexes': [models.Index(fields=['-created'], name='orders_orde_created_743fca_idx'), models.Index(fields=['first_name', 'last_name'], name='orders_orde_first_n_00f073_idx'), models.Index(fields=['email', 'paid'], name='orders_orde_email_6ec9d5_idx'), models.Index(fields=['status'], name='orders_orde_status_c6dd84_idx'), models.Index(fields=['order_number'], name='orders_orde_order_n_f3ada5_idx')],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='products.product')),
            ],
            options={
                'indexes': [models.Index(fields=['order', 'product'], name='orders_orde_order_i_52f79a_idx')],
            },
        ),
    ]
