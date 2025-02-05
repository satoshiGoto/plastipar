# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class AccountTipDoc(models.Model):
    _name = "account.tip.doc"
    _description = "Tipos de Documentos"

    name = fields.Char(string="Descripción")
    code = fields.Char(string="Código")
    code_hck = fields.Char(string="Código Hechauka")
    tipdoc = fields.Selection(string="Tipo Operacion", selection=[('sale', 'Ingreso'), ('purchase', 'Gasto')])
    vatbook = fields.Boolean('Libro IVA?')
    req_timbrado = fields.Boolean('Control Timbrado')
    internal_type = fields.Selection([('invoice', 'Factura'),
                                      ('debit_note', 'Nota de Debito'),
                                      ('credit_note', 'Nota de Crédito')], string="Tipo Documento")

    def _get_document_sequence_vals(self, journal):
        """ Values to create the sequences """
        values = {}
        values.update(
            {'name': 'Secuencia de %s %s-%s-' % (journal.name, journal.timbrado_id.establishment_code, journal.timbrado_id.shipping_point),
             'code': journal.code,
             'implementation': 'no_gap',
             'prefix': "%s-%s-" % (journal.timbrado_id.establishment_code, journal.timbrado_id.shipping_point),
             'suffix': '',
             'padding': 7,
             'number_next': journal.timbrado_id.current_number,
             'company_id': journal.company_id.id,
             'py_latam_journal_id': journal.id}
        )
        return values
