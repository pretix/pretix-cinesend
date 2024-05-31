# Generated by Django 3.0.12 on 2021-02-10 08:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pretixbase", "0175_orderrefund_comment"),
        ("pretix_cinesend", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubEventProduct",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False
                    ),
                ),
                ("asset_id", models.CharField(max_length=200)),
                (
                    "subevent",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cinesend_product",
                        to="pretixbase.SubEvent",
                    ),
                ),
            ],
        ),
    ]
