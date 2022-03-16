# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class mc_kontrak(models.Model):
    _name = 'mc_kontrak.mc_kontrak'

    # Field
    name = fields.Char(string='No Kontrak', readonly=True, default='New')
    mc_cust = fields.Many2one('res.partner', string='Customer')
    mc_pic_cust = fields.Char(string='PIC Customer')
    start_date = fields.Date(string='Start Date', readonly=True, store=True, default=fields.Datetime.now())
    end_date = fields.Date(string='End Date', readonly=False, copy=False)
    mc_total = fields.Float(string='Total', readonly=True, compute='total_harga', store=True)
    mc_isopen = fields.Boolean(default=True)

    so_count = fields.Integer(string='SO', compute='_count_so')

    # Relasi
    product_order_line = fields.One2many('mc_kontrak.product_order_line', 'kontrak_id', string='No Kontrak')

    @api.model
    def create(self, vals_list):
        vals_list['name'] = self.env['ir.sequence'].next_by_code('mc_kontrak.mc_kontrak')
        return super(mc_kontrak, self).create(vals_list)

    # Total Harga
    @api.depends('product_order_line')
    def total_harga(self):
        total = 0.00
        for rec in self.product_order_line:
            total += rec.mc_payment

        self.mc_total = total

    # Hitung berapa SO di Kontrak ini
    def _count_so(self):
        query = "SELECT COUNT(0) FROM public.sale_order where kontrak_id = %s " % self.id
        print(query)
        self.env.cr.execute(query)
        result = self.env.cr.fetchone()
        self.so_count = result[0]

    # Button untuk membuka related SO
    def action_view_so_button(self):
        action = self.env.ref('sale.action_quotations').read()[0]
        action['domain'] = [('kontrak_id', '=', self.id)]
        action['context'] = {}
        return action

    @api.depends('product_order_line')
    def _hitung_qty_belum_terpasang(self):
        for row in self.product_order_line:
            query = "SELECT SUM(x_mc_qty_terpasang) FROM public.sale_order_line WHERE kontrak_id = %s AND product_id = %s" % (
                self.id, row.product_id.id)

            self.env.cr.execute(query)
            result = self.env.cr.fetchone()

            print("SUM QTY TERPASANG : ", result[0])
            row.mc_qty_belum_terpasang = row.mc_qty_kontrak - result[0]
            row.mc_qty_terpasang = result[0]


class ProductOrderLine(models.Model):
    _name = 'mc_kontrak.product_order_line'

    # Relasi
    kontrak_id = fields.Many2one('mc_kontrak.mc_kontrak', string='No Kontrak', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    currency_id = fields.Many2one('res.currency')

    # Field
    mc_qty_kontrak = fields.Integer(string='Quantity Kontrak')
    mc_qty_terpasang = fields.Integer(string='Quantity Terpasang', default=0)
    mc_qty_belum_terpasang = fields.Integer(string='Quantity Belum Terpasang')
    mc_harga_produk = fields.Monetary(string='Standard Price')
    mc_harga_diskon = fields.Monetary(string='Discounted Price')
    mc_period = fields.Integer(string='Period')
    mc_period_info = fields.Selection([
        ('bulan', 'Bulan'),
        ('unit', 'Unit')
    ], string='Keterangan')
    mc_payment = fields.Float(string='Payment', readonly=True, compute='_hitung_subtotal', store=True)
    mc_total = fields.Float(string='Total', readonly=True, store=True)
    mc_isopen = fields.Boolean(default=True)

    # @api.depends('mc_qty_kontrak')
    # def _hitung_qty_blm_terpasang(self):
    #     self.mc_qty_belum_terpasang = self.mc_qty_kontrak

    @api.depends('mc_qty_kontrak', 'mc_harga_produk', 'mc_harga_diskon', 'mc_period', 'mc_period_info')
    def _hitung_subtotal(self):
        subtotal = 0
        grandtotal = 0

        for line in self:
            price = (line.mc_harga_produk - line.mc_harga_diskon) * line.mc_qty_kontrak * line.mc_period
            subtotal += price
            line.update({
                'mc_payment': price,
                'mc_qty_belum_terpasang': line.mc_qty_kontrak
            })

        grandtotal = subtotal
        self.mc_total = grandtotal

    @api.model
    def view_init(self, fields_list):
        print(fields_list)


class CustomSalesOrder(models.Model):
    _inherit = 'sale.order'
    _order = 'kontrak_id DESC'

    # Relasi
    kontrak_id = fields.Many2one('mc_kontrak.mc_kontrak', string='No Kontrak', required=True, ondelete='cascade')
    kontrak_product_line = fields.Many2one('mc_kontrak.product_order_line')

    x_order_line = fields.One2many('sale.order.line', 'order_id')
    x_mc_qty_kontrak = fields.Integer(string='Quantity Kontrak')
    x_mc_qty_terpasang = fields.Integer(string='Quantity Terpasang')
    x_mc_harga_produk = fields.Monetary(string='Standard Price')
    x_mc_isopen = fields.Boolean()

    def write(self, vals):
        if ('order_line' in vals):
            res = super(CustomSalesOrder, self).write(vals)
            arr_order_line = vals['order_line']

            so_line = self.x_order_line
            if so_line:
                i = 0
                for row in so_line:
                    print(i)
                    if arr_order_line[i][2]['x_mc_qty_terpasang']:
                        x_qty_terpasang = arr_order_line[i][2]['x_mc_qty_terpasang']
                        print('x_qty_terpasang = ', x_qty_terpasang)

                        query = "SELECT coalesce(SUM(sol.x_mc_qty_terpasang), 0) FROM public.sale_order so " \
                                "JOIN public.sale_order_line sol " \
                                "ON sol.order_id = so.id " \
                                "WHERE so.state NOT IN('cancel') AND " \
                                "sol.kontrak_line_id = %s AND " \
                                "sol.id != %s" % (row.kontrak_line_id.id, row.id)
                        print(query)
                        self.env.cr.execute(query)
                        x_qty_terpasang2 = self.env.cr.fetchone()[0]
                        print('x_qty_terpasang2 = ', x_qty_terpasang2)
                        total_terpasang = x_qty_terpasang + x_qty_terpasang2
                        print('total_terpasang = ', total_terpasang)

                        query = "UPDATE public.mc_kontrak_product_order_line SET mc_qty_terpasang = %s, " \
                                "mc_qty_belum_terpasang = (mc_qty_kontrak - %s) " \
                                "WHERE id = %s" % (total_terpasang, total_terpasang, row.kontrak_line_id.id)
                        self.env.cr.execute(query)
                        if query:
                            print('oke')
                    i = i + 1
                query = """
                    update mc_kontrak_mc_kontrak set
                    mc_isopen = False
                    where id = %s
                    and 0 = (
                        select SUM(mkpol.mc_qty_belum_terpasang) as mc_qty_belum_terpasang
                        from mc_kontrak_mc_kontrak mkmk
                        join mc_kontrak_product_order_line mkpol on mkpol.kontrak_id = mkmk.id
                        where mkmk.id = %s
                    )
                """ % (self.kontrak_id.id, self.kontrak_id.id)
                print(query)
                self.env.cr.execute(query)
            return res


    # Auto fill Order Line
    def insert_kontrak(self):
        # print('lsakdlsakd')
        print('insert kontrak func')
        kontrak_id = self.kontrak_id
        partner = self.partner_id
        terms = []

        kontrak_line = self.env['mc_kontrak.mc_kontrak'].search([('id', '=', kontrak_id.id)])
        if kontrak_line:
            for row in kontrak_line.product_order_line:
                values = {}
                product = row.product_id.id

                # Cek jika status produk open, masukkan ke SO
                if row.mc_isopen:
                    values['product_id'] = row.product_id.id
                    values['kontrak_line_id'] = row.id
                    values['x_mc_qty_kontrak'] = row.mc_qty_kontrak
                    values['x_mc_qty_terpasang'] = row.mc_qty_belum_terpasang
                    values['kontrak_id'] = kontrak_id.id
                    values['x_mc_harga_produk'] = row.mc_harga_produk
                    values['x_mc_isopen'] = row.mc_isopen
                    values['price_unit'] = row.mc_harga_produk
                    values['product_uom_qty'] = row.mc_qty_belum_terpasang

                    terms.append((0, 0, values))

        return self.update({'order_line': terms})

    def action_cancel(self):
        print('test cancel')
        query = """
            SELECT x_mc_qty_terpasang, kontrak_line_id  FROM sale_order_line sol 
            WHERE sol.order_id  = %s
        """ % (self.id)

        self.env.cr.execute(query)
        arrQuery = self.env.cr.dictfetchall()

        if arrQuery:
            query = """
                update mc_kontrak_mc_kontrak set mc_isopen = true where id = %s
            """ % self.kontrak_id.id
            self.env.cr.execute(query)
            for row in arrQuery:
                query = """
                    update mc_kontrak_product_order_line set
                    mc_qty_terpasang = mc_qty_terpasang - %s,
                    mc_qty_belum_terpasang = mc_qty_belum_terpasang + %s
                    where id = %s 
                """ % (row['x_mc_qty_terpasang'], row['x_mc_qty_terpasang'], row['kontrak_line_id'])
                self.env.cr.execute(query)

        query = """
                UPDATE sale_order SET state = 'cancel' WHERE id = %s 
        """ % self.id
        self.env.cr.execute(query)

        res = super(CustomSalesOrder, self).action_cancel()
        return res


class CustomSalesOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _name = 'sale.order.line'

    product_id = fields.Many2one('product.product', readonly=True)
    order_id = fields.Many2one('sale.order', required=True, Store=True, Index=True)
    kontrak_id = fields.Many2one('mc_kontrak.mc_kontrak')
    kontrak_line_id = fields.Many2one('mc_kontrak.product_order_line')

    # Field
    x_mc_qty_kontrak = fields.Integer(string='Quantity Kontrak')
    x_mc_qty_terpasang = fields.Integer(string='Quantity Terpasang')
    x_mc_harga_produk = fields.Monetary(string='Standard Price')
    x_mc_harga_diskon = fields.Monetary()
    x_mc_isopen = fields.Boolean()
    price_subtotal = fields.Monetary(compute='_hitung_subtotal_so')

    # Total Harga
    @api.depends('x_mc_harga_produk', 'x_mc_harga_diskon', 'x_mc_qty_terpasang')
    def _hitung_subtotal_so(self):
        subtotal = 0

        for line in self:
            price = (line.x_mc_harga_produk - line.x_mc_harga_diskon) * line.x_mc_qty_terpasang
            subtotal += price
            line.update({
                'price_subtotal': price
            })