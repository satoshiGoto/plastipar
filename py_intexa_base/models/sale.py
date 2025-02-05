from odoo import models


class SaleOrderWhat(models.Model):
    _inherit = "sale.order"

    def print_quotation(self):
        self.write({'state': "sent"})
        self.opportunity_id.write({'stage_id': 3})
        return self.env.ref('propaco_formatos.report_presupuesto').report_action(self)
