# Ceraldi · Appgestionale (mobile)

App mobile PIN-only per gestire fatture, assegni, pagamenti, scadenze e personale da telefono. Client di sola UI: parla con il backend FastAPI di [`gestionale2`](https://github.com/ceraldicontabilita/gestionale2) già in produzione su `impresasemplice.online`.

**Live:** <https://ceraldicontabilita.github.io/Appgestionale/>

## Struttura

```
Appgestionale/
├── index.html          ← l'app (single-file, nessuna build)
├── README.md
└── .gitignore
```

Single-page HTML, zero dipendenze esterne (solo Google Fonts per Plus Jakarta Sans). GitHub Pages serve il file direttamente dalla root.

## Accesso

1. Apri l'URL dal telefono — consigliato "Aggiungi a schermata Home" per effetto app nativa
2. Digita il PIN (solo al primo accesso o dopo un "blocca")
3. L'app chiama `POST /api/auth/pin-login` → riceve un JWT admin → lo salva in `localStorage`
4. Finché il JWT è valido (circa 30 giorni) le riaperture dell'app **non richiedono più il PIN**
5. Alla scadenza del token o in caso di 401/403, l'app rimanda automaticamente alla schermata PIN

## Moduli (24)

- **Principale** · Dashboard, Costi Ricorrenti
- **Banca & Cassa** · Prima Nota Cassa, Prima Nota Banca, Provvisori, Corrispettivi, Coerenza POS
- **Ciclo Passivo** · Fatture Ricevute, Fornitori, Scadenze, Assegni, Partitario
- **Fiscale** · F24, IVA, Bilancio, Calendario Fiscale, Commercialista
- **Personale** · Dipendenti, Cedolini, Presenze
- **Altri** · Verbali/Noleggio, Mutui, Documenti/Inbox, Riconciliazione

## OCR fatture & assegni (AI)

Scansione di fatture e assegni tramite Claude API (`claude-sonnet-4-5`) chiamata direttamente dal browser. L'API key Anthropic va inserita una volta dalle Impostazioni e resta in `localStorage` del telefono.

Include un sistema di **correzioni apprese**: ogni volta che l'utente corregge un campo letto male, il diff viene inviato al backend (`/api/ocr-fatture/correzione`) e le scansioni successive usano quelle correzioni come contesto → la lettura migliora nel tempo.

## Deploy

Commit su `main` → GitHub Pages ridistribuisce in circa 1 minuto. Nessuna build, nessun step CI necessario.

## Design system

- Font: **Plus Jakarta Sans** (400→800)
- Primario: `#5D29C7` (viola) · Sidebar: `#1E1B4B` (navy) · Accent gradient: `#5D29C7 → #7B3FF2`
- Safe area iOS/Android, `min-height:100dvh`, viewport-fit=cover
- Drawer laterale, bottom sheet, FAB, toast, haptic feedback dove supportato

---

*Ceraldi Group SRL · P.IVA 04523831214*
