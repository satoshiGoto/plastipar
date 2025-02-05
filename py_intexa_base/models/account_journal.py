# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo import fields, models, api, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    establishment_code = fields.Char('Cod. Establecimiento',
                                     help='Numero de establecimiento que representa este diario', copy=False)
    shipping_point = fields.Char('Cod. Punto de Expedición', help='Punto de expedición que representa este diario',
                                 copy=False)
    py_sequence_ids = fields.One2many('ir.sequence', 'py_latam_journal_id', string="Secuencia", copy=False)
    req_doc = fields.Boolean('Control Documentos')
    check_cheq_diferido = fields.Boolean('Cheques Diferidos', default=False,
                                         help='si esta tildado, el diario activa en la forma'
                                              ' de pago los campos fecha y listado de banco')
    check_cheq_hoy = fields.Boolean('Cheques al día', default=False)
    diario_cheque = fields.Boolean('Diario Cheque', default=False)
    cheque_cobro = fields.Boolean('Cheque Tipo Cobro', default=False)
    cheque_pago = fields.Boolean('Cheques Tipo Pago', default=False)
    timbrado_id = fields.Many2one('account.journal.stamped', string='Timbrado', copy=False)

    _sql_constraints = [
        ('diario-timbrado-unico-type',
         'unique(timbrado_id, type, company_id)',
         "Otro diario ya cuenta con el mismo numero de timbrado, favor verificar!!")
    ]

    @staticmethod
    def _format(value):
        try:
            intvalue = int(value)
        except ValueError:
            raise ValidationError('Esperábamos un numero')
        return '{0:03}'.format(intvalue)

    @api.onchange('establishment_code')
    def onchange_point(self):
        self.ensure_one()
        self.establishment_code = self._format(self.establishment_code)

    @api.onchange('shipping_point')
    def onchange_code(self):
        self.ensure_one()
        self.shipping_point = self._format(self.shipping_point)

    # def _get_journal_codes(self):
    #     self.ensure_one()
    #     usual_codes = ['FAC', 'ND', 'NC', 'FACT', 'INV']
    #     internal_codes = ['AF', 'PLS', 'CING', 'VUI', 'CUI', 'NCI', 'SUEL']
    #     expo_codes = ['DESP', 'INV', 'FEXP']
    #     if self.type != 'sale':
    #         return []
    #     return usual_codes + internal_codes + expo_codes

    @api.model
    def create(self, values):
        """ Create Document sequences after create the journal
        """
        res = super().create(values)
        res._ctrm_py_create_document_sequences()
        return res

    def write(self, values):
        """ Update Document sequences after update journal
            si cambia alguno de los campos to_check, entonces regeneramos las
            secuencias.
        """
        to_check = set(['type', 'req_doc', 'timbrado_id'])
        res = super().write(values)
        if to_check.intersection(set(values.keys())):
            for rec in self:
                rec._ctrm_py_create_document_sequences()
        return res

    def _ctrm_py_create_document_sequences(self):
        """ IF Configuration change try to review if this can be done and then
            create / update the document sequences
        """
        self.ensure_one()
        if self.company_id.country_id != self.env.ref('base.py'):
            return True
        if not self.type == 'sale' or not self.req_doc:
            return False
        sequences = self.py_sequence_ids
        sequences.unlink()

        # Créate secuencia
        documents = self.env['account.tip.doc'].search([('internal_type', 'in', ('invoice', 'debit_note', 'credit_note')),
                                                        ('req_timbrado', '=', True)], limit=1)
        for document in documents:
            if self.py_sequence_ids.filtered(lambda x: x.id == document.id):
                continue
            sequences |= self.env['ir.sequence'].create(document._get_document_sequence_vals(self))
        return sequences
