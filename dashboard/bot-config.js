/**
 * bot-config.js — Intercepteur d'API pour GitHub Pages
 *
 * Ce script doit être chargé EN PREMIER dans chaque page HTML.
 * Il lit bot_config.json pour obtenir l'URL actuelle du bot (Serveo),
 * puis intercepte tous les fetch('/...') pour les rediriger vers cette URL.
 *
 * Si bot_config.json est vide ou inaccessible, les appels restent relatifs
 * (fonctionnement normal quand servi directement par le bot local).
 */
(async function () {
    let apiBase = '';

    try {
        // Cache-bust pour toujours avoir la config la plus récente
        const resp = await fetch('./bot_config.json?t=' + Date.now(), {
            cache: 'no-store'
        });
        if (resp.ok) {
            const cfg = await resp.json();
            const raw = (cfg.api_url || '').trim().replace(/\/$/, '');
            // On n'utilise la config que si l'URL est différente de notre origine
            // (évite la double-redirection quand on est déjà sur le bot local)
            if (raw && raw !== window.location.origin) {
                apiBase = raw;
            }
        }
    } catch (e) {
        // Silencieux — si on ne trouve pas la config, on laisse les URLs relatives
        console.debug('[bot-config] Pas de bot_config.json trouvé, mode relatif actif.');
    }

    window.__BOT_API_BASE__ = apiBase;

    if (apiBase) {
        console.info('[bot-config] API redirigée vers :', apiBase);
        const _fetch = window.fetch.bind(window);
        window.fetch = function (resource, options) {
            // Intercepte uniquement les URLs relatives (commençant par /)
            if (typeof resource === 'string' && resource.startsWith('/')) {
                resource = apiBase + resource;
            }
            return _fetch(resource, options);
        };
    }
})();
