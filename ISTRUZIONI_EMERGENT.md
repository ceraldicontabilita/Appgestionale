# Istruzioni per Emergent · Integrazione Ceraldi Mobile nel backend `gestionale2`

> **Destinatario**: agente Emergent E-2 operante sul repo `ceraldicontabilita/gestionale2`.
> **Obiettivo**: abilitare l'accesso PIN della mini-app mobile `Appgestionale` alle API di `gestionale2`.
> **Autore richiesta**: Enzo Ceraldi (titolare).

## Contesto

È stato creato il repo `ceraldicontabilita/Appgestionale` con una mini-app mobile PIN-only (`index.html`) servita su GitHub Pages a `https://ceraldicontabilita.github.io/Appgestionale/`.

Per funzionare, la mini-app ha bisogno che `gestionale2` esponga un nuovo endpoint `/api/auth/pin-login` e che accetti richieste CORS dal dominio GitHub Pages.

I file sono già pronti nel repo `Appgestionale` e vanno integrati qui. **Tre modifiche**, tutte riportate sotto.

---

## Step 1 · Aggiungere il router PIN login

**Azione**: copiare il file `pin_login.py` dal repo `Appgestionale/backend/` in `gestionale2/app/routers/`.

Il file si trova a:
```
https://raw.githubusercontent.com/ceraldicontabilita/Appgestionale/main/backend/pin_login.py
```

Salvarlo come:
```
gestionale2/app/routers/pin_login.py
```

Il router espone:
- `POST /api/auth/pin-login` — riceve `{pin}`, se l'SHA-256 coincide con `72e0837603bda6733feca2c118417d031d2df2c9574373df26c76c28a2c9c0b4` (PIN 141574) genera un JWT admin
- `GET /api/auth/pin-login/health` — check diagnostico

Il router ha già al suo interno il rate-limit anti brute-force (8 tentativi per IP → lock 60 secondi), usa `settings.SECRET_KEY`/`settings.ALGORITHM`/`settings.ACCESS_TOKEN_EXPIRE_MINUTES` come l'`auth_service` esistente, e recupera l'utente admin dalla collection `users` cercando prima per `username="ceraldi"`, poi per `role="admin"`, poi qualsiasi `is_active=True`.

---

## Step 2 · Registrare il router in `router_registry.py`

**File da modificare**: `gestionale2/app/router_registry.py`

Nella funzione di registrazione router (quella che contiene `app.include_router(auth.router, ...)` o simile), aggiungere subito **dopo** la riga dell'`auth` principale:

```python
# ─── PIN Login mobile (Ceraldi Mobile / Appgestionale) ────────────────────
from app.routers import pin_login as pin_login_router
app.include_router(
    pin_login_router.router,
    prefix="/api/auth",
    tags=["Auth PIN"],
)
```

Così l'endpoint finale diventa `POST /api/auth/pin-login`.

---

## Step 3 · Aggiungere il dominio GitHub Pages al CORS

**File da modificare**: `gestionale2/app/config.py`

**Contesto**: oggi `config.py` definisce un metodo `get_cors_origins(self)` (intorno alla linea 173) che prende gli origins da env. Va esteso per includere sempre i domini della mini-app.

### Sostituire il metodo esistente

Cercare in `app/config.py` il metodo (dovrebbe essere qualcosa come):

```python
def get_cors_origins(self) -> list[str]:
    """Parse CORS origins from comma-separated string."""
    origins = self.CORS_ORIGINS or self.ALLOWED_ORIGINS or "*"
    if origins == "*":
        # CORS con credentials non permette wildcard
        if self.ALLOW_CREDENTIALS and self.FRONTEND_URL:
            import logging
            logging.getLogger(__name__).warning(
                "CORS: allow_credentials=True con origins=* non è valido. "
                f"Uso FRONTEND_URL: {self.FRONTEND_URL}"
            )
            return [self.FRONTEND_URL]
        return ["*"]
    return [origin.strip() for origin in origins.split(",") if origin.strip()]
```

E sostituirlo con:

```python
def get_cors_origins(self) -> list[str]:
    """Parse CORS origins from comma-separated string.

    Estesa per includere sempre i domini della mini-app Ceraldi Mobile
    (repo: ceraldicontabilita/Appgestionale), indipendentemente dal
    valore di CORS_ORIGINS nell'env.
    """
    # Domini sempre consentiti per la mini-app mobile Ceraldi
    CERALDI_MOBILE_ORIGINS = [
        "https://ceraldicontabilita.github.io",
        "https://impresasemplice.online",
        "http://localhost:3000",
        "http://localhost:8001",
    ]

    origins_str = self.CORS_ORIGINS or self.ALLOWED_ORIGINS or "*"

    if origins_str == "*":
        # CORS con credentials non permette wildcard → lista esplicita
        if self.ALLOW_CREDENTIALS:
            base = [self.FRONTEND_URL] if self.FRONTEND_URL else []
            merged = list(dict.fromkeys(base + CERALDI_MOBILE_ORIGINS))
            import logging
            logging.getLogger(__name__).warning(
                "CORS: allow_credentials=True con origins=* non è valido. "
                f"Uso lista esplicita: {merged}"
            )
            return merged
        return ["*"]

    # Lista esplicita da env → aggiungo i domini Ceraldi se mancanti
    origins = [o.strip() for o in origins_str.split(",") if o.strip()]
    for dom in CERALDI_MOBILE_ORIGINS:
        if dom not in origins:
            origins.append(dom)
    return origins
```

**Nessuna modifica a `app/main.py`** è necessaria: il middleware CORS già chiama `settings.get_cors_origins()`.

**Nessuna modifica al `.env`** è necessaria: la patch garantisce che i domini siano sempre inclusi anche se `CORS_ORIGINS=*`.

---

## Step 4 · Verifica post-deploy

Dopo che Emergent ha fatto il deploy, eseguire questi tre check.

### Check 1 · Router registrato

Aprire in browser:
```
https://impresasemplice.online/api/auth/pin-login/health
```

Risposta attesa:
```json
{
  "ok": true,
  "configured": true,
  "admin_username": "ceraldi",
  "token_expire_minutes": 1440
}
```

### Check 2 · PIN login funziona

Da terminale:
```bash
curl -X POST https://impresasemplice.online/api/auth/pin-login \
  -H "Content-Type: application/json" \
  -d '{"pin":"141574"}'
```

Risposta attesa:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "...",
  "email": "...",
  "role": "admin",
  "auth_method": "pin"
}
```

### Check 3 · CORS dal dominio GitHub Pages

Da terminale:
```bash
curl -I -X OPTIONS https://impresasemplice.online/api/auth/pin-login \
  -H "Origin: https://ceraldicontabilita.github.io" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type"
```

Nell'header di risposta deve comparire:
```
access-control-allow-origin: https://ceraldicontabilita.github.io
access-control-allow-credentials: true
```

Se tutti e tre i check passano, la mini-app mobile `https://ceraldicontabilita.github.io/Appgestionale/` funzionerà correttamente al primo accesso.

---

## Riepilogo file toccati

| File | Azione |
|---|---|
| `gestionale2/app/routers/pin_login.py` | **NUOVO** — copiare da `Appgestionale/backend/pin_login.py` |
| `gestionale2/app/router_registry.py` | Aggiungere registrazione del router (Step 2) |
| `gestionale2/app/config.py` | Sostituire metodo `get_cors_origins` (Step 3) |

Nessuna modifica a `main.py`, `.env`, dipendenze Python (tutte le import del router sono già disponibili: `jose`, `bcrypt` vengono già usati da `auth_service.py`).

---

*Documento chat-8 Ceraldi ERP · generato per l'agente Emergent E-2*
