# Nexus-Engine
# 1. Extrai
Expand-Archive "C:\Users\Anatalia\Downloads\NexusEngine-fixed.zip" -DestinationPath "C:\Users\Anatalia\Downloads\NexusFixed" -Force

# 2. Entra na pasta correta
cd C:\Users\Anatalia\Downloads\NexusFixed\NexusEngine

# 3. Roda
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
