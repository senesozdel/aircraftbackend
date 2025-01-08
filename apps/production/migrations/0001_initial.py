# Generated by Django 4.2.17 on 2025-01-08 16:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Aircraft',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='AircraftPart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Part',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('stock', 'Stokta'), ('used', 'Kullanılmış')], default='stock', max_length=10)),
                ('is_deleted', models.BooleanField(default=False)),
                ('aircraft', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.aircraft')),
            ],
        ),
        migrations.CreateModel(
            name='PartType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('is_deleted', models.BooleanField(default=False)),
                ('responsible_part', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='production.parttype')),
            ],
        ),
        migrations.CreateModel(
            name='ProducedAircraft',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('aircraft', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.aircraft')),
                ('parts', models.ManyToManyField(through='production.AircraftPart', to='production.part')),
            ],
        ),
        migrations.CreateModel(
            name='Personnel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.team')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='part',
            name='part_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='production.parttype'),
        ),
        migrations.AddField(
            model_name='part',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.team'),
        ),
        migrations.AddField(
            model_name='aircraftpart',
            name='part',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.part'),
        ),
        migrations.AddField(
            model_name='aircraftpart',
            name='produced_aircraft',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.producedaircraft'),
        ),
        migrations.CreateModel(
            name='PartStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock_quantity', models.PositiveIntegerField(default=0)),
                ('is_deleted', models.BooleanField(default=False)),
                ('aircraft', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='production.aircraft')),
                ('part_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.parttype')),
            ],
            options={
                'unique_together': {('part_type', 'aircraft')},
            },
        ),
        migrations.CreateModel(
            name='AircraftPartRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('required_quantity', models.PositiveIntegerField()),
                ('aircraft', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.aircraft')),
                ('part_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='production.parttype')),
            ],
            options={
                'unique_together': {('aircraft', 'part_type')},
            },
        ),
    ]
