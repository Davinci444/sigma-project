

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
                choices=[
                    ("AUTOMOVIL", "Automóvil"),
                    ("MICROBUS", "Microbús"),

                verbose_name="Tipo de Vehículo",
            ),
        ),
    ]
