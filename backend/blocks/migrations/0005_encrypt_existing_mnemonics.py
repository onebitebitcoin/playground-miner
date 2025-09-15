# Generated manually for encrypting existing mnemonics

from django.db import migrations
from blocks.encryption import encrypt_mnemonic, is_encrypted_mnemonic
import logging

logger = logging.getLogger(__name__)

def encrypt_existing_mnemonics(apps, schema_editor):
    """
    Encrypt all existing plaintext mnemonics in the database
    """
    Mnemonic = apps.get_model('blocks', 'Mnemonic')

    encrypted_count = 0
    total_count = 0

    for mnemonic_obj in Mnemonic.objects.all():
        total_count += 1

        # Check if mnemonic is already encrypted
        if not is_encrypted_mnemonic(mnemonic_obj.mnemonic):
            try:
                # Encrypt the mnemonic
                encrypted_mnemonic = encrypt_mnemonic(mnemonic_obj.mnemonic)
                mnemonic_obj.mnemonic = encrypted_mnemonic
                mnemonic_obj.save(update_fields=['mnemonic'])
                encrypted_count += 1
                logger.info(f"Encrypted mnemonic for user: {mnemonic_obj.username}")
            except Exception as e:
                logger.error(f"Failed to encrypt mnemonic for user {mnemonic_obj.username}: {e}")
                # Continue with other mnemonics even if one fails
                continue

    logger.info(f"Encryption migration complete: {encrypted_count}/{total_count} mnemonics encrypted")

def decrypt_all_mnemonics(apps, schema_editor):
    """
    Reverse migration: decrypt all mnemonics back to plaintext
    WARNING: This should only be used in development
    """
    Mnemonic = apps.get_model('blocks', 'Mnemonic')

    from blocks.encryption import decrypt_mnemonic

    decrypted_count = 0
    total_count = 0

    for mnemonic_obj in Mnemonic.objects.all():
        total_count += 1

        # Check if mnemonic is encrypted
        if is_encrypted_mnemonic(mnemonic_obj.mnemonic):
            try:
                # Decrypt the mnemonic
                decrypted_mnemonic = decrypt_mnemonic(mnemonic_obj.mnemonic)
                mnemonic_obj.mnemonic = decrypted_mnemonic
                mnemonic_obj.save(update_fields=['mnemonic'])
                decrypted_count += 1
                logger.info(f"Decrypted mnemonic for user: {mnemonic_obj.username}")
            except Exception as e:
                logger.error(f"Failed to decrypt mnemonic for user {mnemonic_obj.username}: {e}")
                # Continue with other mnemonics even if one fails
                continue

    logger.info(f"Decryption migration complete: {decrypted_count}/{total_count} mnemonics decrypted")

class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0004_mnemonic'),
    ]

    operations = [
        migrations.RunPython(
            encrypt_existing_mnemonics,
            decrypt_all_mnemonics,
            atomic=True,
        ),
    ]