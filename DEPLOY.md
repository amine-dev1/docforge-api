# Mise en ligne de DocForge (Fly.io + Vercel)

Rien n'est encore créé ni déployé. Backend sur Fly.io, frontend sur Vercel (compte d'Amine, créé par lui).

## 1. Backend sur Fly.io (`backend/`)
Les clés ne sont JAMAIS dans le dépôt : elles vont dans les « secrets » Fly.

```powershell
cd backend
flyctl apps create docforge-api-amine
flyctl secrets set SECRET_KEY="<nouvelle clé : python -c ""import secrets; print(secrets.token_hex(32))"">" DATABASE_URL="<adresse Neon de production>"
flyctl secrets set RESEND_API_KEY="<clé Resend>" RESEND_FROM_EMAIL="<expéditeur>"
flyctl deploy
```

Vérifier : `https://docforge-api-amine.fly.dev/api/v1/health` doit répondre `healthy`.

- **Base de données** : choisir entre la base Neon de développement actuelle et une base/branche Neon dédiée à la production.
  Une **nouvelle** `SECRET_KEY` pour la production (celle du `.env` local ne doit pas être réutilisée).
- **Google Drive** : non configuré en ligne (l'autorisation demande un navigateur sur la machine). L'envoi vers Drive échoue
  sans bloquer ; le PDF se génère à la demande, sans Drive.
- Le serveur s'arrête quand il est inactif : la première requête après une pause est plus lente.

## 2. Frontend sur Vercel (`frontend/`)
Dans le compte Vercel d'Amine : « Add New > Project », importer le dépôt, puis :
- **Root Directory** : `frontend`
- **Framework Preset** : Vite (commande de build `npm run build`, dossier `dist`)
- **Variables d'environnement** : aucune. `vercel.json` redirige `/api/*` vers le backend Fly et gère les routes de l'application.
  Si le nom Fly change, modifier l'adresse dans `frontend/vercel.json`.

## 3. Après la mise en ligne
- **Webhook Stripe** : l'adresse affichée dans l'application utilise le domaine Vercel
  (`https://<domaine>/api/v1/webhooks/stripe/<id>`) : la copier dans Stripe.
- **CORS** : inutile avec la redirection Vercel (les appels passent par le même domaine).
