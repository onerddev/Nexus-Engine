"""
NexusEngine Omega v3.0 — Core Engines
Autor: Emanuel Felipe | github.com/onerddev

Módulos:
  BinaryProcessor   — 15 operações bit a bit em 64 bits
  MatrixEngine      — 10 tipos de matrizes + álgebra NumPy
  QuantumSimulator  — vetor de estado completo, 12 portas quânticas
  HashEngine        — 8 algoritmos criptográficos
  SortEngine        — 8 algoritmos de ordenação com telemetria
  PrimeEngine       — crivos, teste de primalidade, fatoração
  CompressionEngine — RLE e estatísticas de compressão
  FibEngine         — Fibonacci e sequências numéricas
  MetricsCollector  — latência real, CPU, memória
"""

import time, math, random, hashlib, threading, struct, statistics
from collections import deque
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime

import numpy as np


# ══════════════════════════════════════════════════════════════════════════════
#  1. BINARY PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════
class BinaryProcessor:
    M = 0xFFFFFFFFFFFFFFFF  # máscara 64 bits

    def xor(self,a,b):          return a^b
    def and_(self,a,b):         return a&b
    def or_(self,a,b):          return a|b
    def not_(self,a):           return a^self.M
    def nand(self,a,b):         return self.not_(self.and_(a,b))
    def nor(self,a,b):          return self.not_(self.or_(a,b))
    def xnor(self,a,b):         return self.not_(self.xor(a,b))
    def shl(self,a,n):          return (a<<(n%64))&self.M
    def shr(self,a,n):          return (a&self.M)>>(n%64)
    def rol(self,a,n):
        n%=64; return ((a<<n)|(a>>(64-n)))&self.M
    def ror(self,a,n):
        n%=64; return ((a>>n)|(a<<(64-n)))&self.M
    def popcount(self,a):       return bin(a&self.M).count('1')
    def parity(self,a):         return self.popcount(a)%2
    def reverse_bits(self,a):
        a&=self.M
        return int(f'{a:064b}'[::-1],2)
    def to_bin(self,v):         return bin(v&self.M)
    def to_hex(self,v):         return hex(v&self.M)
    def to_oct(self,v):         return oct(v&self.M)

    ALL_OPS = ["xor","and","or","not","nand","nor","xnor",
               "shl","shr","rol","ror","popcount","parity","reverse_bits"]

    def compute(self, op:str, a:int, b:int=0) -> Dict:
        t0=time.perf_counter()
        fn = {"xor":self.xor,"and":self.and_,"or":self.or_,"not":self.not_,
              "nand":self.nand,"nor":self.nor,"xnor":self.xnor,
              "shl":self.shl,"shr":self.shr,"rol":self.rol,"ror":self.ror,
              "popcount":self.popcount,"parity":self.parity,
              "reverse_bits":self.reverse_bits}.get(op)
        if not fn: return {"error":f"Operação inválida: {op}"}
        try:
            r = fn(a,b) if op not in ("not","popcount","parity","reverse_bits") else fn(a)
        except Exception as e:
            return {"error":str(e)}
        lat=(time.perf_counter()-t0)*1e6
        return {"result":r,"binary":self.to_bin(r),"hex":self.to_hex(r),
                "octal":self.to_oct(r),"popcount":self.popcount(r),"latency_us":round(lat,4)}


# ══════════════════════════════════════════════════════════════════════════════
#  2. MATRIX ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class MatrixEngine:
    def zeros(self,r,c):        return np.zeros((r,c))
    def ones(self,r,c):         return np.ones((r,c))
    def identity(self,n,_=None):return np.eye(n)
    def random_normal(self,r,c):return np.random.randn(r,c)
    def random_uniform(self,r,c):return np.random.uniform(0,1,(r,c))
    def diagonal(self,n,_=None):return np.diag(np.random.randn(n))
    def hilbert(self,n,_=None):
        i,j=np.meshgrid(np.arange(1,n+1),np.arange(1,n+1),indexing='ij')
        return 1.0/(i+j-1)
    def vandermonde(self,n,_=None):
        v=np.random.randn(n)
        return np.vander(v,n)
    def toeplitz(self,n,_=None):
        c=np.random.randn(n)
        from numpy.linalg import toeplitz as _t
        try:
            from scipy.linalg import toeplitz as _t2
            return _t2(c)
        except:
            mat=np.zeros((n,n))
            for i in range(n):
                for j in range(n):
                    mat[i,j]=c[abs(i-j)]
            return mat
    def magic(self,n,_=None):
        if n<3: n=3
        mat=np.zeros((n,n),dtype=float)
        i,j=0,n//2
        for k in range(1,n*n+1):
            mat[i,j]=k
            ni,nj=(i-1)%n,(j+1)%n
            if mat[ni,nj]: i=(i+1)%n
            else: i,j=ni,nj
        return mat

    ALL_OPS=["zeros","ones","identity","random_normal","random_uniform",
             "diagonal","hilbert","vandermonde","toeplitz","magic"]

    def _analyze(self, m:np.ndarray) -> Dict:
        out={}
        try: out["det"]=round(float(np.linalg.det(m)),8)
        except: pass
        try: out["trace"]=round(float(np.trace(m)),8)
        except: pass
        try: out["rank"]=int(np.linalg.matrix_rank(m))
        except: pass
        try: out["norm_fro"]=round(float(np.linalg.norm(m,'fro')),8)
        except: pass
        try: out["cond"]=round(float(np.linalg.cond(m)),4)
        except: pass
        return out

    def compute(self, op:str, rows:int, cols:int) -> Dict:
        t0=time.perf_counter()
        fn={"zeros":self.zeros,"ones":self.ones,"identity":self.identity,
            "random_normal":self.random_normal,"random_uniform":self.random_uniform,
            "diagonal":self.diagonal,"hilbert":self.hilbert,
            "vandermonde":self.vandermonde,"toeplitz":self.toeplitz,
            "magic":self.magic}.get(op)
        if not fn: return {"error":f"Operação inválida: {op}"}
        try: m=fn(rows,cols)
        except Exception as e: return {"error":str(e)}
        lat=(time.perf_counter()-t0)*1e6
        r,c=m.shape
        sr,sc=min(3,r),min(3,c)
        sample=[[round(float(m[i,j]),6) for j in range(sc)] for i in range(sr)]
        stats={"min":round(float(m.min()),6),"max":round(float(m.max()),6),
               "mean":round(float(m.mean()),6),"std":round(float(m.std()),6),
               "sum":round(float(m.sum()),6)}
        result={"operation":op,"rows":r,"cols":c,"sample":sample,
                "stats":stats,"latency_us":round(lat,4)}
        if r==c and r<=500: result.update(self._analyze(m))
        return result

    def multiply(self, a_data:List, b_data:List) -> Dict:
        t0=time.perf_counter()
        try:
            A=np.array(a_data); B=np.array(b_data)
            C=A@B
            lat=(time.perf_counter()-t0)*1e6
            r,c=C.shape
            sr,sc=min(4,r),min(4,c)
            sample=[[round(float(C[i,j]),6) for j in range(sc)] for i in range(sr)]
            return {"shape":[r,c],"sample":sample,"latency_us":round(lat,4)}
        except Exception as e: return {"error":str(e)}

    def solve(self, a_data:List, b_data:List) -> Dict:
        """Resolve sistema linear Ax = b"""
        t0=time.perf_counter()
        try:
            A=np.array(a_data,dtype=float); b=np.array(b_data,dtype=float)
            x=np.linalg.solve(A,b)
            lat=(time.perf_counter()-t0)*1e6
            return {"solution":[round(float(v),8) for v in x],"latency_us":round(lat,4)}
        except Exception as e: return {"error":str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  3. QUANTUM SIMULATOR
# ══════════════════════════════════════════════════════════════════════════════
class QuantumSimulator:
    """Simulador de vetor de estado para até 18 qubits."""
    def __init__(self, n:int):
        if n>18: raise ValueError("Máximo 18 qubits")
        self.n=n; self.dim=1<<n
        self.state=np.zeros(self.dim,dtype=complex); self.state[0]=1.0

    def _apply(self, q:int, G:np.ndarray):
        for i in range(self.dim):
            if not(i>>q&1):
                j=i|(1<<q); a,b=self.state[i],self.state[j]
                self.state[i]=G[0,0]*a+G[0,1]*b
                self.state[j]=G[1,0]*a+G[1,1]*b

    # Inicializações
    def init_ground(self):      self.state[:]=0; self.state[0]=1.0
    def init_superposition(self): self.state[:]=1/math.sqrt(self.dim)
    def init_random(self):
        r=np.random.randn(self.dim)+1j*np.random.randn(self.dim)
        self.state=r/np.linalg.norm(r)
    def init_bell(self):
        self.state[:]=0
        self.state[0]=1/math.sqrt(2); self.state[self.dim-1]=1/math.sqrt(2)
    def init_ghz(self):
        self.state[:]=0
        self.state[0]=1/math.sqrt(2); self.state[-1]=1/math.sqrt(2)

    # Portas de 1 qubit
    def H(self,q):  self._apply(q,np.array([[1,1],[1,-1]])/math.sqrt(2))
    def X(self,q):  self._apply(q,np.array([[0,1],[1,0]],dtype=complex))
    def Y(self,q):  self._apply(q,np.array([[0,-1j],[1j,0]],dtype=complex))
    def Z(self,q):  self._apply(q,np.array([[1,0],[0,-1]],dtype=complex))
    def S(self,q):  self._apply(q,np.array([[1,0],[0,1j]],dtype=complex))
    def T(self,q):  self._apply(q,np.array([[1,0],[0,np.exp(1j*math.pi/4)]],dtype=complex))
    def Sdg(self,q):self._apply(q,np.array([[1,0],[0,-1j]],dtype=complex))
    def Rx(self,q,t):c,s=math.cos(t/2),math.sin(t/2); self._apply(q,np.array([[c,-1j*s],[-1j*s,c]],dtype=complex))
    def Ry(self,q,t):c,s=math.cos(t/2),math.sin(t/2); self._apply(q,np.array([[c,-s],[s,c]],dtype=complex))
    def Rz(self,q,t):self._apply(q,np.array([[np.exp(-1j*t/2),0],[0,np.exp(1j*t/2)]],dtype=complex))

    # Portas de 2 qubits
    def CNOT(self,ctrl,tgt):
        for i in range(self.dim):
            if(i>>ctrl&1) and not(i>>tgt&1):
                j=i|(1<<tgt); self.state[i],self.state[j]=self.state[j].copy(),self.state[i].copy()
    def CZ(self,ctrl,tgt):
        for i in range(self.dim):
            if(i>>ctrl&1) and(i>>tgt&1): self.state[i]*=-1
    def SWAP(self,q1,q2):
        self.CNOT(q1,q2); self.CNOT(q2,q1); self.CNOT(q1,q2)

    # Medição
    def prob_zero(self,q): return float(sum(abs(self.state[i])**2 for i in range(self.dim) if not(i>>q&1)))
    def prob_one(self,q):  return 1-self.prob_zero(q)
    def measure(self,q):
        p1=self.prob_one(q); r=1 if random.random()<p1 else 0
        for i in range(self.dim):
            if(i>>q&1)!=r: self.state[i]=0
        n=np.linalg.norm(self.state); 
        if n>0: self.state/=n
        return r
    def entropy(self):
        p=np.abs(self.state)**2; p=p[p>0]
        return float(-np.sum(p*np.log2(p)))
    def fidelity(self,other:'QuantumSimulator'):
        return float(abs(np.dot(self.state.conj(),other.state))**2)

    def probabilities(self,max_q=8):
        return [{"qubit":i,"p0":round(self.prob_zero(i),8),"p1":round(self.prob_one(i),8)}
                for i in range(min(self.n,max_q))]

    def statevector(self,max_s=32):
        out=[]
        for i in range(min(self.dim,max_s)):
            amp=self.state[i]; p=abs(amp)**2
            if p>1e-12:
                out.append({"state":f"|{i:0{self.n}b}⟩","re":round(amp.real,8),
                            "im":round(amp.imag,8),"prob":round(p,8)})
        return out


# ══════════════════════════════════════════════════════════════════════════════
#  4. HASH ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class HashEngine:
    ALGOS=["md5","sha1","sha224","sha256","sha384","sha512","sha3_256","sha3_512","blake2b","blake2s"]

    def hash(self, data:str, algo:str) -> Dict:
        if algo not in self.ALGOS: return {"error":f"Algo inválido. Use: {self.ALGOS}"}
        t0=time.perf_counter()
        raw=data.encode()
        h=hashlib.new(algo,raw).hexdigest()
        lat=(time.perf_counter()-t0)*1e6
        return {"algorithm":algo,"input_length":len(raw),"digest":h,
                "bits":len(h)*4,"latency_us":round(lat,4)}

    def hash_all(self, data:str) -> Dict:
        return {a:hashlib.new(a,data.encode()).hexdigest() for a in self.ALGOS}

    def verify(self, data:str, expected:str, algo:str) -> Dict:
        result=self.hash(data,algo)
        if "error" in result: return result
        match=result["digest"].lower()==expected.lower()
        return {"match":match,"expected":expected,"got":result["digest"]}

    def hmac(self, key:str, data:str, algo:str="sha256") -> Dict:
        import hmac as _hmac
        t0=time.perf_counter()
        try:
            h=_hmac.new(key.encode(),data.encode(),algo)
            lat=(time.perf_counter()-t0)*1e6
            return {"algorithm":f"hmac-{algo}","digest":h.hexdigest(),"latency_us":round(lat,4)}
        except Exception as e: return {"error":str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  5. SORT ENGINE — 8 algoritmos com telemetria
# ══════════════════════════════════════════════════════════════════════════════
class SortEngine:
    def _bubble(self,a):
        a=a[:]; n=len(a); cmps=0
        for i in range(n):
            for j in range(n-i-1):
                cmps+=1
                if a[j]>a[j+1]: a[j],a[j+1]=a[j+1],a[j]
        return a,cmps
    def _insertion(self,a):
        a=a[:]; cmps=0
        for i in range(1,len(a)):
            k=a[i]; j=i-1
            while j>=0 and a[j]>k: cmps+=1; a[j+1]=a[j]; j-=1
            a[j+1]=k
        return a,cmps
    def _selection(self,a):
        a=a[:]; n=len(a); cmps=0
        for i in range(n):
            m=i
            for j in range(i+1,n): cmps+=1; m=j if a[j]<a[m] else m
            a[i],a[m]=a[m],a[i]
        return a,cmps
    def _merge_sort(self,a):
        cmps=[0]
        def ms(arr):
            if len(arr)<=1: return arr
            mid=len(arr)//2
            L,R=ms(arr[:mid]),ms(arr[mid:])
            out=[]; i=j=0
            while i<len(L) and j<len(R):
                cmps[0]+=1
                if L[i]<=R[j]: out.append(L[i]); i+=1
                else: out.append(R[j]); j+=1
            return out+L[i:]+R[j:]
        return ms(a[:]),cmps[0]
    def _quick_sort(self,a):
        cmps=[0]
        def qs(arr):
            if len(arr)<=1: return arr
            p=arr[len(arr)//2]; L=[]; M=[]; R=[]
            for x in arr:
                cmps[0]+=1
                if x<p: L.append(x)
                elif x==p: M.append(x)
                else: R.append(x)
            return qs(L)+M+qs(R)
        return qs(a[:]),cmps[0]
    def _heap_sort(self,a):
        import heapq; cmps=[0]
        h=a[:]
        heapq.heapify(h)
        return [heapq.heappop(h) for _ in range(len(h))],len(a)
    def _shell_sort(self,a):
        a=a[:]; n=len(a); gap=n//2; cmps=0
        while gap>0:
            for i in range(gap,n):
                tmp=a[i]; j=i
                while j>=gap and a[j-gap]>tmp: cmps+=1; a[j]=a[j-gap]; j-=gap
                a[j]=tmp
            gap//=2
        return a,cmps
    def _counting_sort(self,a):
        if not a: return [],0
        mn,mx=min(a),max(a)
        count=[0]*(mx-mn+1)
        for x in a: count[x-mn]+=1
        out=[]
        for i,c in enumerate(count): out.extend([i+mn]*c)
        return out,len(a)

    ALL_ALGOS=["bubble","insertion","selection","merge","quick","heap","shell","counting"]

    def sort(self, data:List[float], algorithm:str) -> Dict:
        t0=time.perf_counter()
        fn={"bubble":self._bubble,"insertion":self._insertion,
            "selection":self._selection,"merge":self._merge_sort,
            "quick":self._quick_sort,"heap":self._heap_sort,
            "shell":self._shell_sort,"counting":self._counting_sort}.get(algorithm)
        if not fn: return {"error":f"Algoritmo inválido. Use: {self.ALL_ALGOS}"}
        try:
            inp=[int(x) for x in data]
            sorted_data,comparisons=fn(inp)
        except Exception as e: return {"error":str(e)}
        lat=(time.perf_counter()-t0)*1e6
        return {"algorithm":algorithm,"input_size":len(data),
                "sorted":sorted_data[:50],"comparisons":comparisons,
                "latency_us":round(lat,4),
                "is_sorted":sorted_data==sorted(sorted_data)}

    def benchmark(self, data:List[float]) -> Dict:
        """Compara todos os algoritmos no mesmo dataset."""
        results={}
        for algo in self.ALL_ALGOS:
            r=self.sort(data,algo)
            if "error" not in r:
                results[algo]={"comparisons":r["comparisons"],"latency_us":r["latency_us"]}
        fastest=min(results,key=lambda k:results[k]["latency_us"])
        return {"input_size":len(data),"results":results,"fastest":fastest}


# ══════════════════════════════════════════════════════════════════════════════
#  6. PRIME ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class PrimeEngine:
    def is_prime(self,n:int)->bool:
        if n<2: return False
        if n<4: return True
        if n%2==0 or n%3==0: return False
        i=5
        while i*i<=n:
            if n%i==0 or n%(i+2)==0: return False
            i+=6
        return True

    def sieve(self,limit:int)->List[int]:
        if limit<2: return []
        sieve=[True]*(limit+1); sieve[0]=sieve[1]=False
        for i in range(2,int(limit**.5)+1):
            if sieve[i]:
                for j in range(i*i,limit+1,i): sieve[j]=False
        return [i for i in range(2,limit+1) if sieve[i]]

    def factorize(self,n:int)->Dict:
        if n<2: return {"factors":[],"is_prime":False}
        factors=[]; d=2
        while d*d<=n:
            while n%d==0: factors.append(d); n//=d
            d+=1
        if n>1: factors.append(n)
        from collections import Counter
        counts=dict(Counter(factors))
        return {"factors":factors,"factorization":counts,"is_prime":len(factors)==1}

    def goldbach(self,n:int)->Dict:
        """Conjectura de Goldbach: n par = soma de 2 primos."""
        if n<4 or n%2!=0: return {"error":"n deve ser um número par >= 4"}
        primes=set(self.sieve(n))
        pairs=[]
        for p in range(2,n//2+1):
            if p in primes and(n-p) in primes:
                pairs.append([p,n-p])
                if len(pairs)>=5: break
        return {"n":n,"pairs":pairs,"total_pairs":len(pairs)}

    def nth_prime(self,n:int)->int:
        if n<1: return 2
        count=0; num=1
        while count<n:
            num+=1
            if self.is_prime(num): count+=1
        return num

    def compute(self, op:str, n:int, limit:int=1000) -> Dict:
        t0=time.perf_counter()
        ops={"is_prime": lambda:{"n":n,"is_prime":self.is_prime(n)},
             "sieve":    lambda:{"limit":limit,"primes":self.sieve(min(limit,100000)),"count":len(self.sieve(min(limit,100000)))},
             "factorize":lambda:self.factorize(n),
             "goldbach": lambda:self.goldbach(n),
             "nth_prime":lambda:{"n":n,"prime":self.nth_prime(min(n,10000))}}
        fn=ops.get(op)
        if not fn: return {"error":f"Operação inválida. Use: {list(ops)}"}
        result=fn()
        result["latency_us"]=round((time.perf_counter()-t0)*1e6,4)
        return result


# ══════════════════════════════════════════════════════════════════════════════
#  7. SEQUENCE ENGINE (Fibonacci, Collatz, etc.)
# ══════════════════════════════════════════════════════════════════════════════
class SequenceEngine:
    def fibonacci(self,n:int)->Dict:
        if n>10000: n=10000
        seq=[0,1]
        for i in range(2,n): seq.append(seq[-1]+seq[-2])
        return {"n":n,"sequence":seq[:min(50,n)],"last":seq[n-1],"golden_ratio":round(seq[-1]/seq[-2],10) if n>1 else None}

    def collatz(self,n:int)->Dict:
        if n<1: return {"error":"n deve ser >= 1"}
        seq=[n]; steps=0
        while n!=1:
            n=n//2 if n%2==0 else 3*n+1
            seq.append(n); steps+=1
            if steps>100000: break
        return {"start":seq[0],"steps":steps,"max_value":max(seq),"sequence":seq[:100]}

    def pascal(self,rows:int)->Dict:
        rows=min(rows,20)
        triangle=[[1]]
        for i in range(1,rows):
            row=[1]
            for j in range(1,i): row.append(triangle[i-1][j-1]+triangle[i-1][j])
            row.append(1); triangle.append(row)
        return {"rows":rows,"triangle":triangle}

    def lucas(self,n:int)->Dict:
        n=min(n,10000)
        seq=[2,1]
        for i in range(2,n): seq.append(seq[-1]+seq[-2])
        return {"n":n,"sequence":seq[:min(50,n)],"last":seq[n-1]}

    def tribonacci(self,n:int)->Dict:
        n=min(n,5000)
        seq=[0,0,1]
        for i in range(3,n): seq.append(seq[-1]+seq[-2]+seq[-3])
        return {"n":n,"sequence":seq[:min(50,n)],"last":seq[n-1]}

    def compute(self,op:str,n:int)->Dict:
        t0=time.perf_counter()
        ops={"fibonacci":self.fibonacci,"collatz":self.collatz,
             "pascal":self.pascal,"lucas":self.lucas,"tribonacci":self.tribonacci}
        fn=ops.get(op)
        if not fn: return {"error":f"Operação inválida. Use: {list(ops)}"}
        result=fn(n)
        result["latency_us"]=round((time.perf_counter()-t0)*1e6,4)
        return result


# ══════════════════════════════════════════════════════════════════════════════
#  8. STATISTICS ENGINE
# ══════════════════════════════════════════════════════════════════════════════
class StatsEngine:
    def analyze(self, data:List[float]) -> Dict:
        if not data: return {"error":"Lista vazia"}
        t0=time.perf_counter()
        arr=np.array(data,dtype=float)
        n=len(arr)
        sl=sorted(data)
        def pct(p): return float(np.percentile(arr,p))
        result={
            "count":n,"min":round(float(arr.min()),8),"max":round(float(arr.max()),8),
            "mean":round(float(arr.mean()),8),"median":round(float(np.median(arr)),8),
            "std":round(float(arr.std()),8),"variance":round(float(arr.var()),8),
            "sum":round(float(arr.sum()),8),"range":round(float(arr.max()-arr.min()),8),
            "percentiles":{"p25":round(pct(25),8),"p50":round(pct(50),8),
                           "p75":round(pct(75),8),"p90":round(pct(90),8),"p99":round(pct(99),8)},
            "skewness":round(float(((arr-arr.mean())**3).mean()/arr.std()**3) if arr.std()>0 else 0,6),
            "kurtosis":round(float(((arr-arr.mean())**4).mean()/arr.std()**4-3) if arr.std()>0 else 0,6),
        }
        result["latency_us"]=round((time.perf_counter()-t0)*1e6,4)
        return result

    def correlation(self, x:List[float], y:List[float]) -> Dict:
        if len(x)!=len(y): return {"error":"Listas devem ter o mesmo tamanho"}
        arr_x=np.array(x); arr_y=np.array(y)
        r=float(np.corrcoef(arr_x,arr_y)[0,1])
        return {"pearson_r":round(r,8),"r_squared":round(r**2,8),
                "interpretation":"forte" if abs(r)>.7 else "moderada" if abs(r)>.4 else "fraca"}

    def histogram(self, data:List[float], bins:int=10) -> Dict:
        arr=np.array(data)
        counts,edges=np.histogram(arr,bins=bins)
        return {"bins":[{"from":round(float(edges[i]),4),"to":round(float(edges[i+1]),4),
                         "count":int(counts[i])} for i in range(len(counts))]}


# ══════════════════════════════════════════════════════════════════════════════
#  9. METRICS COLLECTOR
# ══════════════════════════════════════════════════════════════════════════════
class MetricsCollector:
    def __init__(self):
        self.t0=time.time(); self._lock=threading.Lock()
        self._ops=0; self._errors=0
        self._lats:deque=deque(maxlen=50000)
        self._by_module:Dict[str,int]={}

    def record(self,lat:float,success:bool=True,module:str=""):
        with self._lock:
            self._ops+=1
            if not success: self._errors+=1
            self._lats.append(lat)
            if module: self._by_module[module]=self._by_module.get(module,0)+1

    def snapshot(self)->Dict:
        with self._lock: lats=list(self._lats); ops=self._ops; err=self._errors; by_m=dict(self._by_module)
        uptime=max(1,time.time()-self.t0)
        cpu=mem=0
        try:
            import psutil,os
            p=psutil.Process(os.getpid()); cpu=p.cpu_percent(); mem=p.memory_info().rss
        except: pass
        if not lats:
            zero={"p50":0,"p95":0,"p99":0,"p999":0,"mean":0,"min":0,"max":0}
            return {"total_operations":0,"total_errors":0,"error_rate":0.0,"latency_us":zero,
                    "throughput_ops_sec":0.0,"by_module":by_m,"cpu_percent":cpu,
                    "memory_bytes":mem,"uptime_seconds":int(uptime)}
        sl=sorted(lats); n=len(sl)
        def p(pct): return round(sl[min(int(n*pct),n-1)],4)
        return {"total_operations":ops,"total_errors":err,
                "error_rate":round(err/ops,6) if ops else 0.0,
                "latency_us":{"p50":p(.5),"p95":p(.95),"p99":p(.99),"p999":sl[-1],
                              "mean":round(sum(lats)/n,4),"min":round(sl[0],4),"max":round(sl[-1],4)},
                "throughput_ops_sec":round(ops/uptime,2),
                "by_module":by_m,"cpu_percent":round(cpu,2),
                "memory_bytes":mem,"uptime_seconds":int(uptime)}
