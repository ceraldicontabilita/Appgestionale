# Ceraldi Mobile · Appgestionale

Mini-app mobile PIN-only per gestione pagamenti fatture e assegni da telefono.
Parla con l'API FastAPI di `gestionale2` (in produzione su `impresasemplice.online`).

## Componenti

- **`index.html`** — single-file mobile-first, da pubblicare su GitHub Pages o servire da `/mobile/` del backend
- **`backend/pin_login.py`** — router FastAPI da aggiungere a `gestionale2/app/routers/` per l'autenticazione via PIN

## Flusso d'accesso

1. Apri l'URL sul telefono (consigliato: "Aggiungi a schermata Home")
2. Digiti il PIN `141574` sul tastierino
3. L'app chiama `POST /api/auth/pin-login` → riceve JWT admin → entri

Nessun username, nessuna password. Il JWT resta valido ~1 mese, poi richiede nuovo PIN.

## Funzionalità

**Dashboard** · contatori fatture da pagare / scadute / assegni vuoti-emessi + azioni rapide

**Fatture** · lista filtrabile (Da pagare / Scadute / Tutte), ricerca, dettaglio, **registra pagamento** (importo + metodo)

**Assegni** · lista per stato (Vuoto / Compilato / Emesso / Incassato / Annullato), dettaglio con azioni contestuali: compilare, emettere, incassare, annullare, collegare a fattura, **generare blocchi nuovi**

## Deploy rapido

### Frontend
Opzione più semplice: **GitHub Pages**. Vai su Settings → Pages → Source: `main` / root. URL pubblico:
```
https://ceraldicontabilita.github.io/Appgestionale/
```

### Backend
Leggi `ISTRUZIONI.md` — servono 3 passi:
1. Copiare `backend/pin_login.py` in `gestionale2/app/routers/`
2. Registrare il router in `gestionale2/app/router_registry.py`
3. Configurare CORS in `gestionale2/app/main.py` per accettare `https://ceraldicontabilita.github.io`

## Documentazione completa

Tutto in `ISTRUZIONI.md`: deploy, sicurezza, troubleshooting, endpoint API utilizzati, cambio PIN, roadmap.

## Design system

Font **Plus Jakarta Sans**, palette viola Ceraldi (`#5D29C7` / `#1E1B4B`), card radius 16, badge radius 20, zero Tailwind, zero dipendenze JS esterne.

---

*Ceraldi Group SRL · P.IVA 04523831214 · chat-8 v2.1*
