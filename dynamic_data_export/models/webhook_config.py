# -*- coding: utf-8 -*-
from odoo import api, fields, models
from markupsafe import Markup
import requests
import json


class WebhookConfig(models.Model):
    _name = 'webhook.config'
    _description = 'Webhook Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    url = fields.Char('Webhook URL', required=True)
    model_id = fields.Many2one('ir.model', string='Model',
                               ondelete='cascade', required=True,
                               domain=[('model', '=', 'sale.order')])
    field_ids = fields.Many2many('ir.model.fields', string='Fields to Export',
                                 domain="[('model_id', '=', model_id)]", copy=False,
                                 help="If no fields selected, all fields will be exported.")
    last_export = fields.Datetime('Last Export', readonly=True, copy=False)
    export_count = fields.Integer(compute='_compute_export_count')

    @api.depends('last_export')
    def _compute_export_count(self):
        """Compute the count of export records"""
        for record in self:
            record.export_count = self.env['webhook.export.log'].search_count([
                ('webhook_id', '=', record.id)
            ])

    def action_export_records(self):
        """Export records to the webhook endpoint"""
        self.ensure_one()
        domain = []
        # if self.last_export:
        #     domain = [('write_date', '>', self.last_export)]
        records = self.env[self.model_id.model].search(domain)
        if not records:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No records found to export',
                    'type': 'warning'
                }
            }

        export_data = []
        fields_to_export = self.field_ids.mapped('name') if self.field_ids else []
        for record in records:
            record_data = record.read()[0] if not fields_to_export else (
                record.read(fields_to_export))[0]
            record_data = self._clean_export_data(record_data)
            export_data.append(record_data)
        data = json.dumps(export_data, default=str)
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.url, headers=headers, data=data, timeout=10)
            status = 'success' if response.status_code in range(200, 300) else 'failed'
            message = f"HTTP Status: {response.status_code}"
            response_message = f'''
                <p style="color: #2E8B57;">
                    Exported {len(records)} records to {self.name} successfully!
                </p>'''
            self.write({'last_export': fields.Datetime.now()})

        except Exception as e:
            status = 'failed'
            response_message = f'''
                <p style="color: #D9534F;">
                    Failed to export data to {self.name}.
                </p>'''
            message = str(e)

        self.env['webhook.export.log'].create([{
            'webhook_id': self.id,
            'status': status,
            'record_count': len(records),
            'message': message,
            'data': data,
        }])
        self.message_post(body=Markup(f"<p>{response_message}</p>"))


    def _clean_export_data(self, data):
        """Clean data for export"""
        result = {}
        for key, value in data.items():
            if isinstance(value, tuple) and len(value) == 2:
                result[key] = {'id': value[0], 'name': value[1]}
            elif isinstance(value, list):
                if not value: continue
                model_name = self.model_id.model
                field_info = self.env[model_name]._fields.get(key)
                if field_info and field_info.type in ['one2many', 'many2many']:
                    relation_model = field_info.comodel_name
                    records = []
                    for record in self.env[relation_model].browse(value):
                        record_data = {'id': record.id}
                        if hasattr(record, 'name'):
                            record_data['name'] = record.name
                        records.append(record_data)
                    result[key] = records
                else:
                    result[key] = value
            else:
                result[key] = value
        return result

    def action_view_logs(self):
        """View export logs for this configuration"""
        self.ensure_one()
        return {
            'name': f'Export Logs: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'webhook.export.log',
            'view_mode': 'list,form',
            'domain': [('webhook_id', '=', self.id)],
        }
