from odoo import models, fields, api

class LibraryAuthor(models.Model):
    
    _name = 'library.author'
    _description = 'Auteur'
    _order = 'name asc'
    
    # ============================================================
    # CHAMPS
    # ============================================================
    
    name = fields.Char(
        string='Nom complet',
        required=True,
    )
    
    biography = fields.Html(        # Champ HTML (éditeur riche)
        string='Biographie',
    )
    
    birth_date = fields.Date(
        string='Date de naissance',
    )
    
    death_date = fields.Date(
        string='Date de décès',
    )
    
    nationality = fields.Char(
        string='Nationalité',
    )
    
    photo = fields.Binary(          # Champ pour stocker une image
        string='Photo',
        attachment=True,            # Stocké comme pièce jointe (plus performant)
    )
    
    # Relation inverse : liste des livres de cet auteur
    book_ids = fields.One2many(
        comodel_name='library.book',
        inverse_name='author_id',
        string='Livres',
    )
    
    # Champ calculé : nombre de livres
    book_count = fields.Integer(
        string='Nombre de livres',
        compute='_compute_book_count',
        store=True,                 # Stocké en BDD (plus performant pour les tris)
    )
    
    # ============================================================
    # MÉTHODES CALCULÉES
    # ============================================================
    
    @api.depends('book_ids')
    def _compute_book_count(self):
        for author in self:
            author.book_count = len(author.book_ids)
    
    # ============================================================
    # CONTRAINTES PYTHON
    # ============================================================
    
    @api.constrains('birth_date', 'death_date')
    def _check_dates(self):
        for author in self:
            if author.birth_date and author.death_date:
                if author.death_date < author.birth_date:
                    raise models.ValidationError(
                        "La date de décès ne peut pas être "
                        "antérieure à la date de naissance !"
                    )