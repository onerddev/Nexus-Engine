# Arquitetura - Nexus Engine

**Autor**: Emanuel Felipe  
**Versão**: 1.0.0  
**Data**: 2026-02-22

---

## Visão Geral do Sistema

Nexus Engine é organizado em três camadas integradas:

```
┌──────────────────────────────────┐
│   FastAPI (HTTP/REST/JSON)       │
│   Validação com Pydantic         │
└────────────┬─────────────────────┘
             │
┌────────────▼──────────────────────┐
│   Cython Bindings (type-safe)     │
│   Tradução Python ↔ C++           │
└────────────┬──────────────────────┘
             │
┌────────────▼──────────────────────┐
│   C++20 Core (computação)         │
│   CoreEngine, processadores       │
│   ThreadPool, MemoryPool, etc     │
└──────────────────────────────────┘
```

---

## Componentes Implementados

### 1. CoreEngine

**Responsabilidade**: Orquestrador central que gerencia lifecycle, thread pool, e coleta de métricas.

**Arquivo**: `cpp/src/core_engine.cpp`

**O que faz**:
- Inicializa N worker threads na startup
- Aguarda tarefas da fila
- Pausa/resume execução
- Coleta métricas em tempo real (tasks processadas, falhas, latência)

**Estado**:
```
STOPPED → RUNNING ↔ PAUSED → STOPPED
```

**Métodos principais**:
- `start()`: Cria worker threads, muda para RUNNING
- `stop()`: Aguarda fila vazia, mata threads, retorna ao STOPPED
- `pause()`: Pausa workers (mantém fila)
- `submit_task(priority, callable)`: Enfileira tarefa com prioridade
- `get_metrics()`: Retorna snapshot de métricas

### 2. ThreadPool

**Responsabilidade**: Distribuir tarefas entre múltiplos threads, executar em paralelo.

**Arquivo**: `cpp/src/thread_pool.cpp`

**Como funciona**:

1. **Main thread** enfileira tarefa:
   ```
   task → std::priority_queue → protegido por std::mutex
   ```

2. **Notification**:
   ```
   queue_cv.notify_one() → acorda 1 worker
   ```

3. **Worker thread**:
   ```
   Aguarda em condition_variable
   ↓
   Desenfila tarefa (protegido por mutex)
   ↓
   Executa FORA do lock (sem contention)
   ↓
   Incrementa counter atomicamente
   ```

**Garantias**:
- Sem deadlock: condition_variable + timeout explícito
- Sem double-execution: Tarefa desenfileirada uma vez
- Sem data race: Fila protegida por mutex, counters são atômicos

**Performance**:
- Enqueue: O(log N) - inserção em heap
- Dequeue: O(log N) - remoção de heap
- Execution: Verdadeiramente paralelo (tasks em threads diferentes)

### 3. MemoryPool

**Responsabilidade**: Pré-alocar blocos de memória na inicialização, reusá-los sem fragmentação.

**Arquivo**: `cpp/src/memory_pool.cpp`

**Trade-off**:
- **Pro**: Zero fragmentação, previsível, cache-friendly
- **Con**: Busca linear O(n), tamanho fixo

**Como funciona**:

1. **Inicialização**: Pré-aloca N blocos de tamanho BLOCK_SIZE
2. **Alocação**: Busca bloco com `allocated == false`
   ```cpp
   std::lock_guard<std::mutex> lock(blocks_mutex_);
   for (auto& block : blocks_) {
       if (!block.allocated.load(std::memory_order_acquire)) {
           block.allocated.store(true, std::memory_order_release);
           return block.data;
       }
   }
   ```
3. **Dealocação**: Reset do flag `allocated = false`

**Validações**:
- Bounds checking: Verifica se endereço está dentro do pool
- Nil pointer check: Dealocate rejeita null
- Mutex protection: Sem race conditions

### 4. BinaryProcessor

**Responsabilidade**: Operações bitwise em 64-bit words.

**Arquivo**: `cpp/src/binary_processor.cpp`

**Operações**:
- `xor_op(a, b)`: XOR bitwise
- `and_op(a, b)`: AND bitwise
- `or_op(a, b)`: OR bitwise
- `not_op(a)`: NOT bitwise
- `shift_left(a, bits)`: Shift esquerda
- `shift_right(a, bits)`: Shift direita
- `rotate_left(a, bits)`: Rotação esquerda
- `rotate_right(a, bits)`: Rotação direita
- `popcount(a)`: Contar bits setados
- `leading_zeros(a)`: Contar zeros à esquerda

**Performance**:
- CPU instruction diretamente (não loops)
- Latência: ~1-2 ciclos de CPU por operação

### 5. QuantumSimulator

**Responsabilidade**: Simulação clássica de qubits com amplitudes complexas.

**Arquivo**: `cpp/src/quantum_simulator.cpp`

**O que é**:
- Simula estado quântico usando números complexos
- Cada qubit tem amplitudes α (|0⟩) e β (|1⟩)
- Normalização automática do estado

**O que NÃO é**:
- Não é computação quântica real
- Sem emaranhamento verdadeiro
- Sem superposição física
- É simulação educacional clássica

**Operações**:
- `initialize_ground_state()`: Todos qubits em |0⟩
- `initialize_superposition()`: Todos em (|0⟩ + |1⟩)/√2
- `apply_hadamard(qubit)`: Porta Hadamard
- `apply_pauli_x(qubit)`: Porta NOT
- `measure(qubit)`: Colapsa para 0 ou 1

**Complexidade**:
- Memória: O(2^n) espaco para estado de n qubits
- Limite prático: ~20 qubits em RAM normal

### 6. MatrixEngine

**Responsabilidade**: Operações de álgebra linear com matrizes de doubles.

**Arquivo**: `cpp/src/matrix_engine.cpp`

**Tipos**:
```cpp
using Matrix = std::vector<std::vector<double>>;
using Vector = std::vector<double>;
```

**Factory methods**:
- `create_zeros(rows, cols)`: Matriz de zeros
- `create_ones(rows, cols)`: Matriz de uns
- `create_identity(size)`: Matriz identidade
- `create_random(rows, cols, min, max)`: Valores aleatórios

**Operações**:
- `add(a, b)`: Adição elemento-wise
- `multiply(a, b)`: Multiplicação de matrizes
- `transpose(m)`: Transposição
- `determinant(m)`: Determinante (2x2, 3x3)
- `invert(m)`: Inversa usando Gaussian elimination
- `trace(m)`: Soma da diagonal

**Validações**:
- Dimensionalidade: Erro se dimensões incompatíveis
- Singularidade: Erro se matriz não é invertível

**Limitação conhecida**:
- Sem pivotamento parcial na inversão → possível instabilidade numérica em matrizes mal-condicionadas

### 7. HashEngine

**Responsabilidade**: Hash rápido para dados, NÃO criptográfico.

**Arquivo**: `cpp/src/hash_engine.cpp`

**Algoritmos**:
- `xxhash64()`: Ultra-rápido (~1 GB/s), 64-bit output
- `murmur3_64()`: MurmurHash, varianção 64-bit

**O que faz**:
- Deduplicação
- Hash tables internas
- Checksums não-críticos
- Distribuição uniforme em tabelas de hash

**O que NÃO faz**:
- Senhas (use bcrypt/Argon2)
- Assinaturas (use Ed25519)
- HMAC (use libsodium)
- Qualquer coisa que precisa de segurança

### 8. MetricsCollector

**Responsabilidade**: Capturar latência, throughput, uso de recursos sem overhead.

**Arquivo**: `cpp/src/metrics_collector.cpp`

**Métricas coletadas**:
```cpp
std::atomic<uint64_t> processed_items{0};
std::atomic<uint64_t> failed_items{0};
std::atomic<uint64_t> total_latency_us{0};      // soma de latências
std::atomic<uint32_t> current_queue_size{0};
std::atomic<uint32_t> active_threads{0};
std::atomic<double> avg_throughput{0.0};
std::atomic<double> cpu_usage{0.0};
```

**Coleta**:
- Timestamp no enqueue
- Timestamp no dequeue
- Latência = dequeue_time - enqueue_time

**Zero-copy**: Metrics são `std::atomic`, leitura não-blocking.

### 9. PluginLoader

**Responsabilidade**: Carregar .so/.dll (bibliotecas compartilhadas) em runtime.

**Arquivo**: `cpp/src/plugin_loader.cpp`

**Como funciona**:

1. **dlopen()**: Carrega biblioteca
2. **dlsym()**: Busca símbolo `create_plugin`
3. **Plugin::initialize()**: Inicializa plugin
4. **Plugin::shutdown()**: Cleanup on unload

**Mecanismo**:
- Plugins implementam interface base `Plugin`
- Factory function `create_plugin()` retorna unique_ptr
- Lazy loading: Plugins carregam sob demanda

### 10. SIMDOps

**Responsabilidade**: Operações SIMD (vetorizadas) via instruções AVX2/SSE4.2.

**Arquivo**: `cpp/src/simd_ops.cpp`

**Detecção em runtime**:
```cpp
if (cpu_has_avx2()) {
    // Use AVX2 (256-bit)
} else if (cpu_has_sse42()) {
    // Use SSE4.2 (128-bit)
} else {
    // Fallback scalar
}
```

**Operações**:
- Dot product: Multiplicação de vetores SIMD
- Element-wise add/multiply
- Reduction (min, max, sum)

### 11. LockFreeQueue

**Responsabilidade**: Queue ring-buffer sem locks, single-producer/single-consumer.

**Arquivo**: `cpp/include/lock_free_queue.hpp` + `cpp/src/lock_free_queue_impl.hpp`

**Características**:
```cpp
template <typename T>
class LockFreeQueue {
    std::vector<T> buffer_;
    std::atomic<uint32_t> head_{0};
    std::atomic<uint32_t> tail_{0};
    uint32_t capacity_;
};
```

**Síncronia**:
- `head_`: Apontador para próximo a desenfileirar (producer)
- `tail_`: Apontador para próximo a enfileirar (consumer)
- Ambos com `std::memory_order_acquire/release`

**Latência**:
- Enqueue: ~100-200 ns (sem locks)
- Dequeue: ~100-200 ns (sem locks)

**Limitação**: SPSC (single-producer, single-consumer), não MPMC.

---

## Integração API ↔ Core

### Fluxo de uma Requisição Binária

```
1. HTTP POST /compute/binary
   ├─ Body: {"operation": "xor", "value_a": 42, "value_b": 255}
   │
2. FastAPI valida com Pydantic
   ├─ operation ∈ {xor, and, or, not, shift_left, ...}?
   ├─ value_a, value_b são inteiros?
   │
3. Roteador chama BinaryService.xor(42, 255)
   │
4. BinaryService chama Cython binding
   ├─ nexus_engine.binary_xor(42, 255)
   │
5. Cython traduz tipos
   ├─ Python int → C++ uint64_t
   │
6. C++ executa
   ├─ BinaryProcessor::xor_op(42, 255) = 213
   │
7. Resultado volta
   ├─ C++ uint64_t → Python int → JSON
   │
8. HTTP 200 {"result": 213, "result_binary": "0b11010101"}
```

**Latência esperada**: 1-5 ms total
- Overhead de API: ~1 ms
- Overhead de Cython: <100 µs
- Operação C++: ~1 µs
- JSON serialization: ~100 µs

---

## Trade-offs de Design

### Mutex vs Lock-Free

**Escolhido**: Mutex + condition_variable para ThreadPool  
**Motivo**: Simplicidade, verificabilidade com ThreadSanitizer  
**Trade-off**: Possível contenção vs garantia de correctness

**Para**: Usamos lock-free (LockFreeQueue) para casos que precisam  
**Razão**: Single-producer/single-consumer é suficiente para certos use cases

### Pré-alocação vs Dinâmica

**Escolhido**: MemoryPool pré-alocado  
**Motivo**: Zero fragmentação, previsibilidade  
**Trade-off**: Max RAM é fixo, menos flexibilidade

### Fila Centralizada vs Work-Stealing

**Escolhido**: Fila centralizada com priority_queue  
**Motivo**: Simples, priorização FIFO  
**Trade-off**: Possível contenção com >16 threads

---

## Deployment Architecture

### Local

```
FastAPI Server (1 process)
    ↓
C++20 Core (thread pool)
    ↓
PostgreSQL (opcional, persistência)
```

### Docker

```
Docker Compose
├─ Service: nexus_api (FastAPI)
├─ Service: postgres (PostgreSQL)
└─ Service: redis (Cache, opcional)
```

---

## Escalabilidade Atual

**Single Machine**: Sim  
**Multi-Process**: Sim (nginx load balance)  
**Distributed**: Não (sem replicação)  
**GPU**: Não (CPU only)  

---

**Emanuel Felipe**  
https://github.com/onerddev/Nexus-Engine.git

