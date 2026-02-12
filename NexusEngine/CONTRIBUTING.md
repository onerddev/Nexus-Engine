# Contribuindo para o NexusEngine Omega

Contribuições são bem-vindas. Este guia explica como colaborar com o projeto de forma organizada e alinhada aos padrões técnicos.

---

## Código de Conduta

- Seja respeitoso e inclusivo
- Foque no código, não na pessoa
- Faça críticas construtivas
- Reporte problemas sensíveis de forma privada aos mantenedores

---

## Configuração do Ambiente de Desenvolvimento

### Clonando o Projeto

```bash
git clone https://github.com/nexusengine/nexus-omega.git
cd NexusEngine
```

### Ambiente Python

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Build do Core C++

```bash
mkdir cpp/build && cd cpp/build
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
cd ../..
```

### Build dos Bindings Cython

```bash
python setup.py build_ext --inplace
```

### Verificação

```bash
python -c "import nexus_engine; print('Setup concluído com sucesso')"
```

---

## Estrutura do Projeto

```
NexusEngine/
├── cpp/        # Core C++20
├── cython/     # Ponte Python-C++
├── python/     # Módulos Python
├── api/        # Aplicação FastAPI
├── sql/        # Schema do banco
├── tests/      # Testes
├── docs/       # Documentação
```

---

## Fluxo de Desenvolvimento

### 1. Criar Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/minha-feature
```

Hotfix:

```bash
git checkout main
git checkout -b hotfix/minha-correcao
```

---

### 2. Implementar Alterações

- Modificações Python em `python/`
- Modificações C++ em `cpp/src/`
- Rebuild do C++ se necessário:

```bash
cd cpp/build && make -j$(nproc)
```

---

### 3. Testes

```bash
pytest tests/ -v
pytest --cov=api --cov=python
python tests/benchmark.py
```

Requisitos:
- Cobertura mínima recomendada: 80%
- Testar casos normais e extremos
- Testes independentes

---

### 4. Qualidade de Código

```bash
black python/ api/ tests/
isort python/ api/ tests/
mypy python/ --ignore-missing-imports
flake8 python/ api/ --max-line-length=120
bandit -r python/ api/
```

---

### 5. Commit

Formato:

```
<tipo>: descrição curta

descrição detalhada (opcional)
```

Tipos:

- feat
- fix
- docs
- style
- refactor
- perf
- test
- build
- ci

Exemplo:

```
feat: implementar fila lock-free

Reduz latência e adiciona testes de performance.
Closes #42
```

---

### 6. Pull Request

1. Criar PR para `develop`
2. Descrever mudanças
3. Informar testes adicionados
4. Atualizar documentação se necessário
5. Aguardar CI e revisão

---

## Padrões de Código

### Python

- Utilizar type hints
- Usar f-strings
- Preferir pathlib
- Escrever docstrings completas

### C++

- Utilizar C++ moderno (C++20)
- Aplicar const corretamente
- Usar noexcept quando aplicável
- Nomes de variáveis claros

---

## Documentação

Ao adicionar funcionalidades:

- Atualizar `docs/`
- Atualizar `README.md` se necessário
- Atualizar docstrings
- Documentar mudanças arquiteturais relevantes

---

## Performance

Antes de submeter:

- Verificar regressões
- Adicionar benchmarks quando aplicável
- Documentar impactos de performance

Ferramentas:

```bash
python -m cProfile script.py
perf record ./nexus_engine
python tests/benchmark.py
```

---

## Estratégia de Branches

- `main` – produção
- `develop` – integração
- `feature/*` – novas funcionalidades
- `hotfix/*` – correções críticas

---

## Processo de Release

Versionamento: MAJOR.MINOR.PATCH

- MAJOR: mudanças incompatíveis
- MINOR: novas funcionalidades compatíveis
- PATCH: correções

Passos:

```bash
# Atualizar versão
# Atualizar CHANGELOG.md
git tag v1.0.0
git push --tags
python setup.py sdist bdist_wheel
twine upload dist/*
```

---

## Reportando Problemas

### Bug
- Sistema operacional
- Versão do Python
- Passos para reproduzir
- Logs e comportamento esperado

### Feature
- Caso de uso
- Proposta
- Alternativas consideradas

---

## Suporte

- Perguntas: GitHub Discussions
- Problemas: GitHub Issues
- Contato: team@nexusengine.dev

---

## Licença

Ao contribuir, você concorda que seu código será distribuído sob a licença MIT.

---

Agradecemos sua contribuição para o NexusEngine Omega.
