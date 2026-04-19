# Chat 8 — Mini-app mobile per pagamenti e assegni (v2.1 · PIN-only)

## Cosa c'è in questo patch

```
claude-patches/chat-8-mobile-pagamenti/
├── index.html                ← mini-app mobile single-file (PIN-only)
├── backend/
│   └── pin_login.py          ← router FastAPI da aggiungere a gestionale2
└── ISTRUZIONI.md             ← questo file
```

Per funzionare servono **entrambi i pezzi**: il router `pin_login.py` va aggiunto al backend `gestionale2` (è quello che converte il PIN in JWT admin), e l'HTML va messo online dove raggiungerlo dal telefono.

## Come funziona

1. Apri l'app sul telefono → schermata PIN viola.
2. Digiti **`141574`** → l'app chiama `POST /api/auth/pin-login` con `{pin: "141574"}`.
3. Il backend verifica l'SHA-256 del PIN lato server, recupera l'utente admin dal DB, genera un JWT con la stessa logica del login normale, e lo restituisce.
4. Il JWT viene salvato in `localStorage` del telefono.
5. Da qui in poi ogni chiamata (fatture, assegni, ecc.) viaggia con quel JWT. Nessun username, nessuna password richiesta all'utente — solo il PIN.
6. Il JWT scade dopo ~1 mese (come il login normale): al primo 401 l'app torna alla schermata PIN e si ricomincia il ciclo.

**Niente più setup admin. Niente più `ADMIN_PASSWORD` da ricordare.**

---

## Deploy — Parte 1: BACKEND (`gestionale2`)

### A. Copiare il router nel repo

1. Scarica `backend/pin_login.py` da questo patch.
2. Copialo in `gestionale2/app/routers/pin_login.py`.

### B. Registrare il router

Aprire `gestionale2/app/router_registry.py` e aggiungere (dentro la funzione che monta i router, vicino all'altro `auth`):

```python
# ─── PIN Login mobile ──────────────────────────────────────────────────────
from app.routers import pin_login as pin_login_router
app.include_router(
    pin_login_router.router,
    prefix="/api/auth",
    tags=["Auth PIN"],
)
```

Il prefix è `/api/auth` quindi l'endpoint finale sarà `POST /api/auth/pin-login`.

### C. CORS (critico se frontend è su altro dominio)

Se la mini-app sarà servita da un dominio diverso (es. `ceraldicontabilita.github.io`), il middleware CORS in `app/main.py` deve permetterlo. Verifica che ci sia qualcosa del tipo:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ceraldicontabilita.github.io",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Se invece servi l'HTML direttamente da `impresasemplice.online/mobile/`, il CORS non serve (stesso dominio).

### D. Verifica che funzioni

Dopo il deploy, apri dal browser:

```
https://impresasemplice.online/api/auth/pin-login/health
```

Deve rispondere:
```json
{"ok": true, "configured": true, "admin_username": "ceraldi", "token_expire_minutes": 43200}
```

Poi testa il login PIN da curl/terminale:

```bash
curl -X POST https://impresasemplice.online/api/auth/pin-login \
  -H "Content-Type: application/json" \
  -d '{"pin":"141574"}'
```

Deve rispondere con un JSON contenente `access_token`. Se sì → backend OK.

---

## Deploy — Parte 2: FRONTEND (`index.html`)

Tre opzioni, in ordine di semplicità:

### 1. GitHub Pages su repo dedicato (consigliato)
```bash
# Nuovo repo suggerito: CeraldiMobile
git init && git add index.html
git commit -m "Ceraldi Mobile chat-8 v2.1 · PIN-only"
git branch -M main
git remote add origin https://github.com/ceraldicontabilita/CeraldiMobile.git
git push -u origin main
# poi su GitHub → Settings → Pages → Source: main / root
```
URL: `https://ceraldicontabilita.github.io/CeraldiMobile/`

### 2. Nuova pagina dentro `FattureCeraldiGroup`
Copia `index.html` come `mobile.html` nel repo esistente → `https://ceraldicontabilita.github.io/FattureCeraldiGroup/mobile.html`

### 3. Servito da `gestionale2` (bypassa CORS completamente)
Metti `index.html` in `backend/static/mobile/index.html` e aggiungi in `app/main.py`:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/mobile", StaticFiles(directory="backend/static/mobile", html=True), name="mobile")
```
URL: `https://impresasemplice.online/mobile/`

Una volta online, apri l'URL sul telefono e fai **"Aggiungi a schermata Home"** → diventa un'icona app.

---

## Sicurezza

### Cosa è protetto
- Il PIN **non è in chiaro nel codice HTML**: c'è solo il suo SHA-256.
- Il PIN **non è in chiaro nel backend**: c'è l'hash SHA-256 hardcoded in `pin_login.py`.
- Il JWT è firmato con la `SECRET_KEY` del backend, come per il login normale.
- Brute force: lato client lock 30s dopo 5 tentativi; lato server lock 60s dopo 8 tentativi per IP.
- In 401 il token viene cancellato dal telefono.

### Limiti
- Il PIN è a 6 cifre → 1M combinazioni. Con HTTPS + rate limit server-side è adeguato per un telefono personale, **non** per un sistema multi-utente pubblico.
- Chi ottiene accesso fisico al telefono sbloccato ha il JWT già salvato: usa sempre il lock schermo del telefono.
- Se il JWT venisse esfiltrato, resta valido fino a scadenza (~1 mese). In caso di furto telefono: su `gestionale2` cambia la `SECRET_KEY` → tutti i JWT in circolazione diventano invalidi.

### Cambiare il PIN
In `backend/pin_login.py` sostituisci `PIN_HASH_ADMIN` con il nuovo hash:
```bash
python3 -c "import hashlib; print(hashlib.sha256('NUOVO_PIN'.encode()).hexdigest())"
```
Stesso hash va aggiornato anche in `index.html` nella costante `PIN_HASH` (il check server-side è l'unico che conta davvero per la sicurezza; quello client-side serve solo per lo shake/blocco immediato).

---

## Endpoint usati dall'app

**Auth**
- `POST /api/auth/pin-login` body `{pin}` → JWT  ← **nuovo, in pin_login.py**
- `GET  /api/auth/pin-login/health` → stato router

**Fatture** (`app/routers/invoices/invoices_main.py`)
- `GET /api/invoices/unpaid?skip&limit`
- `GET /api/invoices/overdue?skip&limit`
- `GET /api/invoices/list?skip&limit`
- `GET /api/invoices/{id}`
- `POST /api/invoices/{id}/payment?amount=X&payment_method=Y`

**Assegni** (`app/routers/bank/assegni.py`)
- `GET /api/assegni?stato&search&skip&limit`
- `GET /api/assegni/stats`
- `GET /api/assegni/{id}`
- `PUT /api/assegni/{id}` body JSON
- `POST /api/assegni/genera` body `{numero_primo, quantita}`
- `POST /api/assegni/{id}/collega-fattura` body `{fattura_id}`
- `POST /api/assegni/{id}/emetti`
- `POST /api/assegni/{id}/incassa`
- `POST /api/assegni/{id}/annulla`

Tutti con header `Authorization: Bearer <jwt>` ottenuto dal PIN.

---

## Troubleshooting

| Problema | Causa probabile | Fix |
|---|---|---|
| PIN corretto ma "Errore: rete" | CORS non configurato | vedi sezione CORS, o servi da /mobile/ |
| HTTP 500 "Nessun utente admin configurato" | non esiste utente `ceraldi` nel DB users | cambia `PIN_ADMIN_USERNAME` in pin_login.py oppure crea l'utente admin |
| 404 su /api/auth/pin-login | router non registrato | verifica step B in router_registry.py |
| 429 troppi tentativi | rate limit server raggiunto | attendi 60s, controlla log backend |
| 401 su tutte le chiamate successive | SECRET_KEY cambiata o utente disabilitato | rifai PIN login |
| Fatture endpoint restituiscono 401 anche con JWT | `get_current_user` non accetta il payload | verifica che il JWT contenga `sub`, `email`, `role` |

---

## Design system rispettato

- Font: **Plus Jakarta Sans**
- Colori: primary `#5D29C7`, bg `#F0F4FA`, card `#FFFFFF`, sidebar `#1E1B4B`, success `#00B884`, warning `#FF9800`, danger `#F44336`, info `#2196F3`
- Card radius 16, badge radius 20, shadow viola
- Nessun Tailwind, nessun Shadcn, nessuna dipendenza JS esterna (solo Google Fonts)

---

## Roadmap

- PIN multi-operatore con verifica bcrypt contro `dipendenti.pin` (Pocci, Vespa, ecc. con permessi differenziati)
- Logging in `log_operatori` ad ogni `pin-login` riuscito
- OCR foto assegno → compilazione automatica (endpoint `/api/ocr-assegni` già esistente)
- Pagamento multiplo (un assegno per più fatture) via `/api/pagamenti`
- Push notification alla scadenza fatture
- Dark mode

---

*Chat 8 Ceraldi ERP · Nessun push su main: questa patch è da copiare manualmente nei repo scelti.*
