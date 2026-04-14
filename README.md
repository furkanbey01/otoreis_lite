# otoreis_lite

Basit ama çalışan bir **otonom bilgisayar ajanı MVP**.

- Python 3.12 + FastAPI backend
- Playwright ile browser automation
- SQLite ile task/state/log yönetimi
- MCP remote server iskeleti (`/mcp/tools`, `/mcp/call`)
- Basit web dashboard (`/api/dashboard`)
- Approval/policy katmanı

## 1) Kısa Mimari Özeti

Bu MVP aşağıdaki modüllerle çalışır:

1. **Orchestrator**
   - Görev yaşam döngüsünü yönetir (queued/running/waiting_approval/completed/failed/cancelled).
   - Bounded loop, timeout, retry ve cancellation uygular.

2. **Planner**
   - Kullanıcı explicit step vermezse küçük bir deterministic plan üretir.
   - Token maliyetini düşürmek için kısa plan üretimi yapar.

3. **Executor**
   - Action’ları BrowserTool / FilesystemTool üzerinden çalıştırır.
   - Adım bazlı timeout + retry uygular.

4. **Tools**
   - `browser_tool.py`: navigate, click, type, scroll, extract_text, press
   - `filesystem_tool.py`: read/write/save_json/delete (delete policy ile kontrol edilir)

5. **Memory/State Manager**
   - SQLite üzerinde kısa durum özeti, current step, logs, pending approval saklar.
   - Kısa ve makine-okunur action log üretir.

6. **Policy/Approval**
   - Aşağıdaki action’lar onay olmadan çalışmaz:
     - `form_submit`, `login`, `send_mail`, `delete_file`, `purchase`, `system_change`

7. **MCP Integration Layer**
   - Remote MCP server skeleton:
     - `GET /mcp/tools`
     - `POST /mcp/call`
   - Tool’lar: `create_task`, `task_status`, `approve_task`, `cancel_task`

## 2) Repo Yapısı

```text
otoreis_lite/
├─ app/
│  ├─ api/
│  │  └─ routes.py
│  ├─ core/
│  │  └─ db.py
│  ├─ mcp/
│  │  └─ routes.py
│  ├─ models/
│  │  └─ schemas.py
│  ├─ services/
│  │  ├─ executor.py
│  │  ├─ orchestrator.py
│  │  ├─ planner.py
│  │  ├─ policy.py
│  │  └─ state_manager.py
│  ├─ tools/
│  │  ├─ browser_tool.py
│  │  └─ filesystem_tool.py
│  ├─ templates/
│  │  └─ dashboard.html
│  ├─ static/
│  │  ├─ dashboard.css
│  │  └─ dashboard.js
│  ├─ examples/
│  │  └─ sample_tasks.json
│  ├─ config.py
│  └─ main.py
├─ scripts/
│  └─ run_sample_task.sh
├─ .env.example
├─ Dockerfile
├─ docker-compose.yml
├─ pyproject.toml
└─ README.md
```

## 3) Uygulama Planı (MVP)

1. FastAPI + SQLite temelini ayağa kaldır.
2. Orchestrator/Planner/Executor katmanlarını ekle.
3. Browser + filesystem tool’ları entegre et.
4. Policy/onay ve task durum geçişlerini ekle.
5. MCP server skeleton endpoint’lerini ekle.
6. Basit dashboard ile task başlatma/izleme yap.
7. Docker + örnek task + dokümantasyon tamamla.

---

## Hızlı Kurulum (En Kolay Yol: Docker)

### 1) Gerekenler
- Docker + Docker Compose

### 2) Çalıştır
```bash
docker compose up --build
```

### 3) Aç
- API docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8000/api/dashboard`
- MCP tools: `http://localhost:8000/mcp/tools`

> Veriler host makinede `./data` ve `./workspace` klasörlerine yazılır.

---

## Lokal Kurulum (Python ile)

### 1) Gerekenler
- Python 3.12
- `pip`

### 2) Ortamı hazırla
```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
playwright install chromium
```

### 3) Konfigürasyon
```bash
cp .env.example .env
```

Varsayılan `.env` değerleri:

```env
HOST=0.0.0.0
PORT=8000
DB_PATH=./data/agent.db
WORKSPACE_DIR=./workspace
PLAYWRIGHT_HEADLESS=true
DEFAULT_TIMEOUT_SEC=20
MAX_STEPS=20
MAX_RETRIES=1
```

### 4) Uygulamayı başlat
```bash
uvicorn app.main:app --reload
```

### 5) Doğrula
```bash
curl http://localhost:8000/health
```

Beklenen çıktı:
```json
{"ok": true}
```

---

## Ayarlar Ne İşe Yarıyor?

- `HOST`, `PORT`: API’nin bağlanacağı adres/port.
- `DB_PATH`: SQLite dosyasının yolu.
- `WORKSPACE_DIR`: Ajanın dosya yazacağı güvenli klasör.
- `PLAYWRIGHT_HEADLESS`: `true` ise görünmez tarayıcı, `false` ise görünür.
- `DEFAULT_TIMEOUT_SEC`: Adım başına timeout.
- `MAX_STEPS`: Bir görevde en fazla adım sayısı (bounded loop).
- `MAX_RETRIES`: Başarısız adım için retry sayısı.

---

## İlk Görevini Gönder (Test)

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{
    "goal": "Open wikipedia and search for Artificial intelligence",
    "steps": [
      {"type": "navigate", "args": {"url": "https://www.wikipedia.org"}},
      {"type": "type", "args": {"selector": "input#searchInput", "text": "Artificial intelligence"}},
      {"type": "click", "args": {"selector": "button[type=\"submit\"]"}},
      {"type": "extract_text", "args": {"selector": "#firstHeading"}},
      {"type": "save_json", "args": {"path": "results/ai_heading.json"}}
    ]
  }'
```

Task durumu:
```bash
curl http://localhost:8000/api/tasks/1
```

Çıktı dosyası:
- `./workspace/results/ai_heading.json`

---

## ChatGPT / MCP Entegrasyonu (MVP Skeleton)

Tool listesini al:
```bash
curl http://localhost:8000/mcp/tools
```

Tool çağır:
```bash
curl -X POST http://localhost:8000/mcp/call \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "create_task",
    "arguments": {"goal": "Open example.com and extract h1"}
  }'
```

---

## Sorun Giderme

1. **`ModuleNotFoundError` alıyorum**
   - `.venv` aktif mi kontrol et.
   - `pip install -e .` komutunu tekrar çalıştır.

2. **Playwright browser bulunamadı**
   - `playwright install chromium` çalıştır.

3. **Port dolu (`8000`)**
   - `.env` içinde `PORT=8010` gibi değiştir veya
   - `uvicorn ... --port 8010` ile başlat.

4. **Docker’da permission sorunu**
   - `./data` ve `./workspace` klasörlerinin yazılabilir olduğundan emin ol.

---

## Token Verimliliği İçin Uygulananlar

- Kısa durum özeti (`summary`) ve step indeksleri saklanır.
- Structured action/log JSON tutulur.
- Eski tam context tekrar modele taşınmaz (DB state + compact logs).
- Screenshot zorunlu değil; varsayılan akışta kapalı.
- Planner deterministic ve kısa.

## Notlar

- Desktop GUI kontrolü bu sürümde adapter düzeyinde tasarlandı, gerçek implementasyon browser’a odaklı.
- Production için auth, tenant isolation, sandbox hardening ve rate-limit eklenmelidir.
