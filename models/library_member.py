from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class LibraryMember(models.Model):
    
    # ============================================================
    # HÉRITAGE : on étend res.partner
    # ============================================================
    
    _inherit = 'res.partner'
    # Pas de _name → on modifie le modèle existant
    # La table res_partner reçoit nos nouveaux champs
    
    # ============================================================
    # CHAMPS SPÉCIFIQUES AU MEMBRE
    # ============================================================
    
    # Indique si ce partenaire est un membre de la bibliothèque
    is_library_member = fields.Boolean(
        string='Membre de la bibliothèque',
        default=False,
    )
    
    # Numéro de carte de membre (unique)
    member_number = fields.Char(
        string='Numéro de membre',
        copy=False,         # Ne pas copier ce champ si on duplique
        readonly=True,      # Généré automatiquement
    )
    
    # Date d'adhésion
    membership_start = fields.Date(
        string='Date d\'adhésion',
        default=fields.Date.today,  # Par défaut : aujourd'hui
    )
    
    # Date d'expiration de la carte
    membership_expiry = fields.Date(
        string='Date d\'expiration',
    )
    
    # Statut de l'adhésion (calculé)
    membership_state = fields.Selection(
        selection=[
            ('draft', 'Non membre'),
            ('active', 'Actif'),
            ('expired', 'Expiré'),
            ('suspended', 'Suspendu'),
        ],
        string='Statut adhésion',
        compute='_compute_membership_state',
        store=True,
        default='draft',
    )
    
    # Nombre maximum d'emprunts autorisés
    max_loans = fields.Integer(
        string='Emprunts maximum',
        default=3,
    )
    
    # Notes sur le membre
    member_notes = fields.Text(
        string='Notes',
    )
    
    # ============================================================
    # RELATIONS
    # ============================================================
    
    # Tous les emprunts de ce membre
    loan_ids = fields.One2many(
        comodel_name='library.loan',
        inverse_name='member_id',
        string='Emprunts',
    )
    
    # Emprunts actifs uniquement (calculé)
    active_loan_count = fields.Integer(
        string='Emprunts en cours',
        compute='_compute_loan_stats',
    )
    
    # Total des emprunts
    total_loan_count = fields.Integer(
        string='Total emprunts',
        compute='_compute_loan_stats',
    )
    
    # Emprunts en retard
    overdue_loan_count = fields.Integer(
        string='Emprunts en retard',
        compute='_compute_loan_stats',
    )
    
    # ============================================================
    # CONTRAINTES SQL
    # ============================================================
    
    _sql_constraints = [
        (
            'member_number_uniq',
            'UNIQUE(member_number)',
            'Ce numéro de membre existe déjà !'
        ),
    ]
    
    # ============================================================
    # MÉTHODES CALCULÉES
    # ============================================================
    
    @api.depends('membership_expiry', 'is_library_member')
    def _compute_membership_state(self):
        today = date.today()
        for member in self:
            if not member.is_library_member:
                member.membership_state = 'draft'
            elif not member.membership_expiry:
                member.membership_state = 'active'
            elif member.membership_expiry < today:
                member.membership_state = 'expired'
            else:
                member.membership_state = 'active'
    
    @api.depends('loan_ids', 'loan_ids.state', 'loan_ids.return_date')
    def _compute_loan_stats(self):
        today = date.today()
        for member in self:
            loans = member.loan_ids
            
            # Emprunts actifs
            active = loans.filtered(lambda l: l.state == 'borrowed')
            member.active_loan_count = len(active)
            
            # Total emprunts
            member.total_loan_count = len(loans)
            
            # Emprunts en retard
            overdue = loans.filtered(
                lambda l: l.state == 'borrowed' 
                and l.expected_return_date 
                and l.expected_return_date < today or l.state == 'overdue'
            )
            member.overdue_loan_count = len(overdue)
    
    # ============================================================
    # CONTRAINTES PYTHON
    # ============================================================
    
    @api.constrains('membership_start', 'membership_expiry')
    def _check_membership_dates(self):
        for member in self:
            if member.membership_start and member.membership_expiry:
                if member.membership_expiry < member.membership_start:
                    raise ValidationError(
                        "La date d'expiration ne peut pas être "
                        "antérieure à la date d'adhésion !"
                    )
    
    @api.constrains('max_loans')
    def _check_max_loans(self):
        for member in self:
            if member.max_loans < 1:
                raise ValidationError(
                    "Le nombre maximum d'emprunts doit être "
                    "au moins égal à 1 !"
                )
    
    # ============================================================
    # MÉTHODES MÉTIER
    # ============================================================
    
    def action_activate_membership(self):
        """Active l'adhésion du membre"""
        for member in self:
            member.write({
                'is_library_member': True,
                'membership_state': 'active',
            })
            # Générer le numéro de membre si pas encore fait
            if not member.member_number:
                member.member_number = self.env['ir.sequence'].next_by_code(
                    'library.member'
                )
    
    def action_suspend_membership(self):
        """Suspend l'adhésion du membre"""
        for member in self:
            member.membership_state = 'suspended'
    
    def can_borrow(self):
        """Vérifie si le membre peut emprunter un livre"""
        self.ensure_one()   # S'assure qu'on travaille sur 1 seul enregistrement
        
        if not self.is_library_member:
            raise ValidationError("Ce contact n'est pas membre !")
        
        if self.membership_state != 'active':
            raise ValidationError(
                f"L'adhésion du membre est '{self.membership_state}'. "
                f"Elle doit être active pour emprunter."
            )
        
        if self.active_loan_count >= self.max_loans:
            raise ValidationError(
                f"Ce membre a atteint sa limite de {self.max_loans} emprunts !"
            )
        
        if self.overdue_loan_count > 0:
            raise ValidationError(
                f"Ce membre a {self.overdue_loan_count} emprunt(s) en retard. "
                f"Il doit les retourner avant d'en emprunter de nouveaux."
            )
        
        return True
    
    # ============================================================
    # OVERRIDE DE MÉTHODES EXISTANTES
    # ============================================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override de create pour générer le numéro de membre"""
        records = super().create(vals_list)
        for record in records:
            if record.is_library_member and not record.member_number:
                record.member_number = self.env['ir.sequence'].next_by_code(
                    'library.member'
                ) or '/'
        return records