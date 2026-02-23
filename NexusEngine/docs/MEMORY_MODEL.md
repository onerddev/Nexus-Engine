# Modelo de Memória - Nexus Engine

**Autor**: Emanuel Felipe  
**Versão**: 1.0.0

---

## Visão Geral

Nexus Engine usa dois modelos de alocação:

1. **MemoryPool**: Pré-alocado, blocos fixos, O(n) search
2. **Std Allocator**: Dinâmico via `new`/`delete`

Para uso prático, considera-se tradeoff:
- **MemoryPool**: Previsível, zero fragmentação, melhor cache
- **Std Allocator**: Flexível, crescimento dinâmico

---

## MemoryPool

### Implementação

**Arquivo**: `cpp/src/memory_pool.cpp`

**Estrutura**:
```cpp
struct Block {
    uint8_t data[BLOCK_SIZE];
    std::atomic<bool> allocated{false};
};

class MemoryPool {
    std::vector<Block> blocks;
    std::mutex blocks_mutex;
    std::atomic<uint32_t> free_blocks;
};
```

### Lifecycle

#### 1. Inicialização

```cpp
MemoryPool pool(num_blocks, block_size);  // Pre-aloca blocks

// Internamente:
blocks_.resize(num_blocks);
free_blocks_ = num_blocks;
```

**Tempo**: O(n) alocação contígua  
**Memória**: N × block_size bytes  

#### 2. Alocação

```cpp
void* ptr = pool.allocate();

// Internamente:
1. Adquire std::lock_guard<std::mutex> lock(blocks_mutex);
2. Busca bloco com allocated == false (linear O(n))
3. Set allocated = true (atomicamente)
4. Return buffer.data();
5. Libera lock
```

**Latência**: O(n) em worst case (todos alocados)  
**Atomicity**: Flag protegida, sem double-allocate possível  

#### 3. Dealocação

```cpp
pool.deallocate(ptr);

// Internamente:
1. Valida se ptr está dentro do pool (bounds check)
2. Encontra qual bloco pertence ptr
3. Set allocated = false
4. Incrementa free_blocks
```

**Validação**: Rejeita ptr inválido, retorna erro  
**Idempotência**: Dealocate 2x na mesma ptr é safe (flag fica false)  

### Garantias de Thread-Safety

**Sem Data Race**:
```cpp
std::lock_guard<std::mutex> lock(blocks_mutex);
// ↓ Todas leituras/escritas no bloco protegidas
block.allocated.store(true, std::memory_order_release);
// ↑ Atomicamente
```

**Sem Double-Allocate**:
```
T1: Lê allocated=false, **está dentro mutex**
T2: Tenta ler allocated, **espera por T1**
T1: Seta allocated=true, libera mutex
T2: Lê allocated=true, não aloca
```

**Sem Use-After-Free**:
```cpp
ptr = pool.allocate();   // Retorna endereço no pool
// ...uso...
pool.deallocate(ptr);    // Marca como free
ptr = pool.allocate();   // Pode reaalocar mesmo endereço
```

### Performance Trade-offs

| Operação | Complexidade | Latência |
|----------|-------------|----------|
| Alocação | O(n) | 1-5 µs |
| Dealocação | O(1) | <1 µs |
| Fragmentação | 0% | - |
| Cache locality | Ótima | - |
| Previsibilidade | Alta | - |

**Con**: Busca linear é bottleneck com N > 10000.

### Quando é Bom

- Operações batch com tamanho conhecido
- Latência previsível é importante
- fragmentação é intolerável
- Tamanho de dados é homogêneo

### Quando É Ruim

- Objetos com tamanho variável
- Crescimento dinâmico necessário
- N blocksk muito grande (> 100k)

---

## Stdlib Allocator

### Quando Usado

Para estruturas que crescem dinamicamente:
```cpp
std::vector<Task> task_queue;  // Cresce conforme necessário
```

### Characteristics

| Aspecto | Behavior |
|--------|----------|
| Fragmentação | Presente (depende de padrão) |
| Latência | Variável |
| Cache locality | Ruim (pointers espalhados) |
| Pré-alocação | Não |
| Overhead | ~8-16 bytes/alocac |

---

## Ownership Model

### Responsabilidade em Cython/Python

```python
cdef class EngineWrapper:
    cdef CppEngine* engine
    
    def __cinit__(self):
        self.engine = new CppEngine()  # Python owns
    
    def __dealloc__(self):
        if self.engine is not NULL:
            del self.engine  # Python garbage collects
            self.engine = NULL
```

**Contrato**:
- **Python** cria via `__cinit__`
- **Python** destroi via `__dealloc__`
- **C++** nunca toca lifetime

### Shared Ownership via Future

```cpp
std::unique_ptr<Task> task = std::make_unique<BinaryTask>(a, b);
std::future<uint64_t> result = pool.submit(std::move(task));

// Later:
uint64_t answer = result.get();  // Bloqueia até pronto
```

**Ownership**: `Future` gerencia lifecycle do `Task`.

---

## Pinning Memória

Em embedded/real-time, considerar memory pinning:

```cpp
#include <sys/mlock.h>

uint8_t* buffer = allocated;
mlock(buffer, size);  // Lock na RAM física (não swap)

// Later:
munlock(buffer, size);
```

**Pro**: Latência garantida (sem page faults)  
**Con**: Requer privilégios, consome RAM

---

## Vazamento de Memória

### Detecção

**Valgrind**:
```bash
valgrind --leak-check=full ./program
# ✓ Detecta ptr não liberadas
```

**AddressSanitizer**:
```bash
g++ -fsanitize=address program.cpp
./a.out  # ✓ Detecta heap-use-after-free
```

### Debug

```cpp
MemoryPool pool(1000, 4096);

pool.allocate();
pool.allocate();
pool.allocate();
// Não dealocou 3 → leak visível em debug

pool.get_stats().free_blocks == 997  // ✓ Verifica
```

---

## Stack vs Heap

### Stack (Automático)

```cpp
void func() {
    uint64_t x = 42;           // Stack ✓ automático
    BinaryProcessor proc;      // Stack ✓ destrutor automático
    
    // Saiu do escopo → destruído automaticamente
}
```

**Pro**: Automático, previsível, rápido  
**Con**: Tamanho limitado (~8 MB)

### Heap (Manual)

```cpp
void func() {
    uint64_t* x = new uint64_t(42);  // Heap ✓ manual
    auto proc = new BinaryProcessor(); // Heap ✓ manual
    
    // ...uso...
    
    delete x;    // Manual ✓ necessário
    delete proc; // Manual ✓ necessário
    
    // Esquecer delete → leak
}
```

**Pro**: Tamanho ilimitado  
**Con**: Manual, fácil vazar

### Recomendação

Preferir **Stack** quando possível:
```cpp
// ✓ Good
BinaryProcessor proc;
uint64_t result = proc.xor_op(a, b);

// ✗ Bad
BinaryProcessor* proc = new BinaryProcessor();
uint64_t result = proc->xor_op(a, b);
delete proc;
```

---

## RAII (Resource Acquisition Is Initialization)

Padrão fundamental em C++:

```cpp
class FileHandle {
    FILE* file_;
public:
    FileHandle(const char* path) {
        file_ = fopen(path, "r");  // Acquire
    }
    ~FileHandle() {
        if (file_) fclose(file_);  // Release
    }
};

void function() {
    FileHandle file("data.txt");  // Acquire
    // ...use file...
}  // Destrutor chamado automaticamente → Release
```

**Vantagem**: Impossible vazar (destrutor sempre chamado).

**Nexus Engine**: CoreEngine, ThreadPool, MemoryPool usam RAII.

---

## Profiling Memória

### Massif (Valgrind)

```bash
valgrind --tool=massif ./program
ms_print massif.out.12345 > graph.txt
cat graph.txt  # Visualiza uso ao longo do tempo
```

### Google Sanitizers

```bash
g++ -fsanitize=address,leak,undefined program.cpp
./a.out
# ✓ Detecta leaks, use-after-free, overflow
```

### Manual

```cpp
MemoryPool pool(1000, 4096);
auto stats = pool.get_stats();
std::cout << "Max memory: " 
          << stats.free_blocks * 4096 
          << " bytes" << std::endl;
```

---

## Conclusão

Modelo de memória de Nexus Engine:
- **MemoryPool**: Pré-alocado, previsível, zero fragmentação
- **Stdlib**: Dinâmico, flexível, gerenciamento automático
- **RAII**: Automático cleanup via destrutores
- **Threads**: Mutex-protected access
- **Validação**: Bounds checking, nil checks

Trade-offs são conscientes e defensáveis.

---

**Emanuel Felipe**  
https://github.com/onerddev/Nexus-Engine.git

