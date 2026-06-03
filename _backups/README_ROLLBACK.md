# 🚨 PROCÉDURE DE RESTAURATION D'URGENCE (ROLLBACK)

Si le tableau de bord d'administration ne se charge plus (écran blanc, blocage, erreur de syntaxe console) après une modification :

## Étape 1 : Identifier le dernier backup fonctionnel
Allez dans ce dossier (`dashboard/_backups/`) et regardez les fichiers.
* Le fichier `admin_backup_[DATE]_[HEURE].js` avec la date la plus récente est votre sauvegarde de sécurité.

## Étape 2 : Restaurer le fichier
1. Supprimez ou renommez le fichier corrompu `dashboard/admin.js` (par exemple en `admin.js.broken`).
2. Copiez le fichier de sauvegarde sélectionné à l'étape 1 et collez-le dans le dossier parent (`dashboard/`).
3. Renommez cette copie en `admin.js`.

*Note : Vous pouvez aussi copier le fichier statique permanent de secours `dashboard/admin.backup.js` qui contient une version 100% garantie stable.*

## Étape 3 : Recharger le navigateur
Actualisez votre navigateur (faites un "Hard Reload" : `Ctrl + F5` ou `Shift + F5`) pour être sûr que le navigateur ne charge pas une version en cache.

---
*Ces sauvegardes sont gérées et générées automatiquement avant chaque modification importante.*
