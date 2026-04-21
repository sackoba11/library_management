from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LibraryBook(models.Model):
    
    _name = 'library.book'
    _description = 'Livre'
    _order = 'title asc'
    _rec_name = 'title'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Active le chatter
    
    # ============================================================
    # CHAMPS D'IDENTIFICATION
    # ============================================================
    
    title = fields.Char(
        string='Titre',
        required=True,
        tracking=True,      # Suit les changements dans le chatter
    )
    
    isbn = fields.Char(
        string='ISBN',
        size=13,            # Longueur maximale
    )
    
    cover_image = fields.Binary(
        string='Couverture',
        attachment=True,
    )
    
    # ============================================================
    # CHAMPS DE CLASSIFICATION
    # ============================================================
    
    author_id = fields.Many2one(
        comodel_name='library.author',
        string='Auteur',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    
    # Many2many : un livre peut avoir plusieurs catégories
    # et une catégorie peut contenir plusieurs livres
    category_id = fields.Many2one(
        comodel_name='library.category',
        string='Catégorie',
        tracking=True,
    )
    
    language = fields.Selection(
        selection=[
            ('fr', 'Français'),
            ('en', 'Anglais'),
            ('es', 'Espagnol'),
            ('ar', 'Arabe'),
            ('other', 'Autre'),
        ],
        string='Langue',
        default='fr',
    )
    
    publisher = fields.Char(
        string='Éditeur',
    )
    
    publish_date = fields.Date(
        string='Date de publication',
    )
    
    pages = fields.Integer(
        string='Nombre de pages',
    )
    
    description = fields.Text(
        string='Résumé',
    )
    
    # ============================================================
    # CHAMPS DE GESTION DU STOCK
    # ============================================================
    
    total_copies = fields.Integer(
        string='Nombre total d\'exemplaires',
        default=1,
        required=True,
    )
    
    # Champ calculé : exemplaires actuellement empruntés
    borrowed_copies = fields.Integer(
        string='Exemplaires empruntés',
        compute='_compute_copies',
    )
    
    # Champ calculé : exemplaires disponibles
    available_copies = fields.Integer(
        string='Exemplaires disponibles',
        compute='_compute_copies',
        store=True,
    )
    
    # Champ calculé : est-ce que le livre est disponible ?
    is_available = fields.Boolean(
        string='Disponible',
        compute='_compute_copies',
        store=True,
    )
    
    # Relation vers les emprunts (définie ici pour référence)
    loan_ids = fields.One2many(
        comodel_name='library.loan',
        inverse_name='book_id',
        string='Emprunts',
    )
    
    # ============================================================
    # CONTRAINTES SQL
    # ============================================================
    
    _sql_constraints = [
        ('isbn_uniq', 'UNIQUE(isbn)', 'Cet ISBN existe déjà !'),
        ('total_copies_positive',
         'CHECK(total_copies > 0)',
         'Le nombre d\'exemplaires doit être supérieur à 0 !'),
    ]
    
    # ============================================================
    # MÉTHODES CALCULÉES
    # ============================================================
    
    @api.depends('loan_ids', 'loan_ids.state', 'total_copies')
    def _compute_copies(self):
        for book in self:
            # Compter les emprunts actifs (statut = 'borrowed')
            borrowed = len(book.loan_ids.filtered(
                lambda l: l.state == 'borrowed'
            ))
            book.borrowed_copies = borrowed
            book.available_copies = book.total_copies - borrowed
            book.is_available = book.available_copies > 0
    
    # ============================================================
    # CONTRAINTES PYTHON
    # ============================================================
    
    @api.constrains('total_copies')
    def _check_total_copies(self):
        for book in self:
            if book.total_copies < 1:
                raise ValidationError(
                    "Un livre doit avoir au moins 1 exemplaire !"
                )
    
    @api.constrains('isbn')
    def _check_isbn(self):
        for book in self:
            if book.isbn and len(book.isbn) not in [10, 13]:
                raise ValidationError(
                    "L'ISBN doit contenir 10 ou 13 chiffres !"
                )
    
    # ============================================================
    # MÉTHODES UTILITAIRES
    # ============================================================
    
    # def name_get()(self):
    #     """Personnalise l'affichage du livre dans les listes déroulantes"""
    #     result = []
    #     for book in self:
    #         name = f"[{book.isbn}] {book.title}" if book.isbn else book.title
    #         result.append((book.id, name))
    #     return result

    @api.depends('title', 'isbn')
    def _compute_display_name(self):
        for rec in self:
            if rec.isbn:
                rec.display_name = f"[{rec.isbn}] {rec.title}"
            else:
                rec.display_name = rec.title