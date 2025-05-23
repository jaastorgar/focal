# Generated by Django 5.1.4 on 2025-05-20 03:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0002_almacenero'),
    ]

    operations = [
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_almacen', models.CharField(max_length=100)),
                ('rut', models.CharField(max_length=12, unique=True)),
                ('direccion_tributaria', models.CharField(blank=True, max_length=255)),
                ('comuna', models.CharField(blank=True, max_length=100)),
                ('run_representante', models.CharField(max_length=12)),
                ('inicio_actividades', models.DateField()),
                ('nivel_venta_uf', models.CharField(blank=True, max_length=100)),
                ('giro_negocio', models.CharField(max_length=100)),
                ('tipo_sociedad', models.CharField(max_length=100)),
            ],
        ),
        migrations.RenameField(
            model_name='almacenero',
            old_name='rut',
            new_name='run',
        ),
        migrations.AddField(
            model_name='almacenero',
            name='empresa',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventario.empresa'),
        ),
    ]
