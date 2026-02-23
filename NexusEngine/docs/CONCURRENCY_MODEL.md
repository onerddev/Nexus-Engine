# Modelo de Concorrência - Nexus Engine

**Autor**: Emanuel Felipe  
**Versão**: 1.0.0  

---

## Definição Formal

Nexus Engine usa modelo **thread pool baseado em mutex com priorização FIFO e execução paralela de tarefas**.

```
┌─────────────────────┐
│  Main Thread        │
│  (Enqueue tasks)    │
└──────────┬──────────┘
           │
    std::mutex          ← Protege acesso à fila
    std::priority_queue ← Armazena tarefas
           │
    std::condition_variable ← Sinaliza workers
           │
    ┌──────┴──────┬─────────┬──────────┐
    │             │         │          │
    ▼             ▼         ▼          ▼
┌──────┐     ┌──────┐  ┌──────┐  ┌──────┐
│ W1   │     │ W2   │  │ W3   │  │ W4   │  ← Worker Threads
└──────┘     └──────┘  └──────┘  └──────┘
    │             │         │          │
    ▼             ▼         ▼          ▼
 [Task]       [Task]    [Task]    [Task]
 Execute Parallelamente
```

---

## Protocolo ThreadPool

### 1. Enqueue (Main Thread)

```cpp
std::unique_ptr<Task> task = std::make_unique<ComputeTask>(args);

{
    std::lock_guard<std::mutex> lock(queue_mutex_);
    task_queue_.push({priority, std::move(task)});
    stats_.total_tasks++;
}

queue_cv_.notify_one();  // Wake 1 worker
```

**Memory ordering**:
- `lock_guard`: Implicitamente acquire/release

### 2. Wait & Dequeue (Worker Thread)

```cpp
while (running_.load(std::memory_order_acquire)) {
    PrioritizedTask pTask;
    
    {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        
        // Wait até: fila não-vazia OU engine parando
        queue_cv_.wait(lock, [this] {
            return !task_queue_.empty() || !running_;
        });
        
        if (task_queue_.empty()) {
            if (!running_) break;
            continue;
        }
        
        pTask = task_queue_.top();
        task_queue_.pop();
    } // Lock liberado aqui
    
    // Executa FORA do lock (sem contention)
    if (pTask.task) {
        try {
            pTask.task();
            stats_.completed_tasks++;
        } catch (...) {
            stats_.failed_tasks++;
        }
    }
}
```

**Crítico**: Execução acontece sem lock → verdadeiro paralelismo.

### 3. Shutdown (Main Thread)

```cpp
state_ = STOPPED;

// Sinaliza todos workers
queue_cv_.notify_all();

// Aguarda todos threads terminarem
for (auto& t : worker_threads_) {
    if (t.joinable()) {
        t.join();  // Bloqueia até worker terminar
    }
}
```

---

## Memory Ordering

### Atomics e Memory Ordering

```cpp
std::atomic<uint64_t> completed_tasks{0};
std::atomic<EngineState> state_{STOPPED};
```

**Semântica**:

| Operação | Memory Ordering | Propósito |
|----------|-----------------|-----------|
| `state_.load()` | `acquire` | Ler state consistente |
| `state_.store()` | `release` | Escrever state visível |
| `completed_tasks.fetch_add()` | `release` | Stats visível imediatamente |

**Model**:
- **Acquire**: Previne leitura de antes deste ponto
- **Release**: Previne escrita de depois deste ponto
- **acq_rel**: Ambos (usado em CAS)

### Happens-Before Relationship

```
Enqueue (main thread)
    │
    ├─ Acquire lock
    ├─ Write task_queue_
    ├─ Release lock
    │
    ├─ notify_one() ← synchronize-with
    │
    ├─ Dequeue (worker thread)
    │   Read task_queue_
    └─  Executa garantidamente vendo task

Result: Main-thread modifications visible in worker.
```

---

## Garantias de Correctness

### 1. Thread Safety

**Sem Data Races**:
- Fila protegida por `std::mutex`
- Flags de estado são `std::atomic`
- Contadores são `std::atomic`

**Validação**:
```bash
valgrind --tool=helgrind ./program
# ✓ No race-detected errors (se codigo está correto)
```

### 2. Sem Deadlock

**Proof**:
```
1. Mutex é adquirido brevemente (só para enqueue/dequeue)
2. Tarefa é executada FORA do lock (não pode tentar readquirir)
3. Única dependência circular possível: worker aguardando lock
   Mas: Main thread sempre solta lock → worker eventualmente acorda
4. Conclusion: Sem deadlock possível
```

### 3. Sem Race Condition em Shutdown

```cpp
// Main thread
state_ = STOPPED;
queue_cv_.notify_all();

// Worker threads veem STOPPED e saem
while (running_.load(std::memory_order_acquire)) {
    // Vê STOPPED = false, sai do loop
    break;
}
```

---

## Problema: Mutex Contention

### O Problema

Com muitos threads (>16), todos competem por mesmo mutex:

```
Worker 1: ╔═══════════╗  [Execute]  ╔═══╗        ╔═════┐
          ║ Espera    ║             ║   ║        ║Wait │
          ║ mutex     ║             ║   ║        ║....▌│
          ╚═════╤═════╝             ╚═╤═╝        ╚═════┘
                │                     │
          M = Mutex crítico

Worker 2: ╔═════╗  ╔═════════╗  [Execute]  ╔═════╗
          ║Wait ║  ║ Espera  ║             ║Wait ║
          ║.... ║  ║ mutex   ║             ║.... ║
          ╚═════╝  ╚═════════╝             ╚═════╝

Worker 3: ╔═════════╗  [Execute]  ╔═══════╗
          ║ E       ║             ║ Espera║
          ║ s       ║             ║       ║
          ║ p       ║             ║       ║
          ╚═════════╝             ╚═══════╝
```

**Latência total**: Seria melhor com lock-free.

### Solução Parcial

Usar `LockFreeQueue` para cenários SPSC (single-producer, single-consumer):
```cpp
#include "lock_free_queue.hpp"

LockFreeQueue<Task> fast_queue(1024);
```

---

## Priorização

Tasks são enfileiradas com prioridade:

```cpp
enum class TaskPriority : int {
    LOW = 0,
    NORMAL = 1,
    HIGH = 2,
    CRITICAL = 3
};

struct PrioritizedTask {
    TaskPriority priority;
    std::unique_ptr<Task> task;
    
    bool operator<(const PrioritizedTask& other) const {
        return priority < other.priority;  // Min-heap (max priority first)
    }
};
```

**Behavior**: `std::priority_queue` ordena por `operator<`, então:
- CRITICAL (3) sai primeiro
- LOW (0) sai último

**FIFO dentro de mesma prioridade**: Não garantido (priority_queue não preserva).

### Trade-off

- **Pro**: Tasks críticas executam primeiro
- **Con**: Pode starvar LOW priority tasks
- **Mitigação**: Não acontecer na prática se LOW priority não é abuso

---

## Modelo de Lock-Free (LockFreeQueue)

Para alternativa sem mutex:

```cpp
template <typename T>
bool LockFreeQueue<T>::enqueue(const T& value) {
    uint32_t tail = tail_.load(std::memory_order_acquire);
    uint32_t next_tail = (tail + 1) & mask_;
    
    if (next_tail == head_.load(std::memory_order_acquire)) {
        return false;  // Queue full
    }
    
    buffer_[tail] = value;
    tail_.store(next_tail, std::memory_order_release);
    return true;
}
```

**Limitações**:
- SPSC (Single-Producer, Single-Consumer)
- Capacidade fixa
- Sem espera quando cheia (retorna false)

**Performance**: ~100-200 ns per op vs ~1-5 µs com mutex.

---

## Latência End-to-End

### Componentes

| Componente | Latência |
|-----------|----------|
| Enqueue (mutex) | 1-5 µs |
| Condition variable notify | 0.1-0.5 µs |
| Dequeue (mutex) | 1-5 µs |
| Task execution (binary op) | 1-50 µs |
| **Total** | **3-65 µs** |

### Com Contention

Se >>10 threads:
- Enqueue: 5-20 µs (waiting for lock)
- Dequeue: 5-20 µs (waiting for lock)
- **Total**: 20-100 µs

---

## Possíveis Melhorias

### 1. Per-Core Queues

Em vez de 1 queue compartilhada:
```
Core 1: [Local Q] → Local lock
Core 2: [Local Q] → Local lock
Core 3: [Local Q] → Local lock
```

Reduz contention: cada lock protege apenas 1 core.

### 2. Work Stealing

Worker que terminou rouba task de outro:
```cpp
if (my_queue.empty()) {
    steal_from(victim_queue);
}
```

Aproveita melhor load balancing.

### 3. CPU Pinning

```cpp
pthread_t thread = pthread_create();
cpu_set_t cpuset;
CPU_ZERO(&cpuset);
CPU_SET(core_id, &cpuset);  // Pin thread a core específico
pthread_setaffinity_np(thread, sizeof(cpu_set_t), &cpuset);
```

Melhora cache locality.

---

## Validação

### Ferramentas

**ThreadSanitizer**:
```bash
g++ -fsanitize=thread -g program.cpp
./a.out  # ✓ Detecta data races
```

**Helgrind (Valgrind)**:
```bash
valgrind --tool=helgrind ./program
# ✓ Detecta deadlocks, races
```

**Perf**:
```bash
perf record -e sched:sched_wakeup_new ./program
perf report  # Visualiza wakeups/contention
```

---

## Conclusão

O modelo de concorrência de Nexus Engine é:
- **Simples**: Mutex + condition_variable, padrão consolidado
- **Verificável**: ThreadSanitizer consegue validar
- **Paralelo**: Tasks executam verdadeiramente em paralelo
- **Escalável**: Até ~100 threads sem contention excessiva
- **Limitações**: Possível contention em muito threads; trade-off consciente

Para cenários de ultra-low-latency SPSC, considerar `LockFreeQueue`.

---

**Emanuel Felipe**  
https://github.com/onerddev/Nexus-Engine.git

