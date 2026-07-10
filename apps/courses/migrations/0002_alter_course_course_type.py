from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='course_type',
            field=models.CharField(
                choices=[('free', 'رایگان'), ('paid', 'اختصاصی')],
                default='free',
                max_length=10,
                verbose_name='نوع دوره',
            ),
        ),
    ]
