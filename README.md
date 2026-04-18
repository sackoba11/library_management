# 📚 Library Management - Odoo 18 Module

Module Odoo 18 de gestion complète d’une bibliothèque coopérative.

Ce module permet d’administrer efficacement les livres, auteurs, catégories, membres et emprunts, avec automatisation des alertes de retard et génération de rapports PDF.

---

## 🚀 Fonctionnalités

### 📖 Gestion du catalogue
- Gestion des livres
- Gestion des auteurs
- Gestion des catégories
- Suivi de disponibilité des ouvrages

### 👥 Gestion des membres
- Création et suivi des membres
- Historique des emprunts
- Informations de contact

### 🔄 Gestion des emprunts
- Création d’emprunts
- Workflow de prêt / retour
- Renouvellement via assistant (wizard)
- Suivi des dates d’échéance

### ⏰ Automatisation
- Alertes automatiques de retard
- Tâches planifiées (cron jobs)

### 🧾 Rapports
- Génération de rapports PDF des emprunts

### 💬 Communication
- Intégration du chatter Odoo via `mail`

### 💰 Comptabilité
- Compatible avec `account` pour gestion d’éventuelles amendes

---

## 🛠️ Technologies utilisées

- Odoo 18
- Python
- XML
- PostgreSQL

---

## 📦 Dépendances

Ce module nécessite les modules Odoo suivants :

- `base`
- `mail`
- `account`

---

## 📁 Structure du module

```bash
library_management/
├── models/
├── security/
│   ├── library_security.xml
│   └── ir.model.access.csv
├── data/
│   └── library_cron.xml
├── views/
│   ├── library_category_views.xml
│   ├── library_author_views.xml
│   ├── library_book_views.xml
│   ├── library_member_views.xml
│   ├── library_loan_views.xml
│   └── library_menus.xml
├── wizard/
│   └── library_loan_renew_views.xml
├── report/
│   ├── library_loan_report.xml
│   └── library_loan_report_template.xml
└── __manifest__.py
```

## ⚙️ Installation
1. Copier le module dans le dossier addons :
```bash
addons/library_management
```

2. Redémarrer le serveur Odoo
3. Activer le mode développeur
4. Mettre à jour la liste des applications
5. Rechercher :
```bash
Library Management
```
6. Installer le module

📸 Aperçu Fonctionnel
- Tableau de bord bibliothèque
- Gestion des emprunts
- Liste des membres
- Rapports PDF
- Notifications automatiques

## 👨‍💻 Auteur

#### SACKOBA

## 📄 Licence

#### LGPL-3
