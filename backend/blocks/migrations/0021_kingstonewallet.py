from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0020_sidebarconfig_wallet_password_plain'),
    ]

    operations = [
        migrations.CreateModel(
            name='KingstoneWallet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=64)),
                ('pin_hash', models.CharField(max_length=256)),
                ('wallet_id', models.CharField(max_length=64, unique=True)),
                ('wallet_name', models.CharField(max_length=64)),
                ('index', models.PositiveSmallIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'unique_together': {('username', 'index')},
            },
        ),
        migrations.AddIndex(
            model_name='kingstonewallet',
            index=models.Index(fields=['username'], name='blocks_kingstone_username_idx'),
        ),
    ]

