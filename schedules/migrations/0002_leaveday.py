from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaveDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Jour de congé')),
                ('reason', models.CharField(blank=True, max_length=200, verbose_name='Motif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leave_days', to='doctors.doctor')),
            ],
            options={
                'verbose_name': 'Jour de congé',
                'verbose_name_plural': 'Jours de congé',
                'ordering': ['date'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='leaveday',
            unique_together={('doctor', 'date')},
        ),
    ]