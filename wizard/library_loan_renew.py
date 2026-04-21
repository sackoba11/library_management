from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

class LibraryLoanRenew(models.TransientModel):

    # ============================================================
    # IDENTIFIANTS
    # ============================================================

    _name = 'library.loan.renew'
    _description = 'Wizard de renouvellement d\'emprunt'

    # ============================================================
    # CHAMPS
    # ============================================================

    # L'emprunt concerné
    # On récupère l'emprunt actif via le contexte
    loan_id = fields.Many2one(
        comodel_name='library.loan',
        string='Emprunt',
        required=True,
        # default : récupère l'emprunt depuis le contexte
        default=lambda self: self.env.context.get('default_loan_id')
                                or self.env.context.get('active_id'),
    )

    # Informations de l'emprunt (lecture seule, pour affichage)
    book_id = fields.Many2one(
        comodel_name='library.book',
        string='Livre',
        related='loan_id.book_id',  # Champ relié à l'emprunt
        readonly=True,
    )

    member_id = fields.Many2one(
        comodel_name='res.partner',
        string='Membre',
        related='loan_id.member_id',
        readonly=True,
    )

    current_return_date = fields.Date(
        string='Date de retour actuelle',
        related='loan_id.expected_return_date',
        readonly=True,
    )

    renewal_count = fields.Integer(
        string='Renouvellements effectués',
        related='loan_id.renewal_count',
        readonly=True,
    )

    # Paramètres du renouvellement
    duration_days = fields.Integer(
        string='Durée du renouvellement (jours)',
        required=True,
        default=7,
    )

    reason = fields.Text(
        string='Raison du renouvellement',
        placeholder='Pourquoi ce renouvellement ?'
    )

    # Date de retour calculée (après renouvellement)
    new_return_date = fields.Date(
        string='Nouvelle date de retour',
        compute='_compute_new_return_date',
        store=False,    # Pas besoin de stocker, c'est juste pour l'affichage
    )

    # ============================================================
    # CONSTANTES
    # ============================================================

    MAX_RENEWALS = 2        # Maximum 2 renouvellements autorisés
    MAX_DURATION = 30       # Maximum 30 jours par renouvellement

    # ============================================================
    # MÉTHODES CALCULÉES
    # ============================================================

    @api.depends('duration_days', 'current_return_date')
    def _compute_new_return_date(self):
        for wizard in self:
            if wizard.current_return_date and wizard.duration_days:
                wizard.new_return_date = (
                    wizard.current_return_date
                    + timedelta(days=wizard.duration_days)
                )
            else:
                wizard.new_return_date = False

    # ============================================================
    # ONCHANGE
    # ============================================================

    @api.onchange('duration_days')
    def _onchange_duration_days(self):
        """Avertit si la durée dépasse le maximum autorisé"""
        if self.duration_days and self.duration_days > self.MAX_DURATION:
            return {
                'warning': {
                    'title': 'Durée trop longue',
                    'message': (
                        f"La durée maximale de renouvellement "
                        f"est de {self.MAX_DURATION} jours !"
                    ),
                }
            }

    # ============================================================
    # CONTRAINTES PYTHON
    # ============================================================

    @api.constrains('duration_days')
    def _check_duration(self):
        for wizard in self:
            if wizard.duration_days <= 0:
                raise ValidationError(
                    "La durée du renouvellement doit être "
                    "supérieure à 0 !"
                )
            if wizard.duration_days > self.MAX_DURATION:
                raise ValidationError(
                    f"La durée du renouvellement ne peut pas "
                    f"dépasser {self.MAX_DURATION} jours !"
                )

    # ============================================================
    # ACTION PRINCIPALE DU WIZARD
    # ============================================================

    def action_renew(self):
        """
        Action principale : renouvelle l'emprunt
        Appelée quand l'utilisateur clique sur "Confirmer"
        """
        self.ensure_one()

        loan = self.loan_id

        # ── Vérification 1 : statut de l'emprunt
        if loan.state not in ('borrowed', 'overdue'):
            raise UserError(
                "Seul un emprunt actif peut être renouvelé !"
            )

        # ── Vérification 2 : nombre de renouvellements
        if loan.renewal_count >= self.MAX_RENEWALS:
            raise UserError(
                f"Cet emprunt a déjà été renouvelé "
                f"{loan.renewal_count} fois. "
                f"Le maximum autorisé est {self.MAX_RENEWALS} fois."
            )

        # ── Vérification 3 : durée valide
        if not self.duration_days or self.duration_days <= 0:
            raise UserError(
                "Veuillez saisir une durée valide !"
            )

        # ── Calcul de la nouvelle date
        new_date = (
            loan.expected_return_date
            + timedelta(days=self.duration_days)
        )

        # ── Mise à jour de l'emprunt
        loan.write({
            'expected_return_date': new_date,
            'renewal_count': loan.renewal_count + 1,
            # Si l'emprunt était en retard, on repasse à "borrowed"
            'state': 'borrowed' if loan.state == 'overdue' else loan.state,
        })

        # ── Message dans le chatter
        loan.message_post(
            body=(
                f"🔄 Emprunt renouvelé pour <b>{self.duration_days} jours</b><br/>"
                f"📅 Nouvelle date de retour : <b>{new_date}</b><br/>"
                f"📝 Raison : {self.reason}<br/>"
                f"🔢 Renouvellement n°{loan.renewal_count}"
            )
        )

        # ── Fermer le wizard et revenir à l'emprunt
        # On retourne une action pour rester sur le formulaire
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'library.loan',
            'res_id': loan.id,
            'view_mode': 'form',
            'target': 'current',    # Remplace la vue actuelle
        }

    def action_cancel(self):
        """Ferme le wizard sans rien faire"""
        return {'type': 'ir.actions.act_window_close'}