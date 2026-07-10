from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0002_alter_course_course_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='course_type',
            field=models.CharField(
                choices=[('free', 'رایگان'), ('paid', 'دوره')],
                default='free',
                max_length=10,
                verbose_name='نوع دوره',
            ),
        ),
    ]
