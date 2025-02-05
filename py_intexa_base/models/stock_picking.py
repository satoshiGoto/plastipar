# -*- coding: utf-8 -*-

from odoo import fields, models, exceptions, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class boleta_remision(models.Model):
    _inherit = "stock.picking"

    remision = fields.Char(string="Nota de Remision Nro.", copy=False)
    stamp_journal = fields.Many2one('account.journal.stamped', string="Talonario remision",
                                    domain=[('tipo_documento', '=', 2)], tracking=True, copy=False)
    stamp_journal_timb = fields.Char('Remision Timbrado', tracking=True, copy=False)

    # @api.multi
    def poner_remision(self):

        if self.remision and not self.user_has_groups('stock.group_stock_manager'):
            raise ValidationError(
                'Este albaran ya tiene un numero de remision asignado, '
                'no puede asignarle otro. Contacte al administrador')
        else:

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.remision',
                'context': {'default_picking_id': self.id},
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
            }
