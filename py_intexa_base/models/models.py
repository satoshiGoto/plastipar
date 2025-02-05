# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class IrSequence(models.Model):
    _inherit = 'ir.sequence.date_range'

    number_ini = fields.Integer(string="Numero Inicial", required=True)
    number_max = fields.Integer(string="Max. Numeros", required=True)
    number_used = fields.Integer(string="Numeros Usados", required=True, default=0)
    timbrado = fields.Char(string="Nro. Timbrado", required=True, default=0)

    def _next(self):
        timbrado = self.env['account.journal'].search([
            ('sequence_id', '=', self.id)], limit=1)
        if timbrado.req_seq_ctrl:
            if self.number_used >= self.number_max:
                raise ValidationError(_('Se ha llenado la cuota del talonario. Configure la secuencia.'))
            self.number_used += 1
            res = super(IrSequence, self)._next()
            return res
        if not timbrado.req_seq_ctrl:
            res = super(IrSequence, self)._next()
            return res

    @api.constrains('number_max')
    def check_max_folios(self):
        for record in self:
            if record.number_max <= 0:
                raise ValidationError(_('Max numeros debe ser mayor que cero'))
            if record.number_used < 0:
                raise ValidationError(_('Numeros Usados debe ser positivo'))
