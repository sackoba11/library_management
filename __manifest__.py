# -*- coding: utf-8 -*-
{
    'name': 'Library Management',
    'version': '18.0.1.0.0',
    'category': 'Services',
    'summary': 'Gestion complète d\'une bibliothèque coopérative',
    'description': """
        Module de gestion de bibliothèque coopérative.
        Fonctionnalités :
        - Gestion des livres, auteurs et catégories
        - Gestion des membres
        - Gestion des emprunts avec workflow
        - Alertes automatiques de retard
        - Rapports PDF
    """,
    'author': 'SACKOBA',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',

    # Dépendances Odoo
    'depends': [
        'base',
        'mail',      # Pour les emails et le chatter
        'account',   # Pour les amendes éventuelles
    ],

    # Fichiers à charger (ordre important !)
    'data': [
        # Security en premier
        'security/library_security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/library_data.xml',
        'data/library_cron.xml',

        # Views
        'views/library_category_views.xml',
        'views/library_loan_views.xml',
        'views/library_book_views.xml',
        'views/library_author_views.xml',
        'views/library_member_views.xml',
        'views/library_menus.xml',

        # Wizard
        'wizard/library_loan_renew_views.xml',

        # Reports
        # 'report/library_loan_report.xml',
        # 'report/library_loan_report_template.xml',
    ],
    'demo': ['demo/library_demo.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}

