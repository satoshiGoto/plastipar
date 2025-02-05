# For copyright and license notices, see __manifest__.py file in module root

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.move"

    py_timbrado_prov = fields.Char(string='Timbrado', help='Numero de timbrado')
    py_timbrado_prov_end = fields.Date(string='Validez Timbrado', help='Fecha de caducidad del timbrado del proveedor')
    remision = fields.Char(string='Nro de remito')
    timbrado_id = fields.Many2one('account.journal.stamped', help="Numero de timbrado que habilita la factura", string='Timbrado',
                                  copy=False)
    move_name = fields.Char(string="Cambiar número", readonly=False, default=False, copy=False,
                            help="""Forzar número de factura. Utilice este campo si no desea utilizar la numeración predeterminada. """, )

    def _add_doc(self):
        doc_obj = self.env['account.tip.doc'].search([('tipdoc', '=', 'purchase')])
        if doc_obj:
            tipodic = [('id', 'in', doc_obj.ids)]
        else:
            tipodic = [('id', '=', -1)]
        return tipodic

    tipdocgas = fields.Many2one("account.tip.doc", string="Tipo Documento", domain=_add_doc)

    def _add_doc_ing(self):
        doc_obj = self.env['account.tip.doc'].search([('tipdoc', '=', 'sale')])
        if doc_obj:
            tipodic = [('id', 'in', doc_obj.ids)]
        else:
            tipodic = [('id', '=', -1)]
        return tipodic

    tipdocing = fields.Many2one("account.tip.doc", string="Tipo Documento", domain=_add_doc_ing)

    def action_post(self):
        if self.state == 'draft':
            if self.move_type in ['out_invoice', 'out_refund']:
                self._validate_out_invoice()

            elif self.move_type in ['entry']:
                if self.move_name:
                    self.name = self.move_name
                    return super().action_post()
                else:
                    return super().action_post()
            elif self.move_type in ['in_invoice', 'in_refund']:
                if self.tipdocgas.req_timbrado:
                    self._validate_in_invoice()
                elif not self.tipdocgas.req_timbrado:
                    return super().action_post()

    def _validate_out_invoice(self):
        if not self.partner_id.vat:
            raise ValidationError(_('El RUC es requerido, en este caso no puede quedar en blanco'))

        if not self.timbrado_id:
            sequence_ids = self.journal_id.py_sequence_ids
            type_id = {'out_invoice': 1, 'out_refund': 4, 'debit_note': 6}.get(self.move_type, 0)

            seq = sequence_ids.filtered(lambda x: x.py_latam_journal_id.id == self.journal_id.id)
            proximo = seq.number_next_actual

            if self.journal_id.timbrado_id:
                domain = [('id', '=', self.journal_id.timbrado_id.id),
                          ('state', '=', 'active'),
                          ('company_id', '=', self.company_id.id)]
            else:
                domain = [('type', '=', type_id),
                          ('establishment_code', '=', self.journal_id.establishment_code),
                          ('shipping_point', '=', self.journal_id.shipping_point),
                          ('state', '=', 'active'),
                          ('company_id', '=', self.company_id.id)]

            timbrados = self.env['account.journal.stamped'].search(domain)
            self.timbrado_id = timbrados.id

            if not (timbrados.number_ini <= proximo <= timbrados.number_max):
                raise ValidationError(
                    _('El timbrado ya no es válido, el número de documento está fuera del rango.\n'
                      'El próximo número de factura es %s mientras que el rango de validez del timbrado es [%s - %s]') % (
                        proximo, timbrados.number_ini, timbrados.number_max))

            self.timbrado_id.state = 'no_active' if proximo == timbrados.number_max else 'active'
            self.timbrado_id.number_used = proximo
            self.timbrado_id.current_number = proximo + 1
            self.name = seq.next_by_id()
            return super().action_post()
        elif self.move_name:
            self.name = self.move_name
            return super().action_post()
        else:
            return super().action_post()

    def _validate_in_invoice(self):
        if not self.ref:
            raise ValidationError(_('La referencia es requerida, en este caso no puede quedar en blanco'))
        if not self.py_timbrado_prov or not self.py_timbrado_prov_end:
            raise ValidationError(_('El Timbrado y la fecha son requeridos, en este caso no pueden quedar en blanco'))

        if len(self.py_timbrado_prov) != 8 or not self.py_timbrado_prov.isdigit():
            raise ValidationError(_('El timbrado debe tener una longitud de ocho dígitos y ser numérico'))

        args = self.ref.split('-')
        if len(args) != 3:
            raise ValidationError(_('El número de documento debe tener tres partes separadas por guiones (-)'))

        suc, exp, number = args
        if not (3 == len(suc) == len(exp) == 3) or not (number.isdigit() and 7 == len(number)):
            raise ValidationError(_('El formato del número de documento es incorrecto\n'
                                    'Los siguientes son ejemplos de números validos:\n'
                                    '* 001-001-0000001\n'
                                    '* 003-001-0000087\n'
                                    '* 025-045-0000885'))

        if not (self.py_timbrado_prov_end >= self.invoice_date):
            raise ValidationError(_('La fecha de la factura no está dentro del rango de validez del timbrado.'))

        return super().action_post()
