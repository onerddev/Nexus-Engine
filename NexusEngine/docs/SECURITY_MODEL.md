# Modelo de Segurança - Nexus Engine

**Autor**: Emanuel Felipe  
**Versão**: 1.0.0

---

## [AVISO] Aviso Crítico

**Nexus Engine NÃO é seguro para aplicações sensíveis a segurança.**

Este projeto é educacional e não foi auditado por especialistas em segurança. Não use paras:
- Sistemas de pagamento
- Dados financeiros
- Informações pessoais (PII)
- Criptografia de dados
- Autenticação de usuários

---

## Modelo de Ameaça

### O Que Este Sistema MantémSafe

1. **Data Races em Computação**: Mutex-protected access garante leitura consistente
2. **Corrupção de Estado**: Atomic operations previnem corrupta parcial
3. **Buffer Overflow em MemoryPool**: Bounds checking em allocate/deallocate

### O Que Este Sistema NÃO Garante

1. **Confidencialidade**: Sem encriptação em transit
2. **Autenticação**: Sem mecanismo de verificação de identidade
3. **Autorização**: Sem controle de acesso
4. **Integridade de dados criptográfica**: Hashes não são seguros
5. **Auditoria**: Sem logging de quem fez o quê
6. **Isolamento de usuários**: Sem tenants
7. **Proteção contra DoS**: Rate limit é trivial

---

## Componentes de Segurança Implementados

### 1. API Rate Limiting

**Arquivo**: `api/middleware/middleware.py`

```python
class RateLimitMiddleware:
    @staticmethod
    async def rate_limit(request):
        key = f"{client_ip}:{endpoint}"
        if redis.get(key) > MAX_REQUESTS_PER_MINUTE:
            return HTTPException(429, "Too many requests")
```

**Proteção**: Contra abuse/DoS simples  
**Limitação**: Fácil bypassar com múltiplos IPs

### 2. Input Validation

**Arquivo**: `api/models/schemas.py`

```python
class BinaryOperationRequest(BaseModel):
    operation: Literal["xor", "and", "or"]
    value_a: int  # Pydantic valida tipo
    value_b: int
```

**Proteção**: Contra invalid input  
**Limitação**: Sem fuzzing, sem validação de business logic

### 3. CORS

**Arquivo**: `api/middleware/middleware.py`

```python
class CORSMiddleware:
    allowed_origins = ["http://localhost:3000"]
```

**Proteção**: Contra requests de domínios arbitrários  
**Limitação**: Configuração em código, não dinâmica

---

## Componentes de Segurança NÃO Implementados

### 1. Criptografia em Transit

**Falta**: Sem TLS/HTTPS  

**Solução**:
```bash
# Usar nginx reverse proxy com SSL
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### 2. Autenticação

**Falta**: Sem API key, JWT, ou OAuth  

**Solução** (exemplo com Bearer token):
```python
@app.post("/compute/binary")
async def binary_op(request: BinaryOp, token: str = Header()):
    if not validate_token(token):
        raise HTTPException(401, "Unauthorized")
```

### 3. Autorização

**Falta**: Sem RBAC (role-based access control)  

**Solução**:
```python
if user.role != "admin" and operation == "admin_only":
    raise HTTPException(403, "Forbidden")
```

### 4. Logging d Auditoria

**Falta**: Sem registro de quem fez o quê  

**Solução**:
```python
audit_log.info(f"User {user_id} called {endpoint} with {request}")
```

---

## Hash Functions - Não São Criptográficas

### O Problema

```
Nexus Engine oferece:
  - xxhash64()
  - murmur3_64()
```

**Standard diz**: Não são para criptografia.

### Quando NÃO Usar

#### [NAO] Senhas

```cpp
// ERRADO ✗
uint64_t hashed_password = xxhash64(user_password);
if (hashed_password == stored_hash) {
    // Login OK
}
```

**Por quê**: xxhash é rápido demais.
- Attacker com GPU: 10 billions/segundo
- Usuario típico: Tenta ~1000/segundo
- **Atacante ganha em 1 milissegundo**

**Solução correta**: bcrypt/Argon2
```cpp
// CORRETO ✓
std::string hashed = bcrypt::hash(password, 12);  // 12 rounds
// Attacker: ~100s por tentativa mesmo com GPU
```

#### [NAO] Assinaturas Digitais

```cpp
// ERRADO ✗
uint64_t signature = xxhash64(data);
// Attacker pode forjar assinatura em nanossegundos
```

**Solução**: Ed25519 (via libsodium)
```cpp
sodium_crypto_sign_detached(sig, NULL, data, datalen, sk);
// Cryptographically secure
```

#### [NAO] HMAC (Hash-based Message Authentication Code)

```cpp
// ERRADO ✗
uint64_t hmac = xxhash64(secret + data);
// Timing attack: attacker pode adivinhar bytes
```

**Solução**: libsodium
```cpp
crypto_auth(out, data, datalen, key);
// Constant-time comparison
```

#### [NAO] Derivação de Chaves

```cpp
// ERRADO ✗
AES_KEY = xxhash64(password);
// Fraco contra brute-force
```

**Solução**: HKDF ou Argon2
```cpp
crypto_pwhash(key, keylen, password, salt, 
              ARGON2_OPSLIMIT_MODERATE, 
              ARGON2_MEMLIMIT_MODERATE);
```

### OK Usar Para

#### [OK] Hash Tables

```cpp
std::unordered_map<K, V, XXHash> map;
// Rápido, distribuição boa, tidak precisa seguro
```

#### [OK] Deduplicação

```cpp
uint64_t file_hash = xxhash64(file_data);
if (seen.count(file_hash)) {
    // Arquivo duplicado (com false positive rate)
}
```

#### [OK] Checksums Não-Críticos

```cpp
uint64_t checksum = xxhash64(packet_data);
// Detecta corrupção acidental, não deliberada
```

#### [OK] Cache Keys

```cpp
std::string cache_key = "query:" + std::to_string(xxhash64(sql));
// Rápido, não precisa criptográfico
```

---

## Recomendações de Hardening

### Para Production

Se mesmo assim rodar em produção:

#### 1. TLS/HTTPS

```nginx
server {
    listen 443 ssl http2;
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

#### 2. Autenticação

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/compute/binary")
async def binary_op(request: BinaryOp, 
                   token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    user_id = payload.get("sub")
```

#### 3. Logging

```python
import logging

logger = logging.getLogger(__name__)

@app.post("/compute/binary")
async def binary_op(request: BinaryOp):
    logger.info(f"Binary operation: {request.operation} "
                f"a={request.value_a} b={request.value_b}")
    result = compute_service.binary_op(...)
    logger.info(f"Result: {result}")
```

#### 4. Input Validation

```python
from typing import Literal

class BinaryOperationRequest(BaseModel):
    operation: Literal["xor", "and", "or"]
    value_a: int = Field(..., ge=0, le=2**64-1)
    value_b: int = Field(..., ge=0, le=2**64-1)
```

#### 5. Rate Limiting Apropriado

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/compute/binary")
@limiter.limit("10/minute")  # 10 requests/minute per IP
async def binary_op(request: BinaryOp):
```

#### 6. CORS Restritivo

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Authorization"],
)
```

#### 7. SQL Injection Prevention

```python
# ERRADO ✗
query = f"SELECT * FROM users WHERE id = {user_id}"
db.execute(query)

# CORRETO ✓
query = "SELECT * FROM users WHERE id = ?"
db.execute(query, (user_id,))  # Parameterized
```

#### 8. Monitoring & Alerting

```python
from prometheus_client import Counter

compute_errors = Counter('compute_errors_total', 'Total compute errors')

try:
    result = compute_service.binary_op(...)
except Exception as e:
    compute_errors.inc()
    logger.error(f"Error: {e}")
    raise
```

---

## Bibliotecas Recomendadas

### Criptografia

| Necessidade | Biblioteca | Linguagem |
|------------|-----------|----------|
| AES-256 | libsodium | C, Python |
| Hashing | bcrypt | Python |
| HMAC | libsodium | C, Python |
| Assinaturas | Ed25519 (NaCl) | C, Python |
| Random seguro | os.urandom() | Python |

### Web

| Necessidade | Biblioteca |
|----------|-----------|
| CORS | fastapi.middleware.cors |
| Rate limiting | slowapi |
| JWT | python-jose |
| Bcrypt | bcrypt |

---

## Conclusão

Nexus Engine é um projeto **educacional**. Para usar em produção:

1. **Nunca** use para dados sensíveis sem hardening
2. **Sempre** coloque atrás de TLS/HTTPS
3. **Sempre** adicione autenticação
4. **Nunca** use xxhash para criptografia
5. **Sempre** valide input
6. **Sempre** monitor e log
7. **Sempre** faça code review

---

**Emanuel Felipe**  
https://github.com/onerddev/Nexus-Engine.git

