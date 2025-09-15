# Security Implementation for Mnemonic Storage

## Overview
This implementation provides robust security for storing cryptocurrency mnemonic phrases in the database. Even if the database is compromised, the mnemonics remain protected through encryption.

## Security Features

### 1. Encryption at Rest
- All mnemonic phrases are encrypted using **Fernet** (symmetric encryption) before being stored in the database
- Uses AES 128 encryption in CBC mode with HMAC authentication
- Each mnemonic is individually encrypted with a unique IV

### 2. Environment-Based Key Management
- Encryption keys are stored in environment variables, not in code
- Uses `python-decouple` for secure environment variable management
- Development and production keys should be different

### 3. Automatic Encryption/Decryption
- Model-level encryption: mnemonics are automatically encrypted when saved
- Transparent decryption when accessing mnemonic data
- Backward compatibility with existing plaintext mnemonics

### 4. Security Logging
- All encryption/decryption operations are logged
- Failed operations are logged with error details
- Separate security log file for audit purposes

## Setup Instructions

### 1. Environment Configuration
Copy the `.env.example` file to `.env` and update the values:

```bash
cp .env.example .env
```

### 2. Generate Encryption Key
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the generated key to your `.env` file:
```
MNEMONIC_ENCRYPTION_KEY=your-generated-key-here
```

### 3. Database Migration
Run the migration to encrypt existing mnemonics:
```bash
python3 manage.py migrate
```

## Security Best Practices

### Production Environment
1. **Use a strong encryption key**: Generate a new key for production
2. **Secure key storage**: Store the encryption key securely (e.g., AWS Secrets Manager, Azure Key Vault)
3. **Environment separation**: Use different keys for development, staging, and production
4. **Regular key rotation**: Consider implementing key rotation policies
5. **Backup security**: Ensure backups also maintain encryption

### Database Security
1. **Database encryption**: Enable database encryption at rest if supported
2. **Access controls**: Limit database access to authorized personnel only
3. **Network security**: Use VPNs or private networks for database access
4. **Audit logging**: Enable database audit logging

### Application Security
1. **HTTPS only**: Always use HTTPS in production
2. **Rate limiting**: Implement rate limiting on mnemonic endpoints
3. **Authentication**: Add proper authentication for admin functions
4. **Input validation**: Validate all mnemonic inputs

## Risk Assessment

### Threats Mitigated
✅ **Database compromise**: Encrypted mnemonics are useless without the key
✅ **SQL injection**: Data remains encrypted even if accessed
✅ **Insider threats**: Database administrators cannot read mnemonics
✅ **Backup exposure**: Backup files contain encrypted data

### Remaining Risks
⚠️ **Application compromise**: If the application server is compromised, decryption is possible
⚠️ **Key exposure**: If the encryption key is exposed, all mnemonics can be decrypted
⚠️ **Memory dumps**: Decrypted mnemonics may exist temporarily in memory

### Additional Recommendations
1. **Hardware Security Modules (HSM)**: For enterprise deployments
2. **Key escrow**: Secure backup of encryption keys
3. **Multi-party computation**: For high-security scenarios
4. **Cold storage**: Consider offline storage for high-value mnemonics

## Monitoring and Alerts

Monitor the `security.log` file for:
- Failed encryption/decryption attempts
- Unusual access patterns
- Key initialization issues

Set up alerts for:
- Multiple decryption failures
- Key rotation events
- Unauthorized access attempts

## Recovery Procedures

### Lost Encryption Key
If the encryption key is lost:
1. Existing encrypted mnemonics cannot be recovered
2. New mnemonics can be generated and encrypted with a new key
3. Users will need to re-enter their mnemonics

### Key Compromise
If the encryption key is compromised:
1. Generate a new encryption key immediately
2. Re-encrypt all existing mnemonics with the new key
3. Revoke access to the old key
4. Review access logs for suspicious activity

## Testing

Test the encryption implementation:
```bash
# Test encryption/decryption
python3 manage.py shell
>>> from blocks.encryption import encrypt_mnemonic, decrypt_mnemonic
>>> test_mnemonic = "abandon ability able about above absent absorb abstract absurd abuse access accident"
>>> encrypted = encrypt_mnemonic(test_mnemonic)
>>> decrypted = decrypt_mnemonic(encrypted)
>>> assert test_mnemonic == decrypted
```

## Compliance

This implementation supports compliance with:
- **GDPR**: Personal data protection through encryption
- **PCI DSS**: Secure storage of sensitive data
- **SOC 2**: Data encryption controls
- **CCPA**: California Consumer Privacy Act requirements