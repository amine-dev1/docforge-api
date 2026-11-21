# DocForge — Plan Frontend (React)

Basé sur l'API réelle de `backend/app/api/v1/*` (FastAPI). Voir `DESIGN_SYSTEM.md` pour la charte graphique.

## 1. Stack

- Vite + React 18 + TypeScript
- Tailwind CSS (tokens de la charte)
- React Router (routes protégées)
- TanStack Query (cache des appels API) + Axios (client HTTP, intercepteur JWT)
- React Hook Form + Zod (formulaires + validation, miroir des schémas Pydantic backend)

## 2. Authentification

Backend : `POST /api/v1/auth/register`, `/login` (OAuth2 form), `/refresh`, `/logout` (JWT access + refresh token,
voir `app/api/v1/auth.py`). Le frontend utilise le **JWT** (pas la clé API, réservée aux intégrations tierces).

- Pages : `/login`, `/register` (crée une entreprise + son premier user admin).
- Stockage : access token en mémoire (contexte React), refresh token en cookie httpOnly si possible, sinon
  `localStorage` + rotation automatique sur 401 (intercepteur Axios → `/auth/refresh`).

## 3. Arborescence des pages

| Route | Backend | Contenu |
|---|---|---|
| `/login`, `/register` | `auth.py` | Formulaires |
| `/` (Dashboard) | `documents` + `payments` (agrégats côté front, pas d'endpoint stats dédié pour l'instant) | KPI cards (CA du mois, en attente, en retard), derniers documents |
| `/invoices`, `/invoices/:id`, `/invoices/new` | `invoices.py` (CRUD, hérite de `documents.py`) | Liste, détail (lignes + PDF), création |
| `/quotes`, `/quotes/:id`, `/quotes/new` | `quotes.py` | Idem factures |
| `/clients`, `/clients/:id` | `clients.py` | Liste + fiche (contacts inline) |
| `/suppliers`, `/suppliers/:id` | `suppliers.py` | Idem clients |
| `/catalogue/products`, `/categories`, `/units`, `/tax-rates` | `catalogue.py` | 4 sous-onglets CRUD simples |
| `/payments`, `/payments/:id` | `payments.py` | Liste + allocation sur factures |
| `/settings/company` | `tenant.py` (`EnterpriseOut/Update`) | Raison sociale, IF/ICE/RC, coordonnées bancaires, préfixes de numérotation, branding PDF (`primary_color`, `logo_url`...) |
| `/settings/api-keys` | `app/models/api_key.py` (endpoint à vérifier/compléter côté backend) | Gestion des clés API |

## 4. Mapping des écrans ↔ schémas Pydantic (contrat de données, ne pas inventer de champs)

- **Document** (factures/devis partagent le même modèle, `type` les distingue) : `number`, `status`
  (draft/sent/paid/overdue/cancelled), `subtotal_ht`, `total_tax`, `total_ttc`, `amount_paid`, `amount_due`,
  `pdf_url`, `lines[]` (`description`, `quantity`, `unit_price_ht`, `discount_pct`, `tax_rate_value`,
  `line_total_ttc`). → écran de création = tableau de lignes éditable + totaux recalculés en live (miroir du calcul
  serveur dans `documents.py::_compute_line`, le serveur reste la source de vérité à la sauvegarde).
- **Client / Supplier** : identité légale marocaine (ICE, RC, IF, taxe pro, CNSS), coordonnées bancaires, contacts
  multiples (`is_primary`). Formulaire en sections repliables (Identité / Adresse / Banque / Contacts).
- **Payment** : `allocations[]` vers des documents → UI "payer une facture" = sélection de factures ouvertes +
  répartition du montant.
- **Enterprise** (tenant) : contient déjà `primary_color`, `secondary_color`, `font_family`, `logo_url` — ce sont
  les couleurs des **PDF générés pour ce tenant**, distinctes de la charte de l'app elle-même (section Paramètres
  uniquement, pas globales à l'app).

## 5. Lots de travail (pour Codex, dans l'ordre)

1. **Scaffold** (fait par Claude) : Vite + React + TS + Tailwind, tokens de charte posés, routing + layout coquille
   (sidebar/topbar), client Axios + intercepteur JWT, pages de login/register fonctionnelles contre l'API locale.
2. **Lot A — Documents** : liste + détail + création factures/devis (le cœur métier, déjà 100% supporté côté
   backend).
3. **Lot B — CRM** : Clients, Fournisseurs (liste + fiche + contacts).
4. **Lot C — Catalogue** : Produits, catégories, unités, taux de TVA.
5. **Lot D — Paiements** : liste + allocation sur factures.
6. **Lot E — Paramètres** : profil entreprise (branding PDF, préfixes, coordonnées bancaires).

Chaque lot : états vide/chargement/erreur (règle de la charte), formulaires validés avec Zod sur le même schéma que
le backend, et un build (`npm run build`) propre avant de passer au lot suivant.
