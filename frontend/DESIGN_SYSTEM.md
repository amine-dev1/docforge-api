# DocForge — Charte graphique (frontend React)

Produit : SaaS de facturation/devis multi-tenant (B2B, usage quotidien, financier). Objectif : **clair, sobre,
digne de confiance** — crédible comme outil comptable, pas comme landing page. Deux influences :
- `dashboard-design` (Quiet / Wordless / Honest) pour la lecture des données.
- Emil Kowalski (design engineering) pour le détail d'interaction et l'animation.

Architecture des tokens en 3 couches (primitif → sémantique → composant), pour que le thème (clair/sombre, future
marque blanche) change sans toucher aux composants.

## 1. Couleurs

### 1.1 Primitifs (valeurs brutes, jamais utilisées directement dans un composant)

```css
:root {
  /* Neutres */
  --gray-0: #ffffff;
  --gray-50: #f7f7f8;
  --gray-100: #f1f2f4;
  --gray-200: #e4e5e9;
  --gray-400: #9a9fa6;
  --gray-500: #6b7078;
  --gray-900: #15171c;

  /* Bleu (marque) */
  --blue-500: #5167FC;
  --blue-600: #4558D6;

  /* Statuts */
  --red-500: #d6433c;
  --green-600: #1a9c6b;
  --gray-300: #c7cad1;
}
```

### 1.2 Sémantique (ce que la couleur *veut dire*)

```css
:root {
  --color-bg: var(--gray-50);
  --color-surface: var(--gray-0);
  --color-surface-muted: var(--gray-100);
  --color-border: var(--gray-200);
  --color-text: var(--gray-900);
  --color-text-muted: var(--gray-500);
  --color-text-faint: var(--gray-400);

  --color-accent: var(--blue-500);
  --color-accent-hover: var(--blue-600);
  --color-accent-contrast: #ffffff;

  --color-status-draft: var(--gray-400);
  --color-status-sent: var(--blue-500);
  --color-status-paid: var(--green-600);
  --color-status-overdue: var(--red-500);
  --color-status-cancelled: var(--gray-300);

  --color-money-positive: var(--green-600);
  --color-money-negative: var(--red-500);

  --color-danger: var(--red-500);
  --color-focus-ring: color-mix(in srgb, var(--color-accent) 30%, transparent);
}

:root[data-theme='dark'] {
  --color-bg: #0f1115;
  --color-surface: #17191f;
  --color-surface-muted: #1d2027;
  --color-border: #2a2d36;
  --color-text: #f1f2f4;
  --color-text-muted: #9a9fa6;
  --color-text-faint: #6b7078;
  --color-accent: var(--blue-500);
  --color-accent-hover: var(--blue-600);
  --color-accent-contrast: #ffffff;
}
```

### 1.3 Composant (dérivé du sémantique, au cas par cas)

```css
--button-primary-bg: var(--color-accent);
--button-primary-bg-hover: var(--color-accent-hover);
--badge-draft-bg: color-mix(in srgb, var(--color-status-draft) 15%, transparent);
--badge-paid-bg: color-mix(in srgb, var(--color-status-paid) 15%, transparent);
```

**Règle** : jamais de hex en dur dans un composant React — toujours `var(--color-*)` ou la classe Tailwind
équivalente (`bg-accent`, `text-status-paid`...). Une seule teinte "entité" par domaine, le reste reste gris ; le
rouge n'apparaît que sur une vraie alerte (facture en retard, solde négatif) — jamais comme déco.

### 1.4 Champs de formulaire partagés

Tous les formulaires, y compris Login et Register, utilisent `TextField` et `TextAreaField`
exportés par `src/components/ui`. Leur implémentation unique est dans `Field.tsx`.
Les champs reprennent le libellé flottant du modèle de connexion, une hauteur de 52px,
des coins de 6px et le focus bleu de la marque. Les couleurs suivent le thème ; les pages
d’authentification définissent uniquement les variables `--field-bg`, `--field-border`,
`--field-text` et `--field-muted` pour leur fond sombre.

```tsx
<TextField label="Email" type="email" autoComplete="email" required
  {...form.register('email')} error={form.formState.errors.email?.message} />
<TextAreaField label="Notes" rows={3} {...form.register('notes')} />
```

Les propriétés natives, références React Hook Form, aides et erreurs sont conservées.
Le libellé reste levé lorsqu’un exemple de saisie est fourni via `placeholder`.
Réserver `bare` aux cellules de tableau déjà nommées par leur en-tête, avec un `aria-label`.
Utiliser `SelectField` et `DatePicker` avec `label` pour les choix et les dates : ils partagent
le même style de contrôle et un libellé intérieur permanent. Les cases à cocher restent
des `CheckboxField`. Ne pas créer de nouvel `<input>` ou `<textarea>` dans une page.

Pour les coordonnées, utiliser `CountryField` et `PhoneField` via un `Controller` React Hook Form.
`CountryField` reçoit et renvoie un code ISO alpha-2 (`MA`, `FR`…), et affiche le nom français
avec son drapeau. `PhoneField` reçoit et renvoie une chaîne de téléphone complète ; son sélecteur
affiche code ISO et indicatif. `defaultCountry` provient du pays de l’adresse (repli `MA`).
Les numéros locaux existants ne sont pas réécrits ni validés automatiquement : le champ accepte
le numéro international complet et le choix d’un pays remplace seulement un préfixe international
explicite. Les codes partagés gardent le pays choisi par l’utilisateur.

La liste des indicatifs est embarquée dans `countries.ts` (source :
[country-telephone-data](https://github.com/mukeshsoni/country-telephone-data)).
Les drapeaux SVG sont chargés depuis `flagcdn.com` ; les noms et codes restent utilisables
si les images sont indisponibles. Aucun paquet npm supplémentaire n’est nécessaire.

## 2. Typographie

- **Famille unique** : `Inter` (variable font) pour tout — UI, titres, chiffres. Même police que `font_family` par
  défaut de `Enterprise` côté backend : cohérence visuelle avec les PDF générés par l'app. Fallback :
  `-apple-system, 'Segoe UI', sans-serif`.
- Pas de police secondaire pour les titres : un outil financier gagne en crédibilité avec une seule typo bien
  exécutée plutôt qu'un pairing décoratif (règle *Quiet* du skill dashboard-design).
- **Échelle** :

  | Rôle | Taille | Poids | Line-height |
  |---|---|---|---|
  | Titre de page | 1.5rem / 24px | 600 | 1.25 |
  | Titre de section / carte | 1.125rem / 18px | 600 | 1.3 |
  | Corps | 0.875rem / 14px | 400 | 1.5 |
  | Label / meta | 0.75rem / 12px | 500, tracking +0.02em, uppercase | 1.3 |
  | Chiffres (cartes KPI) | 1.25rem / 20px | 600 | 1.2 |
  | Chiffres (tableaux) | 0.875rem / 14px | 500 | — |

- Montants et références toujours en `font-variant-numeric: tabular-nums`, alignés à droite dans les tableaux —
  jamais de police mono séparée : Inter en tabular-nums suffit et reste cohérent avec le reste du texte.

## 3. Grille, espacement, layout

- **Unité de base** : 4px. Espacements usuels : 4, 8, 12, 16, 24, 32, 48px (`gap-1` → `gap-12` Tailwind).
- **Flexbox** pour la coquille (sidebar fixe 240px + zone de contenu `flex-1`) et tout alignement 1D (toolbar,
  ligne de formulaire).
- **CSS Grid** pour tout ce qui est 2D : cartes KPI (`grid-cols-12`, cartes en `col-span-3/4/6`), formulaires à
  colonnes multiples, tableau de lignes de document.
- **Conteneur de contenu** : max-width 1280px, centré, padding horizontal 24px (16px en mobile).
- **Cartes** : `bg-surface`, `border border-border`, `rounded-xl` (12px), padding 20px, `shadow-sm` seulement.
- **Breakpoints** (Tailwind) : `sm` 640, `md` 768, `lg` 1024 (sidebar → drawer sous `lg`), `xl` 1280.
- **Tableaux** : lignes 48px, en-tête collante, zébrage léger (`--color-surface-muted` sur les lignes paires),
  actions à droite en icônes.

## 4. Animation & motion

Principe directeur (Emil Kowalski / design engineering) : **chaque animation doit justifier sa présence**. Pas
d'animation "parce que ça fait propre" sur un outil utilisé des dizaines de fois par jour.

### 4.1 Faut-il animer ?

| Fréquence d'usage | Décision |
|---|---|
| Raccourcis clavier, validation de ligne dans un tableau | **Aucune animation.** |
| Hover, tri de colonne, navigation de liste | Supprimer ou réduire au minimum (couleur/opacité, pas de mouvement) |
| Modale, panneau latéral (fiche client/fournisseur), toast | Animation standard (ci-dessous) |
| Premier chargement, écran vide, confirmation de paiement | Peut avoir un peu plus de présence |

### 4.2 Courbes et durées (tokens)

```css
:root {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);     /* entrée d'élément, feedback de clic */
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* déplacement/morph à l'écran */
  --ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);   /* panneau latéral, type iOS */
}
```

| Élément | Durée | Easing |
|---|---|---|
| Feedback de clic (bouton, ligne de tableau) | 120–160ms | `--ease-out` |
| Tooltip, petit popover | 125–200ms | `--ease-out` |
| Menu déroulant, select | 150–250ms | `--ease-out` |
| Modale, panneau latéral (fiche, filtre) | 200–400ms | `--ease-drawer` |
| Toast (confirmation d'enregistrement) | 400ms | `ease` |

Jamais `ease-in` sur une animation d'interface (démarre lentement → sensation de lenteur). Jamais `transition: all` —
toujours les propriétés exactes (`transform`, `opacity`).

### 4.3 Patterns de composants

- **Boutons / lignes cliquables** : `transform: scale(0.97)` sur `:active`, transition 160ms `--ease-out`. Confirme
  que l'app a "entendu" le clic.
- **Apparition** : jamais depuis `scale(0)` (rien n'apparaît de rien) — partir de `scale(0.95)` + `opacity: 0`.
- **Popovers / menus contextuels** (actions de ligne, sélecteur de client) : `transform-origin` sur le déclencheur,
  pas centré. **Exception : les modales** (confirmation de suppression, création rapide) restent centrées.
- **Panneau latéral** (fiche client/fournisseur, filtres avancés) : entre depuis la droite, `translateX(100%)` →
  `0`, `--ease-drawer`, 300ms ; sortie plus rapide que l'entrée (200ms).
- **Toasts** (ligne enregistrée, facture envoyée) : transitions CSS (pas de keyframes) pour rester interruptibles
  si plusieurs apparaissent vite.
- **Listes** (résultats de recherche client, lignes de document ajoutées) : stagger léger 30–60ms entre éléments,
  jamais plus — un tableau de 50 factures n'anime pas chaque ligne à l'affichage initial (coût + bruit visuel),
  seulement les lignes *ajoutées* après coup.
- **Skeletons de chargement** : `opacity` pulse doux, pas de mouvement.

### 4.4 Accessibilité

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
```
Les changements de couleur/opacité qui aident à la compréhension (badge de statut qui change) restent ; on retire
le mouvement.

### 4.5 Performance

N'animer que `transform` et `opacity` (compositor, pas de reflow). Les changements de `--swipe-amount` ou autre
variable CSS sur un conteneur parent recalculent le style de tous les enfants — pour un drag sur une ligne de
tableau, modifier `transform` directement sur l'élément, pas une variable CSS héritée.

## 5. Composants (conventions)

- **Boutons** : primaire = fond `--color-accent`, texte blanc, `rounded-lg`, `h-9 px-4`, poids 500, voir §4.3 pour
  le press state ; secondaire = bordure `--color-border` + fond transparent ; destructeur = texte
  `--color-status-overdue`, fond plein uniquement dans la modale de confirmation.
- **Champs** : `h-9`, `rounded-lg`, bordure `--color-border`, focus = `box-shadow: 0 0 0 2px var(--color-focus-ring)`
  (pas de `outline` par défaut du navigateur).
- **Badges de statut** : pastille pleine 6px + label court, couleur = token de statut — jamais de texte seul en
  couleur sans la pastille.
- **États vide / chargement / erreur** : chaque liste a ses 3 états dessinés (skeleton, illustration simple + CTA,
  message d'erreur avec bouton "réessayer") — jamais un tableau vide sans rien.

## 6. Stack technique (implémentation)

- React 18 + TypeScript, Vite, Tailwind CSS 4 (`@theme` mappe les tokens sémantiques ci-dessus sur
  `colors.bg/surface/border/text/accent/status-*`).
- Police Inter via `@fontsource/inter` (400/500/600).
- Dark mode via `data-theme` sur `<html>`, toggle persisté en `localStorage`.
- Animations : CSS transitions/`@starting-style` par défaut (perf, interruptible) ; `motion/react` uniquement pour
  le drag (fiches à glisser, réordonnancement de lignes) où une physique de ressort est nécessaire.
