# UniSphere — Plateforme universitaire

Plateforme Django (**MVT**) pour une faculté / université (type ESPRIT).

**Rôles séparés :**
- **Étudiant** : consulte ses modules (affectés selon son **niveau scolaire**), passe les quiz, reçoit les notifications. **Ne peut pas** créer / modifier / supprimer de modules.
- **Enseignant** : responsable de ses modules — CRUD, ressources, quiz, statuts.
- **Admin** : accès Django Admin + enseignant.

---

## Démarrage

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Ouvrir : **http://127.0.0.1:8000/**  
Après connexion, redirection automatique selon le rôle (`/espace/`).

---

## Liens d’accès

| Espace | URL |
|--------|-----|
| Accueil public | http://127.0.0.1:8000/ |
| Connexion | http://127.0.0.1:8000/connexion/ |
| Redirection selon rôle | http://127.0.0.1:8000/espace/ |
| **Inscription étudiant** (choix filière/spécialité) | http://127.0.0.1:8000/inscription/ |
| **Espace étudiant** (sidebar + Chart.js) | http://127.0.0.1:8000/etudiant/ |
| Quiz étudiant | http://127.0.0.1:8000/etudiant/quiz/ |
| Résultats étudiant | http://127.0.0.1:8000/etudiant/resultats/ |
| **Espace enseignant** (sidebar + Chart.js) | http://127.0.0.1:8000/back/ |
| Étudiants de l’enseignant | http://127.0.0.1:8000/back/etudiants/ |
| **Console admin** (gère tout + Chart.js) | http://127.0.0.1:8000/console/ |
| Utilisateurs (admin) | http://127.0.0.1:8000/console/utilisateurs/ |
| Modules globaux (admin) | http://127.0.0.1:8000/console/modules/ |
| Django Admin | http://127.0.0.1:8000/admin/ |

---

## Comptes démo (id / mot de passe)

### Administrateur

| Identifiant | Mot de passe | Rôle |
|-------------|--------------|------|
| `admin` | `Admin@2024` | Admin (front + back + `/admin/`) |

### Enseignants

| Identifiant | Mot de passe | Modules |
|-------------|--------------|---------|
| `enseignant` | `edu2024` | INF101, INF220, INF310 |
| `enseignant2` | `edu2024` | MAT150, ANG110 (brouillon) |

### Étudiants (parcours différents)

| Identifiant | Mot de passe | Parcours | Ex. modules affectés |
|-------------|--------------|----------|----------------------|
| `etudiant1` | `etu2024` | **1A** (TC Info) | INF101, MAT150 |
| `etudiant2` | `etu2024` | **2A** (TC Info) | INF210 |
| `etudiant3` | `etu2024` | **3IA** | IA320 (ML) |
| `etudiant4` | `etu2024` | **4A-FINTECH** | FIN410 |
| `etudiant_em` | `etu2024` | **1EM** | EM110 |
| `etudiant_gc` | `etu2024` | **1GC** | GC110 |

**Inscription libre :** http://127.0.0.1:8000/inscription/  
→ choix filière (Info / EM / GC) puis année/spécialité.

### Parcours supportés
- **Info :** 1A, 2A (TC) · 3A, 3IA · 4A/5A Fintech, DAS-info, SSA, Actuariat  
- **EM :** 1EM, 2EM, 3EM · 4A/5A OGI, MecaT, Option Air  
- **GC :** 1GC → 5GC

---

## Règles métier (rôles)

| Action | Étudiant | Enseignant |
|--------|----------|------------|
| Voir modules de son niveau | Oui | — |
| Créer / modifier / supprimer un module | **Non** | Oui (ses modules) |
| Gérer ressources & quiz | **Non** | Oui |
| Passer un quiz | Oui | Non (espace enseignant) |
| Notifications | Oui | Oui |

L’affectation des modules se fait **automatiquement** selon `academic_level` de l’étudiant = `level` du module publié.

---

## Recréer les données

```bash
python manage.py seed_demo
```
