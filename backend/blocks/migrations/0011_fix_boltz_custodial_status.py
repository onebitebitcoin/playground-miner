# Generated migration to fix Boltz custodial status

from django.db import migrations


def fix_boltz_custodial_status(apps, schema_editor):
    """Set Boltz as non-custodial service"""
    LightningService = apps.get_model('blocks', 'LightningService')
    try:
        boltz = LightningService.objects.get(service='boltz')
        boltz.is_custodial = False
        boltz.description = 'Boltz 교환 수수료 (non-KYC, 비수탁형)'
        boltz.save()
    except LightningService.DoesNotExist:
        pass  # Boltz record doesn't exist yet


def reverse_boltz_custodial_status(apps, schema_editor):
    """Revert Boltz back to custodial (for rollback)"""
    LightningService = apps.get_model('blocks', 'LightningService')
    try:
        boltz = LightningService.objects.get(service='boltz')
        boltz.is_custodial = True
        boltz.description = 'Boltz 교환 수수료 (non-KYC)'
        boltz.save()
    except LightningService.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0010_add_is_custodial_to_lightningservice'),
    ]

    operations = [
        migrations.RunPython(fix_boltz_custodial_status, reverse_boltz_custodial_status),
    ]