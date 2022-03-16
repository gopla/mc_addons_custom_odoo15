# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HistoriSO(models.Model):
    _name = 'mc_kontrak.histori_so'

    x_kontrak_id = fields.Many2one('mc_kontrak.mc_kontrak')
    x_order_id = fields.Many2one('sale.order')

    x_tgl_start = fields.Date(string='Tgl Start')
    x_tgl_end = fields.Date(string='Tgl End')
    x_item = fields.Many2one('product.product', string='Item')
    x_period = fields.Char(string='Period')
    x_status_pembayaran = fields.Char(string='Status Pembayaran')
    x_note = fields.Text(string='Note')
