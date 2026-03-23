# NexusEngine Omega v3.0

**Motor Computacional de Alta Performance**

> **Autor:** Emanuel Felipe — [@onerddev](https://github.com/onerddev)  
> **Versão:** 3.0.0 · **Licença:** MIT · **Python 3.10+**

---

## Início rápido

### Windows
```
Duplo clique em: iniciar.bat
```
Abre o dashboard automaticamente no navegador.

### Manual
```bash
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```
Dashboard: **http://localhost:8000/dashboard**

---

## Módulos (8 engines)

| Engine | Endpoints | Funcionalidades |
|---|---|---|
| **Binary** | `POST /compute/binary` | 14 operações: XOR, AND, OR, NOT, NAND, NOR, XNOR, SHL, SHR, ROL, ROR, popcount, parity, reverse_bits |
| **Matrix** | `POST /compute/matrix` | 10 tipos: zeros, ones, identity, random, hilbert, magic, vandermonde, toeplitz + det/trace/rank/norm |
| **Matrix** | `POST /compute/matrix/multiply` | Multiplicação AxB |
| **Matrix** | `POST /compute/matrix/solve` | Sistema linear Ax=b |
| **Quantum** | `POST /compute/quantum` | 12 portas: H, X, Y, Z, S, T, Sdg, CNOT, CZ, SWAP, Rx, Ry, Rz + vetor de estado + entropia |
| **Hash** | `POST /hash` | 10 algoritmos: md5, sha1, sha224, sha256, sha384, sha512, sha3_256, sha3_512, blake2b, blake2s |
| **Hash** | `POST /hash/all` | Todos os algoritmos de uma vez |
| **Hash** | `POST /hash/verify` | Verificação de hash |
| **Hash** | `POST /hash/hmac` | HMAC |
| **Sort** | `POST /compute/sort` | 8 algoritmos: bubble, insertion, selection, merge, quick, heap, shell, counting |
| **Sort** | `POST /compute/sort/benchmark` | Compara todos os algoritmos no mesmo dataset |
| **Prime** | `POST /compute/prime` | is_prime, sieve (crivo de Eratóstenes), factorize, goldbach, nth_prime |
| **Sequence** | `POST /compute/sequence` | fibonacci, collatz, pascal, lucas, tribonacci |
| **Statistics** | `POST /compute/stats` | 12 métricas: mean, median, std, variance, percentis, skewness, kurtosis |
| **Statistics** | `POST /compute/stats/correlation` | Correlação de Pearson |
| **Statistics** | `POST /compute/stats/histogram` | Histograma de frequência |
| **Metrics** | `GET /metrics` | Latência p50/p95/p99, throughput, CPU, RAM, por módulo |
| **Metrics** | `POST /metrics/stress` | Stress test com threads paralelas |

---

## Dashboard

Interface web completa em `/dashboard`:
- Métricas ao vivo (2.5s)
- Barras de uso por módulo
- Testador com 40+ endpoints pré-configurados
- Log de requests

---

## Exemplos

```bash
# XOR
curl -X POST http://localhost:8000/compute/binary \
  -H "Content-Type: application/json" \
  -d '{"operation":"xor","value_a":255,"value_b":170}'

# Bell State
curl -X POST http://localhost:8000/compute/quantum \
  -H "Content-Type: application/json" \
  -d '{"qubits":2,"operation":"bell"}'

# Sort benchmark
curl -X POST http://localhost:8000/compute/sort/benchmark \
  -H "Content-Type: application/json" \
  -d '{"data":[64,34,25,12,22,11,90]}'

# Fibonacci
curl -X POST http://localhost:8000/compute/sequence \
  -H "Content-Type: application/json" \
  -d '{"operation":"fibonacci","n":20}'

# Fatoração
curl -X POST http://localhost:8000/compute/prime \
  -H "Content-Type: application/json" \
  -d '{"operation":"factorize","n":360}'
```

---

## Estrutura

```
NexusEngine/
├── api/
│   ├── main.py                    # FastAPI app
│   ├── middleware/middleware.py   # CORS, rate limit, logging, request ID
│   ├── models/schemas.py          # Schemas Pydantic v2
│   ├── routers/
│   │   ├── routes.py              # 25+ endpoints
│   │   └── dashboard.py          # Dashboard web embutido
│   └── services/
│       ├── engine_core.py         # 9 engines de computação
│       └── services.py            # Camada de serviço
├── iniciar.bat                    # Launcher Windows
├── requirements.txt
└── README.md
```

---

## Autor

**Emanuel Felipe** · [github.com/onerddev](https://github.com/onerddev) · MIT License
