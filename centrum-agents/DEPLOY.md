# Centrum — Deploy en DGX Spark

## Secuencia completa (primera vez)

### 1. Descargar modelos Gemma 4 (una sola vez)
```bash
pip install huggingface_hub
huggingface-cli login   # token de HuggingFace con acceso a Gemma

huggingface-cli download google/gemma-4-E4B-it
huggingface-cli download google/gemma-4-26B-A4B-it
huggingface-cli download google/gemma-4-31B-it
```

### 2. Instalar vLLM
```bash
pip install vllm bitsandbytes
```

### 3. Arrancar los 3 servidores vLLM
```bash
bash /root/centrum-agents/vllm-start.sh
```
Espera hasta ver los 3 puertos `[OK]`. La primera vez tarda más (carga modelos).

### 4. Transferir los agentes desde Windows al DGX Spark
Desde PowerShell en el PC de Lucas:
```powershell
scp -r "C:\Users\Pc2025\Desktop\ANTIGRAVITY\centrum-agents\" root@<IP_DGX>:/tmp/
```

### 5. Desplegar los 98 agentes
```bash
ssh root@<IP_DGX>
bash /tmp/centrum-agents/setup-centrum.sh
```

El script:
- Verifica que los 3 puertos vLLM responden
- Crea `~/.openclaw/agents/<nombre>/` para cada agente
- Copia config desde plantilla `iris` y ajusta `model` + `base_url`
- Copia `IDENTITY.md` al workspace de cada agente
- Reinicia el gateway

---

## Puertos y tiers

| Tier | Modelo              | Puerto | Uso                                    | Agentes |
|------|---------------------|--------|----------------------------------------|---------|
| Nano | gemma-4-E4B-it      | 8001   | Tareas atómicas: envío, routing, logs  | ~30     |
| Pro  | gemma-4-26B-A4B-it  | 8002   | Coordinación, resúmenes, contexto      | ~45     |
| Max  | gemma-4-31B-it      | 8003   | Legal, análisis crítico, escritura     | ~23     |

Nano + Pro siempre cargados. Max on-demand con `vllm-load-max.sh`.

---

## Actualizar un agente (IDENTITY.md)

```bash
# Sólo sobreescribir el IDENTITY.md, no tocar el config
cp /tmp/centrum-agents/bloque-6/solution-matcher/IDENTITY.md \
   /root/.openclaw/workspace-solution-matcher/IDENTITY.md
```
No hace falta reiniciar el gateway.

---

## Verificar estado

```bash
# Ver los 3 servidores vLLM activos
for p in 8001 8002 8003; do
  echo "Puerto $p:"; curl -s http://localhost:$p/v1/models | python3 -c "import json,sys; d=json.load(sys.stdin); print(' ', d['data'][0]['id'])"
done

# Ver agentes OpenClaw registrados
ls /root/.openclaw/agents/ | wc -l   # debe ser 98 + los que ya había

# Test rápido de un agente
openclaw run lead-classifier "Tengo una deuda de 3 meses. Casa en Tarragona."
```

---

## Arranque automático al reiniciar

```bash
crontab -e
# Añadir:
@reboot sleep 30 && bash /root/centrum-agents/vllm-start.sh >> /var/log/vllm/autostart.log 2>&1
```
