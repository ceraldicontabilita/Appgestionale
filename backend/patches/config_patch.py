"""
PATCH · CORS per Ceraldi Mobile (chat-8)

Scopo: garantire che il dominio GitHub Pages della mini-app mobile
(https://ceraldicontabilita.github.io) sia sempre accettato dal CORS
del backend gestionale2, indipendentemente dal valore di CORS_ORIGINS
in .env.

Come applicare:
    Sostituire il metodo `get_cors_origins(self)` esistente nella
    classe Settings di `app/config.py` con la versione qui sotto.

La funzione:
  - Se CORS_ORIGINS è "*" → forza lista esplicita con i domini noti
    (serve perché CORS con allow_credentials=True non accetta wildcard)
  - Se CORS_ORIGINS è una lista → vi aggiunge sempre i domini Ceraldi
    se mancanti, senza duplicati
"""

# ============================================================================
# PATCH da applicare in app/config.py (dentro la classe Settings)
# ============================================================================

def get_cors_origins(self) -> list[str]:
    """Parse CORS origins from comma-separated string.

    Extended to always include Ceraldi Mobile (GitHub Pages) origin.
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
