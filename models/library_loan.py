from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta

class LibraryLoan(models.Model):

    # ============================================================
    # IDENTIFIANTS DU MODÈLE
    # ============================================================

    _name = 'library.loan'
    _description = 'Emprunt de livre'
    _order = 'loan_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================
    # CHAMPS D'IDENTIFICATION
    # ============================================================

    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default='/',        # Sera remplacé par la séquence à la création
    )

    # ============================================================
    # CHAMP ÉTAT — Le cœur du workflow
    # ============================================================

    state = fields.Selection(
        selection=[
            ('draft',      'Brouillon'),
            ('borrowed',   'Emprunté'),
            ('returned',   'Retourné'),
            ('overdue',    'En retard'),
            ('cancelled',  'Annulé'),
        ],
        string='Statut',
        default='draft',
        required=True,
        tracking=True,      # Chaque changement d'état est tracé dans le chatter
        copy=False,
    )

    # ============================================================
    # RELATIONS PRINCIPALES
    # ============================================================

    member_id = fields.Many2one(
        comodel_name='res.partner',
        string='Membre',
        required=True,
        ondelete='restrict',
        tracking=True,
        domain=[('is_library_member', '=', True)],  # Filtre : membres seulement
    )

    book_id = fields.Many2one(
        comodel_name='library.book',
        string='Livre',
        required=True,
        ondelete='restrict',
        tracking=True,
    )

    # ============================================================
    # CHAMPS DE DATES
    # ============================================================

    loan_date = fields.Date(
        string='Date d\'emprunt',
        default=fields.Date.today,
        required=True,
        tracking=True,
    )

    expected_return_date = fields.Date(
        string='Date de retour prévue',
        required=True,
        tracking=True,
    )

    return_date = fields.Date(
        string='Date de retour effective',
        readonly=True,
        tracking=True,
        copy=False,
    )

    # ============================================================
    # CHAMPS CALCULÉS
    # ============================================================

    # Nombre de jours d'emprunt prévus
    loan_duration = fields.Integer(
        string='Durée (jours)',
        compute='_compute_loan_duration',
        store=True,
    )

    # Nombre de jours de retard
    delay_days = fields.Integer(
        string='Jours de retard',
        compute='_compute_delay',
        store=True,
    )

    # Montant de l'amende
    fine_amount = fields.Float(
        string='Amende (FCFA)',
        compute='_compute_fine',
        store=True,
        digits=(10, 0),     # 10 chiffres, 0 décimales
        groups='library_management.group_library_librarian',
    )

    # Est-ce en retard ?
    is_overdue = fields.Boolean(
        string='En retard',
        compute='_compute_delay',
        store=True,
    )

    # Nombre de renouvellements
    renewal_count = fields.Integer(
        string='Nombre de renouvellements',
        default=0,
        readonly=True,
    )

    notes = fields.Text(
        string='Notes',
    )

    # ============================================================
    # CONSTANTES
    # ============================================================

    # Tarif amende par jour de retard
    FINE_PER_DAY = 100      # 100 FCFA par jour
    MAX_RENEWALS = 2        # Maximum 2 renouvellements

    # ============================================================
    # CONTRAINTES SQL
    # ============================================================

    _sql_constraints = [
        (
            'name_uniq',
            'UNIQUE(name)',
            'La référence de cet emprunt existe déjà !'
        ),
    ]

    # ============================================================
    # MÉTHODES CALCULÉES
    # ============================================================

    @api.depends('loan_date', 'expected_return_date')
    def _compute_loan_duration(self):
        for loan in self:
            if loan.loan_date and loan.expected_return_date:
                delta = loan.expected_return_date - loan.loan_date
                loan.loan_duration = delta.days
            else:
                loan.loan_duration = 0

    @api.depends('state', 'expected_return_date', 'return_date')
    def _compute_delay(self):
        today = date.today()
        for loan in self:
            if loan.state in ('draft', 'cancelled'):
                loan.delay_days = 0
                loan.is_overdue = False

            elif loan.state == 'returned':
                # Retourné : calcul basé sur la date effective
                if loan.return_date and loan.expected_return_date:
                    delta = loan.return_date - loan.expected_return_date
                    loan.delay_days = max(0, delta.days)
                    loan.is_overdue = loan.delay_days > 0
                else:
                    loan.delay_days = 0
                    loan.is_overdue = False

            else:
                # Emprunté ou en retard : calcul par rapport à aujourd'hui
                if loan.expected_return_date:
                    delta = today - loan.expected_return_date
                    loan.delay_days = max(0, delta.days)
                    loan.is_overdue = loan.delay_days > 0
                else:
                    loan.delay_days = 0
                    loan.is_overdue = False

    @api.depends('delay_days')
    def _compute_fine(self):
        for loan in self:
            loan.fine_amount = loan.delay_days * self.FINE_PER_DAY

    # ============================================================
    # ONCHANGE — Réaction en temps réel dans le formulaire
    # ============================================================

    @api.onchange('loan_date')
    def _onchange_loan_date(self):
        """Calcule automatiquement la date de retour prévue
        (14 jours après l'emprunt par défaut)"""
        if self.loan_date:
            self.expected_return_date = self.loan_date + timedelta(days=14)

    @api.onchange('book_id')
    def _onchange_book_id(self):
        """Avertit si le livre n'est pas disponible"""
        if self.book_id and not self.book_id.is_available:
            # Retourne un warning visible dans le formulaire
            return {
                'warning': {
                    'title': 'Livre non disponible',
                    'message': (
                        f"Le livre '{self.book_id.title}' n'a plus "
                        f"d'exemplaires disponibles !"
                    ),
                }
            }

    # ============================================================
    # CONTRAINTES PYTHON
    # ============================================================

    @api.constrains('loan_date', 'expected_return_date')
    def _check_dates(self):
        for loan in self:
            if loan.loan_date and loan.expected_return_date:
                if loan.expected_return_date < loan.loan_date:
                    raise ValidationError(
                        "La date de retour prévue ne peut pas être "
                        "antérieure à la date d'emprunt !"
                    )

    @api.constrains('book_id', 'state')
    def _check_book_availability(self):
        for loan in self:
            if loan.state == 'borrowed':
                if not loan.book_id.is_available:
                    raise ValidationError(
                        f"Le livre '{loan.book_id.title}' "
                        f"n'est plus disponible !"
                    )

    # ============================================================
    # ACTIONS DU WORKFLOW
    # ============================================================

    def action_confirm(self):
        """Brouillon → Emprunté"""
        for loan in self:

            # 1. Vérifier que le membre peut emprunter
            loan.member_id.can_borrow()

            # 2. Vérifier que le livre est disponible
            if not loan.book_id.is_available:
                raise UserError(
                    f"Le livre '{loan.book_id.title}' "
                    f"n'est plus disponible !"
                )

            # 3. Générer la référence si pas encore fait
            if loan.name == '/':
                loan.name = self.env['ir.sequence'].next_by_code(
                    'library.loan'
                ) or '/'

            # 4. Changer le statut
            loan.state = 'borrowed'

            # 5. Message dans le chatter
            loan.message_post(
                body=f"📚 Emprunt confirmé pour <b>{loan.member_id.name}</b> "
                     f"— Retour prévu le <b>{loan.expected_return_date}</b>"
            )

    def action_return(self):
        """Emprunté/En retard → Retourné"""
        for loan in self:
            if loan.state not in ('borrowed', 'overdue'):
                raise UserError(
                    "Seul un emprunt actif peut être retourné !"
                )

            # Enregistrer la date de retour effective
            loan.return_date = date.today()
            loan.state = 'returned'

            # Message dans le chatter
            message = f"✅ Livre retourné le <b>{loan.return_date}</b>"
            if loan.delay_days > 0:
                message += (
                    f"<br/>⚠️ Retard de <b>{loan.delay_days} jour(s)</b>"
                    f" — Amende : <b>{loan.fine_amount} FCFA</b>"
                )
            loan.message_post(body=message)

    def action_cancel(self):
        """Brouillon/Emprunté → Annulé"""
        for loan in self:
            if loan.state == 'returned':
                raise UserError(
                    "Un emprunt retourné ne peut pas être annulé !"
                )
            loan.state = 'cancelled'
            loan.message_post(body="❌ Emprunt annulé")

    def action_reset_draft(self):
        """Annulé → Brouillon (réinitialiser)"""
        for loan in self:
            if loan.state != 'cancelled':
                raise UserError(
                    "Seul un emprunt annulé peut être remis en brouillon !"
                )
            loan.state = 'draft'
            loan.return_date = False

    def action_renew_wizard(self):
        """Ouvre le wizard de renouvellement"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Renouveler l'emprunt",
            'res_model': 'library.loan.renew',
            'view_mode': 'form',
            'target': 'new',
            # On passe l'ID de l'emprunt dans le contexte
            # Le wizard le récupère via active_id
            'context': {
                'default_loan_id': self.id,
                'active_id': self.id,
                'active_ids': self.ids,
                'active_model': 'library.loan',
            },
        }
    # ============================================================
    # MÉTHODE APPELÉE PAR LE CRON (étape 11)
    # ============================================================

    @api.model
    def _check_overdue_loans(self):
        """Passe les emprunts en retard au statut 'overdue'
        Appelée automatiquement par le cron job"""
        today = date.today()

        # Chercher tous les emprunts actifs dont la date est dépassée
        overdue_loans = self.search([
            ('state', '=', 'borrowed'),
            ('expected_return_date', '<', today),
        ])

        if overdue_loans:
            overdue_loans.write({'state': 'overdue'})

            # Notifier chaque membre
            for loan in overdue_loans:
                loan.message_post(
                    body=(
                        f"⚠️ Cet emprunt est en retard de "
                        f"<b>{loan.delay_days} jour(s)</b>. "
                        f"Amende actuelle : <b>{loan.fine_amount} FCFA</b>"
                    )
                )

    # ============================================================
    # OVERRIDE CREATE
    # ============================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Génère la référence automatiquement"""
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'library.loan'
                ) or '/'
        return super().create(vals_list)