# MASTER_CONTEXT.md — Mémoire & Constitution de l'Académie Al-Baji

Ce document fait office de mémoire à long terme pour le projet et définit la charte comportementale obligatoire pour tout agent IA travaillant sur ce codebase. 

---

## 🏛️ 1. Charte comportementale & Interaction de l'IA (Rules of Engagement)

Tout agent IA démarrant une session dans ce projet **doit** se conformer aux consignes suivantes :

### A. Brainstorming & Approbation Obligatoires
* **Règle :** L'IA ne doit jamais modifier de code source ni exécuter de commande impactant le système sans avoir préalablement décrit son plan d'action et obtenu l'accord explicite et écrit de l'utilisateur.

### E. Auto-mise à jour de la Constitution (MASTER_CONTEXT)
* **Règle :** À la fin de chaque étape importante, résolution de bug, ou modification de structure technique, l'IA doit mettre à jour d'elle-même ce fichier `MASTER_CONTEXT.md` (notamment le Registre des Bugs ou le Contexte Technique) sans attendre que l'utilisateur le lui demande.

### B. Protocole d'Arrêt sur Question (Halt-on-Question)
* **Règle :** Si l'IA pose une question de clarification, demande un avis ou présente des options dans son message, elle **doit impérativement arrêter son tour** et attendre la réponse de l'utilisateur.
* Il est formellement interdit d'effectuer des écritures de fichiers ou de lancer des commandes en tâche de fond tant que l'utilisateur n'a pas répondu aux questions posées, même si les paramètres de l'agent autorisent l'auto-approbation.

### C. Le Réflexe Hybride & Recommandation
* **Règle :** Face à tout choix de conception technique ou fonctionnelle, l'IA doit présenter un **tableau comparatif** listant au moins 2 options alternatives.
* Pour chaque option, le tableau doit détailler : les avantages, les inconvénients, le coût d'implémentation et les risques.
* L'IA doit clairement identifier son choix recommandé en le préfixant par **« (Recommandé) »** et en justifiant son raisonnement, tout en s'interdisant d'imposer un verdict final unilatéral.

### D. Alerte Anti-Bloat (Qualité & Modularité du Code)
* **Règle :** Il est interdit de laisser des fichiers uniques grossir de manière démesurée (ex: approcher des 5 000 ou 10 000 lignes).
* Avant d'ajouter du code à un fichier déjà volumineux, l'IA doit analyser s'il est préférable de le découper en modules indépendants (fichiers séparés) et le proposer à l'utilisateur lors du brainstorming.

---

## 🎨 2. Principes directeurs UI / UX

### A. Interface Élève (Dashboard `interactive.html`)
* **Simplicité & Sobriété :** L'application doit être premium, moderne (HSL tailored colors, glassmorphism avec `backdrop-filter` flouté, ombres fines).
* **RTL (Right-To-Left) :** Alignement parfait de l'arabe de droite à gauche.
* **Ergonomie Mobile :** Pas de barres de défilement (scroll) internes masquées dans de petites cartes. Préférer l'affichage vertical complet (auto-height) pour que l'utilisateur fasse défiler la page web globale naturellement sur son téléphone dans Telegram.
* **Focus Questions :** La progression doit afficher le taux de questions résolues avec des jauges visuelles bicolores claires (Vert = correct, Rouge = erreur).

### B. Interface Admin (`admin.html`, `admin-bot.html`, `admin-support.html`)
* **Efficacité :** Triage rapide, indicateurs de tickets ou de rapports non lus sous forme de pastilles rouges accrocheuses.
* **Simplicité :** Options d'édition rapide en ligne et recherche textuelle puissante.

---

## 📓 3. Registre Historique des Bugs & Solutions (Bug Memory)

Afin d'éviter la répétition d'erreurs passées, voici les solutions aux dysfonctionnements historiquement rencontrés sur ce codebase :

| Bug rencontré | Cause racine | Solution technique appliquée |
| :--- | :--- | :--- |
| **Database Locked (SQLite)** | Concurrence d'accès lors des lectures/écritures asynchrones. | Configuration systématique de `PRAGMA journal_mode=WAL;` et `PRAGMA busy_timeout=5000;` lors de l'initialisation de la connexion. |
| **Crash OSError (WinError 87) au démarrage** | Utilisation de `os.kill(old_pid, 0)` sous Windows pour vérifier si l'ancienne instance du bot tourne encore. | Capture spécifique de `OSError` dans le bloc d'exception de la fonction `_kill_existing_instance()` pour éviter de bloquer le démarrage du script. |
| **Erreur de table manquante au démarrage du bot de secours** | La table `student_course_progress` n'était pas initialisée dans `backup_bot.db`. | Ajout de la création de la table `student_course_progress` dans la fonction `init_db()` de `database.py` du bot de secours. |
| **Problème d'encodage des logs console** | Windows PowerShell utilise par défaut des encodages locaux (CP1252) causant des erreurs lors de l'écriture de caractères arabes en console. | Réécriture des sorties intermédiaires dans des fichiers en forçant l'encodage `utf-8`. |
| **Sidebar admin mobile impossible à fermer** | Le backdrop mobile réutilisait la classe générique `.drawer-backdrop` et portait un `display: none` inline prioritaire, empêchant le clic extérieur de fermer le menu. | Création d'un backdrop mobile dédié (`.mobile-sidebar-backdrop`), ajout d'un bouton de fermeture dans la sidebar, fermeture automatique après clic sur un item de navigation mobile, et verrouillage du scroll du body pendant l'ouverture. |
| **Tri absent ou incohérent dans les tableaux admin** | Les tableaux statiques et générés dynamiquement n'avaient pas de comportement de tri homogène, et les dates affichées en arabe n'étaient pas fiables à parser visuellement. | Ajout d'un module générique de tri par en-têtes avec flèches `▲/▼`, détection automatique des tableaux dynamiques, et valeurs `data-sort-value` propres pour les dates/compteurs principaux. |
| **Ajout questions officielles Fiqh leçon 25** | Les 6 questions officielles fournies par l'utilisateur n'étaient pas présentes en source officielle dans `telegram-bot-backup/backup_bot.db` ; seules des questions `generated_by_gemini` existaient pour cette leçon. | Insertion locale dans la table `questions` (`source='official'`, réponses `c.a.b.d.a.b`) et ajout d'une migration idempotente dans `telegram-bot-backup/database.py` pour appliquer le même seed au démarrage Railway sans doublons. |

---

## ⚙️ 4. Contexte technique & Architecture active

### A. Double Structure des Bots
* **Bot Principal (`telegram-bot/`) :** Bot de production fonctionnant avec la base `telegram-bot/persistent_storage/academy.db`.
* **Bot de Secours (`telegram-bot-backup/`) :** Bot de remplacement autonome configuré sur le port **8082** avec sa base de données `telegram-bot-backup/backup_bot.db`.
* **🎯 Focus Actuel de Développement :** Nous travaillons exclusivement sur le **Bot de Secours** (`telegram-bot-backup/`) sur le port **8082**. Le bot principal ne doit recevoir aucune modification pour le moment.

### B. Logique de Progression
* **Parcours Officiel (Leçons) :** Basé uniquement sur les questions officielles (`source != 'generated_by_gemini'`).
* **Parcours Thématique (Axes) :** Basé sur les questions d'entraînement et générées par l'IA (`source == 'generated_by_gemini'`).
* **Sira (Switch Années) :** Progression chronologique basée sur la colonne `hijra_year` pour la matière Sira.

---

## 🔍 5. Procédures d'Audit de Qualité (Contrôle des cours & Médias)

Afin d'éviter la réintroduction d'erreurs, de doublons de cours ou de liens YouTube manquants, les outils et scripts d'audit suivants sont documentés dans le dossier des artifacts et peuvent être exécutés pour valider les données :

### A. Détection des Doublons dans les Transcriptions
* **Script de référence :** `check_duplicate_transcripts.py`
* **Rôle :** Compare le contenu textuel nettoyé des fichiers `.txt` de transcription pour repérer les cours identiques enregistrés sous des noms différents.

### B. Validation des Liens Vidéos & Sources
* **Scripts de référence :** `find_missing_sources.py`, `check_source_quality.py`
* **Rôle :** Vérifie que chaque question officielle possède bien un bloc d'explication pédagogique contenant la mention « المصدر », un lien href YouTube valide (`https://www.youtube.com/...`), et un horodatage précis (ex: `[8:20]`).

---

## 🛡️ 6. Stratégie de Sauvegarde & Plan de Secours (Disaster Recovery)

Le projet dispose d'une politique de sauvegarde multiniveau pour prévenir toute perte de code ou de données utilisateurs.

### A. Sauvegardes Automatiques du Code
* **Mécanisme :** Le bot copie les fichiers sensibles (ex. `handlers/exam.py`, `keyboards/exam_kb.py`) dans le dossier `backup/` à la racine avant chaque démarrage ou modification.
* **Format des fichiers :** `backup/[nom_du_fichier].[timestamp].bak`

### B. Sauvegardes de la Base de Données (Données élèves & Questions)
1. **Sauvegarde Automatique locale :** Au démarrage de l'application, une copie de la base SQLite `backup_bot.db` est automatiquement créée sous le nom `backup_bot.db.bak`.
2. **Export Admin à Distance :** Les administrateurs dotés des rôles `super_admin` ou `backup_admin` peuvent exporter la base de données active directement sur Telegram via le bouton **📦 نسخة احتياطية (SQLite DB)** dans le panneau d'administration (ou la commande callback `admin_data_backup_db`).

### C. Procédure de Restauration rapide (Rollback)
Si le bot ou la base de données rencontre une corruption :
1. Identifier le PID actuel dans le fichier `.bot.pid` et stopper le processus.
2. **Restauration Code :** Remplacer le fichier corrompu par la version `.bak` de secours la plus récente du dossier `backup/`.
3. **Restauration Base de Données :** Remplacer `backup_bot.db` par le fichier `backup_bot.db.bak` ou par le dernier export d'administration sain.
4. **Relancement :** Exécuter `Lancer_Bot.bat` ou `python telegram-bot-backup/main.py`.
