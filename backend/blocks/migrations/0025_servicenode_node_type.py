from django.db import migrations, models
from django.db.models import Q


def set_default_node_type(apps, schema_editor):
    ServiceNode = apps.get_model('blocks', 'ServiceNode')
    ServiceNode.objects.filter(service='user').update(node_type='user')
    ServiceNode.objects.filter(service='personal_wallet').update(node_type='wallet')
    exchange_prefixes = ['upbit', 'bithumb', 'binance', 'okx']
    exchange_q = Q()
    for prefix in exchange_prefixes:
        exchange_q |= Q(service__startswith=prefix)
    if exchange_q:
        ServiceNode.objects.filter(exchange_q).update(node_type='exchange')
    ServiceNode.objects.filter(node_type__isnull=True).update(node_type='service')


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0024_kingstone_pin_encrypted'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicenode',
            name='node_type',
            field=models.CharField(choices=[('user', '사용자'), ('exchange', '거래소'), ('service', '서비스'), ('wallet', '지갑')], default='service', max_length=20),
        ),
        migrations.RunPython(set_default_node_type, migrations.RunPython.noop),
    ]
