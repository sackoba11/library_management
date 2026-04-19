from odoo import models, fields, api

class LibraryCategory(models.Model):
    
    # ============================================================
    # IDENTIFIANTS DU MODÈLE
    # ============================================================
    
    _name = 'library.category'          # Nom technique du modèle
                                        # → crée la table "library_category" en BDD
    
    _description = 'Catégorie de livre' # Description lisible par l'humain
    
    _order = 'name asc'                 # Tri par défaut : alphabétique
    
    _parent_store = True                # Active la hiérarchie parent/enfant
    
    # ============================================================
    # CHAMPS
    # ============================================================
    
    name = fields.Char(
        string='Nom',
        required=True,          # Champ obligatoire
        translate=True,         # Peut être traduit en plusieurs langues
    )
    
    description = fields.Text(
        string='Description',
    )
    
    # Relation hiérarchique (catégorie parente)
    parent_id = fields.Many2one(
        comodel_name='library.category',
        string='Catégorie parente',
        ondelete='restrict',    # Interdit de supprimer si elle a des enfants
        index=True,             # Indexé pour les performances
    )
    
    # Champ technique requis par _parent_store
    parent_path = fields.Char(index=True)
    
    # Catégories enfants (inverse de parent_id)
    child_ids = fields.One2many(
        comodel_name='library.category',
        inverse_name='parent_id',
        string='Sous-catégories',
    )
    
    # Nombre de livres dans cette catégorie (champ calculé)
    book_count = fields.Integer(
        string='Nombre de livres',
        compute='_compute_book_count',
    )
    
    # ============================================================
    # CONTRAINTES SQL
    # ============================================================
    
    _sql_constraints = [
        # (identifiant, contrainte SQL, message d'erreur)
        ('name_uniq', 'UNIQUE(name)', 'Ce nom de catégorie existe déjà !')
    ]
    
    # ============================================================
    # MÉTHODES CALCULÉES
    # ============================================================
    
    @api.depends('child_ids')   # Se recalcule quand child_ids change
    def _compute_book_count(self):
        for category in self:
            category.book_count = self.env['library.book'].search_count([
                ('category_id', '=', category.id)
            ])