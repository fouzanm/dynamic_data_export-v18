# -*- coding: utf-8 -*-
from odoo import fields, models


class WebhookExportLog(models.Model):
    _name = 'webhook.export.log'
    _order = 'create_date desc'
    _rec_name = 'webhook_id'

    webhook_id = fields.Many2one('webhook.config', string='Webhook', required=True)
    create_date = fields.Datetime('Export Date', readonly=True)
    status = fields.Selection([('success', 'Success'), ('failed', 'Failed')],
                              string='Status', required=True)
    record_count = fields.Integer('Records Exported', default=0)
    message = fields.Text('Message', help="Response or error message")
    data = fields.Text('Exported Data', help="JSON data that was exported")
