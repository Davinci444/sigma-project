from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fleet", "0007_rename_vehicle_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vehicle",
            name="vehicle_type",
            field=models.CharField(
                "Tipo de Vehículo",
                max_length=10,
                choices=[
                    ("AUTOMOVIL", "Automóvil"),
                    ("MICROBUS", "Microbús"),
                    ("BUS", "Bus"),
                ],
                help_text="Seleccione el tipo de vehículo",
            ),
        ),
    ]
