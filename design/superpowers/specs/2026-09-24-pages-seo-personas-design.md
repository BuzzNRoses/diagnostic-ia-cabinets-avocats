# Design — Pages SEO par persona pour les cabinets d’avocats

Date : 2026-09-24
Statut : design conversationnel approuvé, spécification écrite en attente de revue

## 1. Intention et résultat recherché

Étendre le site commercial actuel avec un répertoire de quinze pages consacrées aux principaux rôles rencontrés dans un cabinet d’avocats. Chaque page doit répondre à une intention de recherche propre au rôle, décrire ses tâches et points de friction, puis distinguer ce qui peut être assisté, automatisé sous conditions ou doit rester exclu de l’automatisation.

Le résultat attendu n’est pas un catalogue d’outils ni une encyclopédie exhaustive. Le site doit aider un lecteur à reconnaître une situation de travail et à demander un diagnostic sur un seul cas d’usage.

### Contraintes confirmées

- Cible initiale : cabinets d’avocats français, principalement de 1 à 50 personnes.
- Quinze pages persona dès la première publication.
- Contenu original et spécifique à chaque rôle ; aucun simple remplacement de titre dans un texte générique.
- Aucun gain chiffré, témoignage, prix accepté ou résultat client inventé.
- Validation humaine obligatoire pour les résultats utilisés professionnellement.
- Aucun conseil juridique, garantie RGPD, recherche juridique autonome, calcul autonome de délais ou envoi automatique non contrôlé.
- Un seul appel à l’action commercial : demander un échange exploratoire.
- Le formulaire existant reste local au navigateur tant qu’un canal de contact n’est pas choisi.

## 2. Approches examinées

### A. Quinze pages persona reliées à un hub — retenue

Chaque page correspond à un rôle ou une responsabilité suffisamment distincte. Une page centrale permet de comparer les rôles et d’accéder aux pages. Le gabarit visuel reste commun, mais les tâches, risques, exemples et questions de diagnostic sont propres à chaque persona.

Avantages : recherche ciblée, contenu utile, maillage compréhensible, extension progressive.
Compromis : effort éditorial important et obligation de documenter chaque métier.

### B. Six familles de métiers

Regrouper les rôles en direction, production juridique, support administratif, finance, développement et fonctions techniques.

Avantage : moins de risque de contenu mince.
Rejet : ne répond pas au choix confirmé de douze à quinze personas dès la première publication.

### C. Pages persona × tâche

Créer une URL pour chaque combinaison, par exemple « automatiser la facturation pour un office manager ».

Avantage apparent : grand nombre de mots-clés.
Rejet : multiplication de pages proches, maintenance lourde et risque de pages satellites ou de contenu produit à grande échelle sans valeur propre.

## 3. Taxonomie retenue

Le répertoire public sera placé sous `/metiers/`.

1. `/metiers/avocat-individuel/`
2. `/metiers/associe-dirigeant/`
3. `/metiers/avocat-collaborateur/`
4. `/metiers/avocat-contentieux/`
5. `/metiers/avocat-conseil-transactionnel/`
6. `/metiers/eleve-avocat-stagiaire/`
7. `/metiers/secretaire-assistant-juridique/`
8. `/metiers/office-manager-assistant-direction/`
9. `/metiers/responsable-administratif-financier/`
10. `/metiers/facturation-recouvrement/`
11. `/metiers/ressources-humaines-recrutement/`
12. `/metiers/communication-business-development/`
13. `/metiers/documentaliste-knowledge-manager/`
14. `/metiers/referent-informatique-dsi/`
15. `/metiers/dpo-conformite/`

### Règles de regroupement

- « Secrétaire juridique » et « assistant juridique » partagent une page, car les appellations et missions se recouvrent fortement dans les sources métier.
- « Office manager » et « assistant de direction » partagent une page, mais les différences de responsabilité sont explicitées dans le contenu.
- Les pages « contentieux » et « conseil / transactionnel » ne décrivent pas un statut contractuel : elles couvrent deux contextes de travail dont les flux, contraintes et risques diffèrent.
- Une même personne peut porter plusieurs rôles dans un petit cabinet. Chaque page le signale et renvoie vers les responsabilités connexes plutôt que de prétendre à une organisation universelle.

## 4. Architecture technique

Le site reste statique et compatible avec GitHub Pages. La source et la sortie publique sont séparées.

```text
/
├── content/
│   ├── site.json
│   └── personas/
│       ├── avocat-individuel.json
│       └── ... 14 autres fichiers
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── hub-metiers.html
│   ├── persona.html
│   └── 404.html
├── assets-src/
│   ├── styles.css
│   └── site.js
├── scripts/
│   └── build.py
├── tests/
│   └── test_site.py
└── docs/
    ├── index.html
    ├── 404.html
    ├── robots.txt
    ├── sitemap.xml
    ├── assets/
    └── metiers/
```

### Choix techniques

- Générateur local en Python standard uniquement : aucune dépendance applicative ou service de génération externe.
- Les contenus sont stockés dans des fichiers JSON structurés, un fichier par persona.
- Les pages HTML finales sont générées dans `/docs` et commitées.
- GitHub Pages est reconfiguré pour publier `main:/docs`.
- CSS et JavaScript sont mutualisés sous `/docs/assets/`.
- Le site reste utilisable sans JavaScript, sauf la génération locale du résumé du formulaire.

Ce découpage évite quinze copies de la feuille de style et rend les contrôles de cohérence automatisables. Le gabarit commun ne justifie jamais un contenu commun : les paragraphes métier restent propres à chaque persona.

## 5. Modèle de contenu d’une persona

Chaque fichier persona contient au minimum :

- `slug` : identifiant d’URL stable ;
- `name` : nom affiché du rôle ;
- `seo_title` : titre de page unique ;
- `meta_description` : description unique et factuelle ;
- `intro` : situation du rôle dans le cabinet ;
- `responsibilities` : responsabilités principales ;
- `frictions` : tâches répétitives ou points de contrôle ;
- `assist` : usages où l’IA peut préparer, classer, extraire ou proposer ;
- `automate_with_controls` : automatisations envisageables avec limites explicites ;
- `do_not_automate` : décisions ou actions à exclure ;
- `data_and_risks` : données manipulées et risques ;
- `pilot` : un exemple de pilote limité ;
- `existing_tools_first` : vérifications à mener avant tout développement ;
- `diagnostic_questions` : questions propres au rôle ;
- `related_personas` : deux à quatre liens réellement pertinents ;
- `sources` : sources publiques utilisées pour vérifier les missions du rôle.

Le modèle interdit les champs de gains estimés non mesurés, de recommandations juridiques et de témoignages fictifs.

## 6. Structure d’une page persona

1. Fil d’Ariane : Accueil → Métiers → Persona.
2. Titre explicite, par exemple « IA et automatisation pour un associé de cabinet d’avocats ».
3. Introduction : responsabilités et contexte du rôle.
4. « Ce qui prend du temps » : tâches et contrôles observables.
5. Matrice en trois niveaux :
   - assister ;
   - automatiser sous conditions ;
   - ne pas automatiser.
6. Données, confidentialité et validation humaine.
7. Exemple de pilote limité, sans promesse de résultat.
8. Outils et processus existants à examiner d’abord.
9. Questions à poser pendant un diagnostic.
10. Rôles connexes.
11. Appel à l’action unique vers `/#contact`.
12. Sources métier visibles en bas de page.

## 7. Ligne éditoriale

- Écrire pour le professionnel concerné, avec ses tâches et son vocabulaire, sans jargon de consultant.
- Décrire ce que l’outil prépare ou transforme ; ne pas écrire qu’il « remplace » une personne.
- Séparer explicitement assistance, automatisation et décision humaine.
- Préférer les exemples de flux aux listes génériques d’outils.
- Mentionner les incertitudes et les différences selon la taille du cabinet.
- Ne pas présenter toutes les tâches comme des problèmes nécessitant l’IA.
- Ne pas publier une page lorsque les sources ne permettent pas de distinguer suffisamment son contenu d’une autre persona.

### Garde-fou anti-contenu répétitif

Le build échoue si deux personas ont le même titre, la même meta description, le même exemple de pilote ou des blocs entiers identiques. La revue humaine vérifie également que la page apporte une réponse différente, pas seulement des synonymes.

## 8. SEO et maillage

### Page centrale `/metiers/`

- Présente les quinze rôles par familles fonctionnelles.
- Explique qu’une personne peut cumuler plusieurs responsabilités.
- Ne contient pas quinze cartes identiques : elle utilise une liste éditoriale structurée avec une courte différence métier par rôle.

### Métadonnées

Chaque page possède :

- un `<title>` unique ;
- une meta description unique ;
- une URL canonique absolue ;
- un seul `h1` ;
- une hiérarchie de titres cohérente ;
- des données structurées `WebPage` et `BreadcrumbList` ;
- aucun faux balisage `Person`, avis, note ou FAQ.

### Maillage interne

- Accueil → hub Métiers.
- Hub → quinze personas.
- Persona → deux à quatre personas connexes et accueil/contact.
- Aucun lien automatique vers toutes les pages depuis chaque persona.

### Fichiers d’indexation

- `sitemap.xml` contient uniquement les pages canoniques publiées.
- `robots.txt` autorise l’exploration et indique le sitemap.
- La page 404 renvoie vers l’accueil et le hub Métiers.

## 9. Sources et validation factuelle

Avant rédaction définitive, chaque persona fait l’objet d’une recherche ciblée. Les sources prioritaires sont :

1. organismes professionnels et institutions du droit ;
2. référentiels métier publics ou organismes d’orientation ;
3. CNIL pour les sujets données et IA ;
4. documents officiels sur les usages responsables de l’IA ;
5. sources professionnelles secondaires seulement lorsque les sources primaires ne décrivent pas le rôle.

Les sources communes de conception comprennent :

- Google Search Central, « Creating helpful, reliable, people-first content » : https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Google Search Central, « Spam policies » : https://developers.google.com/search/docs/essentials/spam-policies
- Onisep, « Secrétaire juridique » : https://www.onisep.fr/ressources/univers-metier/metiers/secretaire-juridique
- CNB, « Guide pratique — utilisation des systèmes d’intelligence artificielle générative » : https://www.cnb.avocat.fr/fr/actualites/guide-pratique-utilisation-des-systemes-dintelligence-artificielle-generative-ia
- CNIL, dossier « Intelligence artificielle » : https://www.cnil.fr/fr/intelligence-artificielle

Les affirmations propres aux tâches d’un rôle sont sourcées dans la page correspondante. Les exemples proposés par Nicolas sont identifiés comme exemples de diagnostic, pas comme pratiques universelles ou résultats démontrés.

## 10. Formulaire et flux utilisateur

Le CTA de toutes les pages mène au formulaire de l’accueil. Le formulaire :

- ne transmet aucune donnée ;
- génère un résumé dans le navigateur ;
- rappelle de ne pas inclure de donnée confidentielle ;
- conserve le même vocabulaire sur toutes les pages.

Le futur choix d’un canal de contact est hors périmètre de cette version. Il nécessitera une décision séparée sur l’adresse, le service utilisé, les mentions d’information et la conservation des données.

## 11. Erreurs et cas limites

- Persona inconnue : aucune page n’est générée ; le build échoue avant publication.
- Slug dupliqué : échec du build.
- Champ obligatoire absent : échec du build avec le fichier et le champ concernés.
- Lien interne inexistant : échec des tests.
- Source absente : le build complet échoue. Si un rôle ne peut pas être documenté ou distingué, la taxonomie revient en revue avant publication ; la version ne publie pas silencieusement moins de quinze personas.
- JavaScript indisponible : la navigation et le contenu restent accessibles ; seul le résumé interactif ne fonctionne pas.
- URL inconnue en production : page 404 avec navigation utile.

## 12. Tests et critères d’acceptation

### Tests automatisés

- Validation du schéma des quinze fichiers persona.
- Unicité des slugs, titres, meta descriptions et exemples de pilote.
- Génération reproductible de l’ensemble du dossier `/docs`.
- Présence d’un `title`, d’une description, d’une canonique et d’un `h1` par page.
- Vérification de tous les liens internes.
- Vérification des chemins CSS et JavaScript.
- Vérification que le sitemap correspond exactement aux pages canoniques.
- Recherche de formulations interdites : garantie de conformité, autonomie juridique, gain chiffré non sourcé.
- Absence de formulaire réseau, `fetch`, `XMLHttpRequest` ou service externe non autorisé.

### Vérifications dans un navigateur

- Accueil, hub, trois personas représentatives et page 404 sur ordinateur et mobile.
- Navigation clavier et focus visible.
- Aucun débordement horizontal.
- Formulaire et génération du résumé.
- Préférence de réduction des animations respectée.

### Vérification après publication

- GitHub Pages publie depuis `main:/docs`.
- Toutes les URL du sitemap répondent en HTTP 200.
- Les titres et canoniques de la version publique correspondent aux fichiers générés.
- Aucun fichier de suivi, contenu du vault ou brouillon de recherche n’est publié.

### Sécurité du déploiement

- La version `/docs` est construite et testée avant toute modification du réglage GitHub Pages.
- Le site actuel publié depuis la racine reste actif jusqu’à ce que `/docs` soit complet.
- Le réglage Pages ne bascule vers `main:/docs` qu’après vérification locale de toutes les URL.
- Après bascule, le site public est parcouru depuis le sitemap. En cas d’échec, la source Pages revient temporairement à `main:/` plutôt que de laisser un site incomplet.

## 13. Hors périmètre

- Blog ou publication automatique d’actualités.
- Pages par ville, domaine du droit ou combinaison persona × tâche.
- Traductions.
- Analytics, pixels publicitaires ou CRM.
- Formulaire envoyé à un tiers.
- Témoignages, études de cas ou prix non validés.
- Automatisation métier effectivement déployée chez un cabinet.

## 14. Définition de terminé

La version est terminée lorsque les quinze pages persona et le hub sont générés, testés, relus, publiés et accessibles ; que leur contenu est suffisamment distinct et sourcé ; que l’accueil reste commercialement cohérent ; et qu’aucune affirmation non vérifiée ou donnée interne n’est exposée.
