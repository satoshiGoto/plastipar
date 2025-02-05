# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime
from odoo.exceptions import ValidationError


class WizardDeliveryNote(models.TransientModel):
    _name = 'wizard.remision'
    _description = "Asignación de Nro. Remisión"

    picking_id = fields.Many2one('stock.picking', string="Envio")
    assign_number = fields.Char(compute='get_stamp_number', string="Esta remisión tendrá el numero:")
    company_id = fields.Many2one('res.company', 'Compañía', index=True, default=lambda self: self.env.company)

    @api.model
    def _get_stamp_journal(self):
        journal = self.env['account.journal.stamped'].search([['type', '=', 2], ['state', '=', 'active'],
                                                              ['company_id', '=', self.company_id.id]])
        return journal

    stamp_journal = fields.Many2one('account.journal.stamped', string="Talonario", default=_get_stamp_journal,
                                    domain=[('type', '=', 2), ('state', '=', 'active')])

    @api.depends('stamp_journal', 'stamp_journal.current_number')
    def get_stamp_number(self):
        for record in self:
            if record.stamp_journal:
                d1 = datetime.strptime(str(datetime.now().date()), '%Y-%m-%d')
                d2 = datetime.strptime(str(record.stamp_journal.date_range_end), '%Y-%m-%d')
                d3 = datetime.strptime(str(record.stamp_journal.date_range_ini), '%Y-%m-%d')
                daysDiff = (d2 - d1).days
                dias_anti = (d3 - d1).days
                if daysDiff < 0:
                    raise ValidationError('Timbrado ya se encuentra vencido.')
                elif dias_anti > 0:
                    raise ValidationError('Fecha inicio de timbrado es mayor a la fecha actual')
                estab = record.stamp_journal.establishment_code
                exp_point = record.stamp_journal.shipping_point
                current_number = record.stamp_journal.current_number + 1
                nro_s = str(current_number)
                nro_final = nro_s.zfill(7)
                record.assign_number = str(estab) + '-' + str(exp_point) + '-' + str(nro_final)
            else:
                record.assign_number = 0

    def procesar(self):
        for record in self:
            d1 = datetime.strptime(str(datetime.now().date()), '%Y-%m-%d')
            d2 = datetime.strptime(str(record.stamp_journal.date_range_end), '%Y-%m-%d')
            d3 = datetime.strptime(str(record.stamp_journal.date_range_ini), '%Y-%m-%d')
            daysDiff = (d2 - d1).days
            dias_anti = (d3 - d1).days
            if daysDiff < 0:
                raise ValidationError('Timbrado ya se encuentra vencido.')
            elif dias_anti > 0:
                raise ValidationError('Fecha inicio de timbrado es may(or a la fecha actual')
            estab = record.stamp_journal.establishment_code
            exp_point = record.stamp_journal.shipping_point
            nro = record.stamp_journal.current_number + 1
            nro_s = str(nro)
            nro_final = nro_s.zfill(7)
            remision = str(estab) + '-' + str(exp_point) + '-' + str(nro_final)
            record.picking_id.write({'remision': remision, 'stamp_journal_timb': record.stamp_journal.name,
                                     'stamp_journal': record.stamp_journal.id})
            record.stamp_journal.write({'number_used': record.stamp_journal.current_number,
                                        'current_number': record.stamp_journal.current_number + 1})

            am_vals_list = []
            lineas_remision = []
            tipotransaccion = ''
            pyg = self.env['res.currency'].search([('name', '=', 'PYG')])
            for rec in record.picking_id:
                for line in rec.move_ids_without_package:
                    tipo_transaccion_dict = {'product': '1', 'service': '2'}
                    tipotransaccion = tipo_transaccion_dict.get(line.product_id.detailed_type, '')
                    # impuesto = line.price_total - line.price_subtotal
                    line_vals = {
                        'codigo': line.product_id.default_code,
                        'descripcion': line.description_picking,
                        'unidad_medida': 'UNI',
                        'cantidad': str(line.quantity_done),
                    }
                    lineas_remision.append((0, 0, line_vals))
                if rec.partner_id.is_proveedor:
                    tipooperacion = '3'
                elif '-' in rec.partner_id.vat:
                    tipooperacion = '1'
                elif '-' not in rec.partner_id.vat:
                    tipooperacion = '2'
                else:
                    tipooperacion = '4'
                move_vals = {
                    'picking_id': rec.id,
                    'move_type': 'picking',
                    'state': 'done',
                    'cliente': rec.partner_id.name,
                    'nom_fantasia': rec.partner_id.nom_fantasia,
                    'is_proveedor': rec.partner_id.is_proveedor,
                    'tipo_documento_cli': rec.partner_id.tipo_documento,
                    'num_casa': rec.partner_id.num_casa,
                    'moneda': pyg.name,
                    'tipoemision': '1',
                    'tipotransaccion': tipotransaccion,
                    'tipooperacion': tipooperacion,
                    'company_type': rec.partner_id.company_type,
                    'nro_documento': rec.partner_id.vat,
                    'ciudad': rec.partner_id.city,
                    'pais': rec.partner_id.country_id.code_alpha3 if rec.partner_id.country_id else 'PRY',
                    'departamento': rec.partner_id.state_id.name,
                    'company_id': rec.company_id.id,
                    'nro_factura': remision,
                    'fecha_factura': rec.date_done.date(),
                    'fecha_vcto_factura': rec.date_done.date(),
                    'timbrado': record.stamp_journal.name,
                    'descripcion': rec.note,
                    'establecimiento': estab,
                    'punto_expedicion': exp_point,
                    'numero': nro_final,
                    'lineas_factura': lineas_remision,
                    'iMotEmiNR': rec.iMotEmiNR,
                    'dDesMotEmiNR': rec.dDesMotEmiNR,
                    'iRespEmiNR': rec.iRespEmiNR,
                    'dDesRespEmiNR': rec.dDesRespEmiNR,
                    'dKmR': rec.dKmR,
                    'dFecEm': rec.dFecEm,
                    'iTipTrans': rec.iTipTrans,
                    'dDesTipTrans': rec.dDesTipTrans,
                    'iModTrans': rec.iModTrans,
                    'dDesModTrans': rec.dDesModTrans,
                    'iRespFlete': rec.iRespFlete,
                    'cCondNeg': rec.cCondNeg,
                    'dNuManif': rec.dNuManif,
                    'dNuDespImp': rec.dNuDespImp,
                    'dIniTras': rec.dIniTras,
                    'dFinTras': rec.dFinTras,
                    'cPaisDest': rec.cPaisDest,
                    'dDesPaisDest': rec.dDesPaisDest,
                    'dDirLocSal': rec.dDirLocSal,
                    'dNumCasSal': rec.dNumCasSal,
                    'dComp1Sal': rec.dComp1Sal,
                    'dComp2Sal': rec.dComp2Sal,
                    'dTelSal': rec.dTelSal,
                    'dDirLocEnt': rec.dDirLocEnt,
                    'dNumCasEnt': rec.dNumCasEnt,
                    'dComp1Ent': rec.dComp1Ent,
                    'dComp2Ent': rec.dComp2Ent,
                    'dTelEnt': rec.dTelEnt,
                    'dTiVehTras': rec.dTiVehTras,
                    'dMarVeh': rec.dMarVeh,
                    'dTipIdenVeh': rec.dTipIdenVeh,
                    'dNroIDVeh': rec.dNroIDVeh,
                    'dAdicVeh': rec.dAdicVeh,
                    'dNroMatVeh': rec.dNroMatVeh,
                    'dNroVuelo': rec.dNroVuelo,
                    'iNatTrans': rec.iNatTrans,
                    'dNomTrans': rec.dNomTrans,
                    'dRucTrans': rec.dRucTrans,
                    'dDVTrans': rec.dDVTrans,
                    'iTipIDTrans': rec.iTipIDTrans,
                    'dDTipIDTrans': rec.dDTipIDTrans,
                    'dNumIDTrans': rec.dNumIDTrans,
                    'cNacTrans': rec.cNacTrans,
                    'dDesNacTrans': rec.dDesNacTrans,
                    'dNumIDChof': rec.dNumIDChof,
                    'dNomChof': rec.dNomChof,
                    'dDomFisc': rec.dDomFisc,
                    'dDirChof': rec.dDirChof,
                    'dNombAg': rec.dNombAg,
                    'dRucAg': rec.dRucAg,
                    'dDVAg': rec.dDVAg,
                    'dDirAge': rec.dDirAge,
                    'cDepSal': rec.company_id.partner_id.state_id.code,
                    'dDesDepSal': rec.company_id.partner_id.state_id.name,
                    'cDisSal': rec.company_id.partner_id.district_id.code_district,
                    'dDesDisSal': rec.company_id.partner_id.district_id.name,
                    'cCiuSal': rec.company_id.partner_id.city_id.code_city,
                    'dDesCiuSal': rec.company_id.partner_id.city_id.name,
                    'cDepEnt': rec.partner_id.state_id.code,
                    'dDesDepEnt': rec.partner_id.state_id.name,
                    'cDisEnt': rec.partner_id.district_id.code_district,
                    'dDesDisEnt': rec.partner_id.district_id.name,
                    'cCiuEnt': rec.partner_id.city_id.code_city,
                    'dDesCiuEnt': rec.partner_id.city_id.name,
                }
                am_vals_list.append(move_vals)
                electronic_billings = self.env['electronic.billing'].sudo().create(am_vals_list)
                rec.billing_picking_id = electronic_billings
                electronic_billings.generar_codigo_seguridad()
                electronic_billings.generar_cdc()
                rec.cdc = electronic_billings.cdc
                rec.codigo_seguridad = electronic_billings.codigo_seguridad
