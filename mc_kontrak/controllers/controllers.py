# -*- coding: utf-8 -*-
# from odoo import http


# class McKontrak(http.Controller):
#     @http.route('/mc_kontrak/mc_kontrak', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mc_kontrak/mc_kontrak/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mc_kontrak.listing', {
#             'root': '/mc_kontrak/mc_kontrak',
#             'objects': http.request.env['mc_kontrak.mc_kontrak'].search([]),
#         })

#     @http.route('/mc_kontrak/mc_kontrak/objects/<model("mc_kontrak.mc_kontrak"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mc_kontrak.object', {
#             'object': obj
#         })
