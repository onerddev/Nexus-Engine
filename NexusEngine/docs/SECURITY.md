# Security Policy - NexusEngine Omega

## Security Overview

NexusEngine Omega implements defense-in-depth security with multiple protective layers:

```
┌──────────────────────────────────┐
│   Network Layer (TLS/HTTPS)      │
├──────────────────────────────────┤
│   API Authentication (API Keys)  │
├──────────────────────────────────┤
│   Rate Limiting (Token Bucket)   │
├──────────────────────────────────┤
│   Input Validation (Pydantic)    │
├──────────────────────────────────┤
│   Database (SQL Parameterization)│
├──────────────────────────────────┤
│   Encryption (AES-256 at rest)   │
└──────────────────────────────────┘
```

## Authentication

### API Key Authentication

```python
# Generate API key
import secrets
api_key = secrets.token_urlsafe(32)

# Use in request
curl -H "X-API-Key: your-api-key" http://localhost:8000/health

# Enable in config
ENABLE_AUTH=true
API_KEY=your-secure-key-here
```

### JWT Tokens (Optional)

```python
from fastapi_jwt_auth import AuthJWT

@app.post("/auth/login")
async def login(credentials: LoginRequest):
    token = create_access_token(credentials)
    return {"access_token": token}

@app.get("/protected")
async def protected_route(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    return {"secure": "data"}
```

## Input Validation

### Pydantic Models

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class BinaryRequest(BaseModel):
    operation: str = Field(..., regex="^(xor|and|or|not)$")
    value_a: int = Field(..., ge=0, le=2**64-1)
    value_b: Optional[int] = Field(None, ge=0, le=2**64-1)
    
    @validator('operation')
    def validate_operation(cls, v):
        if v not in ['xor', 'and', 'or', 'not']:
            raise ValueError('Invalid operation')
        return v
```

### Input Sanitization

```python
import re
from html import escape

def sanitize_input(data: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove SQL injection attempts
    data = re.sub(r"['\";\-\-]", "", data)
    
    # HTML escape
    data = escape(data)
    
    # Limit length
    return data[:1000]
```

## SQL Injection Prevention

### Parameterized Queries

```python
# ✓ SAFE - Parameterized
from sqlalchemy import text

result = session.execute(
    text("SELECT * FROM metrics WHERE metric_name = :name"),
    {"name": user_input}
)

# ✗ UNSAFE - String concatenation
result = session.execute(f"SELECT * FROM metrics WHERE metric_name = '{user_input}'")
```

### ORM Usage

```python
from sqlalchemy.orm import Session
from models import Metric

# SQLAlchemy automatically parameterizes
metrics = session.query(Metric).filter(
    Metric.name == user_input
).all()
```

## Rate Limiting

### Token Bucket Algorithm

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )

# Apply limits
@app.post("/compute/binary")
@limiter.limit("1000/minute")
async def binary_op(request: BinaryRequest):
    pass

# Per-user limits
@app.post("/compute/matrix")
@limiter.limit("100/minute;key=api_key")
async def matrix_op(request: MatrixRequest):
    pass
```

## CORS Configuration

### Secure CORS Setup

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://example.com",
        "https://www.example.com"  # Whitelist specific domains
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600
)

# Never use allow_origins=["*"] in production
```

## Data Encryption

### At-Rest Encryption

```python
from cryptography.fernet import Fernet

cipher_suite = Fernet(encryption_key)

def encrypt_data(plaintext: str) -> str:
    return cipher_suite.encrypt(plaintext.encode()).decode()

def decrypt_data(ciphertext: str) -> str:
    return cipher_suite.decrypt(ciphertext.encode()).decode()
```

### In-Transit Encryption

```yaml
# docker-compose.yml
services:
  nexus_api:
    environment:
      - SSL_CERTFILE=/etc/ssl/certs/server.crt
      - SSL_KEYFILE=/etc/ssl/private/server.key
    volumes:
      - ./certs:/etc/ssl:ro
```

## Password Security

### Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)
```

## Secure Defaults

### Environment Configuration

```env
# .env
# Never commit actual secrets to git!
# Use environment variables or secret management

# API Security
API_KEY_REQUIRED=true
RATE_LIMIT_PER_MINUTE=1000
MAX_REQUEST_SIZE=10485760  # 10MB

# Database
DB_SSL_MODE=require
DB_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
LOG_SENSITIVE_DATA=false  # Never log passwords/keys

# CORS
ALLOWED_ORIGINS=https://example.com
```

### Secret Management

```bash
# Never hardcode secrets!
# Use environment variables
export API_KEY=$(secrets.token_urlsafe)
export DB_PASSWORD=$(pass database/nexus)

# Or secret management service
# AWS Secrets Manager, HashiCorp Vault, etc.
```

## Logging & Monitoring

### Secure Logging

```python
import logging

# Configure secure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nexus.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log security events
logger.warning(f"Failed authentication attempt from {ip}")
logger.error(f"Rate limit exceeded for {api_key}")

# Don't log sensitive data
sensitive_data = password  # ✗ Never log
logger.info(f"User {username} authenticated")  # ✓ Safe
```

### Security Monitoring

```python
@app.middleware("http")
async def log_security_events(request: Request, call_next):
    # Track suspicious activity
    if suspicious_pattern in request.headers:
        logger.warning(f"Suspicious request: {request.url}")
    
    response = await call_next(request)
    return response
```

## Vulnerability Management

### Dependencies

```bash
# Check for vulnerabilities
pip install safety
safety check

# Update dependencies
pip install --upgrade pip
pip install -r requirements.txt --upgrade

# Lock dependencies
pip install pip-tools
pip-compile requirements.in > requirements.txt
```

### Code Security Scanning

```bash
# Bandit finds common security issues
bandit -r . -f json -o bandit-report.json

# Semgrep for custom rules
semgrep --config=p/security-audit .
```

## Incident Response

### Security Incident Process

1. **Detection** - Alert triggered
2. **Triage** - Assess severity
3. **Containment** - Stop ongoing attack
4. **Investigation** - Root cause analysis
5. **Remediation** - Fix vulnerability
6. **Recovery** - Restore services
7. **Post-mortem** - Learn and improve

### Emergency Contacts
- **Security Team**: security@nexusengine.dev
- **On-call**: Check internal wiki
- **Escalation**: CTO/VP Engineering

## Compliance

### Data Protection
- GDPR compliance for EU users
- Data retention policies
- Right to deletion implementation

### Audit Trail
```python
@app.middleware("http")
async def audit_trail(request: Request, call_next):
    # Log all API calls
    audit_log.write({
        "timestamp": datetime.utcnow(),
        "method": request.method,
        "path": request.url.path,
        "user": get_current_user(),
        "ip": request.client.host,
        "status": response.status_code
    })
```

## Security Testing

### Regular Testing
```bash
# Penetration testing
# OWASP Top 10 vulnerability check
# Dependency audit
# Code review

# Schedule
# Monthly: automated scans
# Quarterly: penetration testing
# Annually: security audit
```

## Reporting Security Vulnerabilities

### Private Disclosure
**DO NOT** open public issues for security vulnerabilities.

1. Email: security@nexusengine.dev
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Your contact information
3. Allow 72 hours for response
4. Coordinate disclosure timeline

### Responsible Disclosure
- We will acknowledge receipt within 24 hours
- Provide timeline for fix
- Coordinate disclosure date
- Credit discoverer (if desired)

## Security Best Practices

### For Operators
- [ ] Change default credentials
- [ ] Enable HTTPS/TLS
- [ ] Restrict access to admin endpoints
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Regular backups
- [ ] Test disaster recovery
- [ ] Implement network segmentation

### For Users
- [ ] Use strong API keys
- [ ] Rotate credentials regularly
- [ ] Don't share API keys
- [ ] HTTPS only
- [ ] Monitor account activity
- [ ] Report suspicious activity

---

For questions: security@nexusengine.dev
