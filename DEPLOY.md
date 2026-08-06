# Mettre le site BONZINILABS LTD en ligne

Objectif : obtenir une **adresse web publique et gratuite**, qui s'ouvre **sans mot de passe et
sans connexion**, à coller dans le champ « Business website » de Stripe.

Le site est statique : `index.html` + trois pages légales + un dossier `assets/`. Il n'y a rien à
compiler, aucune base de données, aucun serveur.

---

## 0. Quelle plateforme choisir — lisez ceci d'abord

| | Netlify (gratuit) | Vercel (Hobby, gratuit) |
|---|---|---|
| Usage commercial | **Autorisé** (seule la revente d'hébergement est interdite) | **Interdit** : « Hobby teams are restricted to non-commercial personal use only » |
| Convient au site d'une société qui vend des services | oui | non — il faut le plan Pro (20 $/mois) |
| Bande passante | 100 Go/mois | ~100 Go/mois |

**Recommandation : Netlify.** Le site de BONZINILABS LTD fait la promotion de prestations
vendues et sert à activer un compte Stripe : c'est un usage commercial au sens des conditions
de Vercel. Si vous préférez Vercel, prenez le plan Pro.

En cas d'urgence absolue vous pouvez publier sur Vercel Hobby aujourd'hui pour débloquer
Stripe, puis migrer vers Netlify dans les jours qui suivent.

---

## 1. Netlify — la voie la plus rapide (glisser-déposer, 5 minutes)

1. Ouvrez `https://github.com/omegathesecond/level1-portfolio/tree/claude/bonzinilabs-website-w4s21z`.
2. Bouton vert **Code** → **Download ZIP**.
3. Décompressez le ZIP. Ouvrez le dossier obtenu : vous devez voir `index.html` **directement
   dedans** (pas dans un sous-dossier).
4. Ouvrez `https://app.netlify.com/drop` et connectez-vous (GitHub ou e-mail).
5. Faites glisser **le dossier** (pas le fichier ZIP) dans la zone en pointillés.
6. Netlify affiche une adresse en `.netlify.app` au bout de quelques secondes.
7. **Rendez le site public** — voir §3. C'est obligatoire depuis 2026.
8. Renommez le projet — voir §4 — puis testez — voir §5.

## 2. Netlify depuis GitHub (mises à jour automatiques ensuite)

1. `https://app.netlify.com` → **Sign up** → **GitHub** → **Authorize Netlify**.
2. **Add new project** → **Import an existing project** → **GitHub**.
3. Choisissez le dépôt `level1-portfolio`. Si vous ne le voyez pas :
   **Configure the Netlify app on GitHub**, cochez le dépôt, enregistrez.
4. **Branch to deploy** : `claude/bonzinilabs-website-w4s21z`.
5. **Build command** : laissez vide. **Publish directory** : `.`
   (le fichier `netlify.toml` du dépôt règle déjà tout cela.)
6. **Deploy**.
7. Rendez le site public (§3), renommez-le (§4), testez (§5).

Pour changer de branche plus tard :
**Project configuration → Build & deploy → Continuous Deployment → Branches and deploy
contexts → Configure**.

---

## 3. LE PIÈGE DU MOT DE PASSE — la partie la plus importante

Si l'adresse que vous donnez à Stripe affiche un écran de connexion, **votre dossier est
bloqué**. Stripe l'écrit noir sur blanc : *« The webpage must be accessible without a
password. »*

### 3.1 Netlify

Piège 2026 : les équipes créées **à partir du 28 juillet 2026** ont pour réglage par défaut
**« Private for new projects »** — un site neuf démarre donc derrière une connexion d'équipe.

1. Ouvrez le projet dans `https://app.netlify.com`.
2. **Project configuration** → **General**.
3. Descendez à **Visitor access** → **Project visibility**.
4. Choisissez **Public** (ou cliquez **Make public**), puis enregistrez.
5. Sur certains plans, le réglage est dans **Project configuration → Access & security →
   Visitor access → Password Protection** : il doit être sur **No protection**.
6. Vérifiez qu'aucun fichier `_headers` n'a été ajouté avec une ligne `Basic-Auth`.

### 3.2 Vercel

Vercel active **Vercel Authentication** en portée **Standard Protection** : cela protège
**tous les déploiements sauf la production**. Autrement dit, une adresse *preview* demande une
connexion — et Stripe est bloqué.

- **Adresse de production** : nom court et propre, `bonzinilabs.vercel.app`.
- **Adresse preview** : contient un identifiant aléatoire ou le nom de la branche
  (`bonzinilabs-git-claude-…vercel.app`). **Ne la donnez jamais à Stripe.**
- Dans l'onglet **Deployments**, la bonne ligne porte l'étiquette **Production**.
- Réglage : projet → **Settings** → **Deployment Protection**. Mettez **Vercel
  Authentication** sur **Disabled** et **Save**. Vérifiez qu'aucune **Password Protection**
  n'est active.
- Le site vit sur `claude/bonzinilabs-website-w4s21z`, qui n'est pas la branche par défaut.
  Réglez **Settings → Environments → Production → Branch Tracking** sur cette branche, ou
  fusionnez la branche dans `master`. Sans cela, vos futures modifications ne partiront qu'en
  preview protégée.

---

## 4. Une adresse propre

**Netlify** : **Project configuration** → **General** → **Project details** →
**Change project name** → `bonzinilabs` (sinon `bonzinilabs-ltd`).
L'ancienne adresse cesse aussitôt de fonctionner et redevient disponible pour quelqu'un
d'autre : **renommez avant** de coller l'adresse dans Stripe.

**Vercel** : **Settings** → **General** → **Project Name** → `bonzinilabs` → **Save**.
Vercel ne garantit pas que l'ancienne adresse reste accessible : même règle.

---

## 5. Vérification obligatoire avant de coller l'adresse dans Stripe

1. **Fenêtre de navigation privée** (`Ctrl+Maj+N`) : collez l'adresse. Le site doit s'afficher
   immédiatement, sans écran de connexion ni mot de passe.
2. **Téléphone, Wi-Fi coupé** (données mobiles) : la même adresse doit s'ouvrir. Ce test prouve
   qu'aucun cookie de votre ordinateur ne masque une protection.
3. L'onglet du navigateur doit afficher
   **« BONZINILABS LTD — AI Automation & AI Agents for Business »**.
4. `Ctrl+F` sur la page et vérifiez la présence de : `BONZINILABS LTD`, `71-75 Shelton Street`,
   `England & Wales`, `contact@bonzinilabs.com`, `GBP`.
5. Ouvrez chacune des trois pages légales en tapant l'adresse à la main :
   `/terms.html`, `/refunds.html`, `/privacy.html`. Aucune erreur 404.
6. `F12` → onglet **Network** → `Ctrl+R` : aucune ligne rouge, aucun 404.
7. Envoyez un e-mail de test à `contact@bonzinilabs.com` depuis une autre adresse et
   **vérifiez qu'il arrive**. Une adresse qui rebondit est une cause invisible de refus.
8. Confirmez que l'adresse est bien celle de **production** (§3.2), puis collez-la dans Stripe
   avec `https://`.
9. **Ne remettez aucune protection après l'activation.** Stripe exige que le site reste
   accessible en permanence et le revérifie régulièrement.

---

## 6. Brancher le domaine `bonzinilabs.com` (plus tard)

**Netlify** : **Domain management** → **Add a domain** → `bonzinilabs.com` → « DNS externe ».
Valeurs documentées : domaine nu → ALIAS/ANAME vers `apex-loadbalancer.netlify.com`, ou à
défaut un enregistrement **A** vers `75.2.60.5` ; `www` → **CNAME** vers
`bonzinilabs.netlify.app`.

**Vercel** : **Settings** → **Domains** → **Add Domain**. Valeurs habituelles : **A**
`216.198.79.1` pour le domaine nu, **CNAME** propre au projet pour `www`.

Dans les deux cas, **recopiez ce qu'affiche l'écran au moment où vous le faites** : ces valeurs
changent et celles de votre tableau de bord font foi.

**Chez IONOS** : `my.ionos.fr` → **Domaines & SSL** → `bonzinilabs.com` → onglet **DNS** →
**AJOUTER UN ENREGISTREMENT**. Créez l'enregistrement A (hostname `@` ou vide) et le CNAME
`www`. Supprimez les anciens enregistrements A/CNAME qui pointaient ailleurs, sinon conflit.
Comptez de 15 minutes à quelques heures, puis attendez le cadenas HTTPS.

Pensez aussi à créer les enregistrements **MX** pour recevoir le courrier sur
`contact@bonzinilabs.com` : un domaine d'entreprise incapable de recevoir un e-mail est un
signal négatif pour un examinateur.

---

## 7. Solution de repli : hébergement classique IONOS

1. `my.ionos.fr` → **Hébergement** → **FTP/SFTP**. Notez le serveur et l'identifiant, créez le
   mot de passe.
2. Connectez-vous avec **FileZilla** en **SFTP** (port 22).
3. La racine web est `/`, dont le chemin absolu ressemble à
   `/kunden/homepages/…/htdocs/` (contrats antérieurs au 21/07/2026) ou `/home/www/` (après).
4. Déposez **tout le contenu du dépôt** : `index.html`, `terms.html`, `privacy.html`,
   `refunds.html`, `favicon.ico`, `robots.txt`, `sitemap.xml` et le dossier `assets/`.
5. `index.html` doit être **à la racine liée au domaine**, jamais dans un sous-dossier.
6. Supprimez toute page « en construction » d'IONOS qui prendrait le dessus.

---

## 8. Modifier le site plus tard

- Chaque `git push` sur la branche de production redéclenche un déploiement en 30 à 60
  secondes. Vous pouvez aussi éditer un fichier directement sur GitHub (crayon **Edit** →
  **Commit changes**).
- Forcer un redéploiement — **Netlify** : onglet **Deploys** → **Trigger deploy**.
  **Vercel** : onglet **Deployments** → menu **⋯** → **Redeploy**.
- Site déposé en glisser-déposer : refaites glisser le dossier mis à jour en bas de la page
  **Deploys**.

---

## 9. À compléter dès que vous avez l'information

Ces éléments ne sont pas inventés dans le code — il faut les ajouter vous-même :

| Élément | Où | Pourquoi |
|---|---|---|
| Numéro d'immatriculation (company number) | `index.html`, section « Company details » (un commentaire indique l'emplacement exact) et pied de page des pages légales | Obligatoire sur le site d'une société britannique (Companies Act 2006) et fort signal de confiance pour Stripe |
| Numéro de téléphone | section Contact | Stripe demande « something besides contact forms » ; e-mail + téléphone est plus solide qu'e-mail seul |
| Numéro de TVA | pied de page | uniquement si la société est assujettie |
| Boîte `contact@bonzinilabs.com` opérationnelle | chez votre hébergeur mail | une adresse qui rebondit fait échouer la vérification sans explication |

Pour changer l'adresse e-mail partout d'un coup :

```sh
grep -rl 'contact@bonzinilabs.com' . --exclude-dir=.git \
  | xargs sed -i 's/contact@bonzinilabs\.com/votre@adresse.com/g'
```
