# Security Guidelines for GeoEDF Connectors

## Overview
This document outlines security best practices for the GeoEDF Connectors repository to prevent accidental exposure of sensitive information.

## ⚠️ NEVER commit these items:

### 1. Authentication Credentials
- Usernames and passwords
- API keys and secrets
- Bearer tokens and JWT tokens
- OAuth tokens and refresh tokens
- SSH private keys
- SSL certificates and private keys

### 2. Configuration Files with Secrets
- `.env` files with credentials
- `config.py` files with hardcoded secrets
- Database connection strings with passwords
- Service account JSON files

### 3. Test Data with Real Credentials
- Test files with real usernames/passwords
- Example code with actual API keys
- Debug output containing sensitive headers

## ✅ Best Practices

### 1. Use Environment Variables
```python
import os

# Good: Use environment variables
username = os.getenv('EARTHDATA_USERNAME')
password = os.getenv('EARTHDATA_PASSWORD') 
bearer_token = os.getenv('EARTHDATA_BEARER_TOKEN')

# Bad: Hardcoded credentials
username = "myusername"  # DON'T DO THIS
password = "mypassword"  # DON'T DO THIS
```

### 2. Use Configuration Files (Not in Git)
```python
# config/local_secrets.py (add to .gitignore)
EARTHDATA_USERNAME = "your_username"
EARTHDATA_PASSWORD = "your_password"

# In your code:
try:
    from config.local_secrets import EARTHDATA_USERNAME, EARTHDATA_PASSWORD
except ImportError:
    EARTHDATA_USERNAME = os.getenv('EARTHDATA_USERNAME')
    EARTHDATA_PASSWORD = os.getenv('EARTHDATA_PASSWORD')
```

### 3. Use Placeholders in Examples
```python
# Good: Use placeholders
bearer_token = "YOUR_BEARER_TOKEN_HERE"
username = "your_earthdata_username"
password = "your_earthdata_password"

# Good: Show the pattern but not real values
# Example JWT structure: eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.payload.signature
```

### 4. Sanitize Debug Output
```python
# Good: Mask sensitive information in logs
print(f"Username: {username[:3]}***")
print(f"Token: {token[:10]}...")

# Bad: Print full credentials
print(f"Username: {username}")  # DON'T DO THIS
print(f"Token: {token}")        # DON'T DO THIS
```

## 🔧 Repository Setup

### 1. Update .gitignore
The repository `.gitignore` includes patterns to prevent common credential files:
```
# Security: Credential files and tokens
*.key
*.pem
.env
.env.*
config/secrets.py
**/secrets.py
**/*_token.txt
**/*_credentials.json
```

### 2. Pre-commit Hooks (Recommended)
Consider adding pre-commit hooks to scan for secrets:
```bash
pip install pre-commit detect-secrets
pre-commit install
```

### 3. Regular Security Scans
- Use tools like GitGuardian, GitLeaks, or TruffleHog
- Review commits before pushing
- Scan the repository periodically

## 🚨 If You Accidentally Commit Secrets

### 1. Immediate Actions
1. **Revoke the compromised credentials immediately**
2. **Remove the secret from the code**
3. **Commit and push the fix**
4. **Generate new credentials**

### 2. Clean Git History (if needed)
⚠️ **WARNING**: This rewrites git history and affects all collaborators
```bash
# For recent commits, use git revert instead of rewriting history
git revert <commit-with-secret>

# Only for emergency cases with sensitive data:
# git filter-branch --force --index-filter \
#   'git rm --cached --ignore-unmatch path/to/file/with/secret' \
#   --prune-empty --tag-name-filter cat -- --all
```

### 3. Notify Team
- Inform all team members about the credential compromise
- Update any systems using the compromised credentials
- Document the incident for future reference

## 📋 Security Checklist

Before committing code, verify:
- [ ] No hardcoded usernames or passwords
- [ ] No API keys or tokens in the code
- [ ] Environment variables used for secrets
- [ ] Test data uses placeholders, not real credentials
- [ ] Debug output doesn't expose sensitive information
- [ ] `.gitignore` patterns cover credential files

## 📞 Incident Response

If GitGuardian or other security tools detect exposed secrets:
1. **Immediately revoke the exposed credential**
2. **Remove it from the code and commit the fix**
3. **Generate new credentials**
4. **Update any systems using the old credential**
5. **Review how the exposure happened and improve processes**

## 🔗 Resources

- [GitHub Security Best Practices](https://docs.github.com/en/code-security/getting-started/securing-your-repository)
- [GitGuardian Documentation](https://docs.gitguardian.com/)
- [OWASP Secrets Management](https://owasp.org/www-community/vulnerabilities/Information_exposure_through_server_log_files)
- [NASA Earthdata Security](https://wiki.earthdata.nasa.gov/display/EL/How+To+Access+Data+With+Python)

---
**Remember**: It's always better to be overly cautious with credentials than to risk a security incident.
