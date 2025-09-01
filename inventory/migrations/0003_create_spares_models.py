from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_part_unit_alter_inventorymovement_quantity_and_more'),
        ('fleet', '0008_alter_vehicle_vehicle_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpareCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True, verbose_name='Nombre de categoría')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activa')),
            ],
            options={
                'verbose_name': 'Categoría de repuesto',
                'verbose_name_plural': 'Categorías de repuestos',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='SpareItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='Nombre (genérico)')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('unit', models.CharField(blank=True, max_length=32, verbose_name='Unidad')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='items', to='inventory.sparecategory', verbose_name='Categoría')),
            ],
            options={
                'verbose_name': 'Ítem de repuesto',
                'verbose_name_plural': 'Ítems de repuesto',
                'ordering': ['category__name', 'name'],
                'unique_together': {('category', 'name')},
            },
        ),
        migrations.CreateModel(
            name='VehicleSpare',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand', models.CharField(blank=True, max_length=120, verbose_name='Marca')),
                ('part_number', models.CharField(blank=True, max_length=120, verbose_name='Referencia / Part number')),
                ('quantity', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Cantidad')),
                ('notes', models.TextField(blank=True, verbose_name='Notas')),
                ('last_replacement_date', models.DateField(blank=True, null=True, verbose_name='Último reemplazo')),
                ('next_replacement_km', models.PositiveIntegerField(blank=True, null=True, verbose_name='Próximo reemplazo (km)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creado')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Actualizado')),
                ('spare_item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vehicle_links', to='inventory.spareitem', verbose_name='Ítem')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spares', to='fleet.vehicle', verbose_name='Vehículo')),
            ],
            options={
                'verbose_name': 'Repuesto del vehículo',
                'verbose_name_plural': 'Repuestos del vehículo',
                'ordering': ['vehicle__plate', 'spare_item__category__name', 'spare_item__name'],
            },
        ),
    ]
