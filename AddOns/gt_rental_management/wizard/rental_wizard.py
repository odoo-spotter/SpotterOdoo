# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

                    
class RentalOrderLine(models.Model):
    _name = 'rental.order.line'
     
    product_id = fields.Many2one('product.product', string='Product')
    serial_no = fields.Char('Serial Number')
    order_rental_id = fields.Many2one('rental.wizard', string='Rental Wizard')
    quantity = fields.Float('Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    move_id = fields.Many2one('stock.move', "Move")
    
    
class RentalWizard(models.Model):
    _name = "rental.wizard"
    
    rental_wizard_line = fields.One2many('sale.order.line', 'rental_wizard_id', string='Existing Products')
    product_return_moves = fields.One2many('rental.order.line', 'order_rental_id', string='Replace Products')
    picking_id = fields.Many2one('stock.picking')
    move_dest_exists = fields.Boolean('Chained Move Exists', readonly=True)
    original_location_id = fields.Many2one('stock.location')
    parent_location_id = fields.Many2one('stock.location')
    location_id = fields.Many2one(
        'stock.location', 'Return Location',
        domain="['|', ('id', '=', original_location_id), '&', ('return_location', '=', True), ('id', 'child_of', parent_location_id)]")
 
 
    @api.model
    def default_get(self, fields):
        res = super(RentalWizard, self).default_get(fields)

        move_dest_exists = False
        product_return_moves = []
        rent_obj = self.env['stock.picking'].search([('sale_id','=',self.env.context.get('active_id')),
                                                    ('state','=','done'),
                                                    ])
        sale_order = self.env['sale.order'].search([('id','=',self.env.context.get('active_id'))])
        
        picking = rent_obj
        if picking:
            res.update({'picking_id': picking.id})
            if picking.state != 'done':
                raise UserError(_("You may only return Done pickings"))
            for move in picking.move_lines:
                if move.scrapped:
                    continue
                if move.move_dest_ids:
                    move_dest_exists = True
                for rent_line in sale_order.order_line:
                    if rent_line.product_id == move.product_id:
                        quantity = rent_line.product_uom_qty
                product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity, 'move_id': move.id, 'uom_id': move.product_id.uom_id.id}))

            if not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)!"))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': product_return_moves})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': move_dest_exists})
            if 'parent_location_id' in fields and picking.location_id.usage == 'internal':
                res.update({'parent_location_id': picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.view_location_id.id or picking.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': picking.location_id.id})
            if 'location_id' in fields:
                location_id = picking.location_id.id
                if picking.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                    location_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id
                res['location_id'] = location_id
        return res

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals

    def _create_returns(self):
        self.ensure_one()
        sale_order = self.env['sale.order'].search([('id','=',self._context.get('active_id'))])
        picking_exist = self.env['stock.picking'].search([('sale_id','=',sale_order.id)])
        for picking in picking_exist:
            loc = picking.location_id
            dest = picking.location_dest_id
            pic_type = picking.picking_type_id
            group_id = picking.group_id
        
        partner_obj = self.env['res.partner']
        picking_obj = self.env['stock.picking']
        picking_line_obj = self.env['stock.move']
        ids = []

        stock = picking_obj.create({
            'partner_id': sale_order.partner_id.id,
            'location_id': loc.id,
            'location_dest_id': dest.id,
            'picking_type_id': pic_type.id,
            'move_type': 'direct',
            'origin': sale_order.name,
            'scheduled_date': datetime.now(),
            'group_id': group_id.id,
            
        })
        for order_line in sale_order.order_line:
            stock_lines = {
                'picking_id': stock.id,
                'product_id': order_line.product_id.id,
                'product_uom_qty': order_line.product_uom_qty,
                'name': order_line.product_id.name,
                'product_uom': order_line.product_uom.id,
                'location_id': loc.id,
                'location_dest_id': dest.id,
                }
            stock_line_rec = picking_line_obj.create(stock_lines)
            ids.append(stock_line_rec.id)
            
        serial_list = []
        for l in self.product_return_moves:
            serial_list.append(l.serial_no)
        j = 0
        for id in ids:
            order_line = picking_line_obj.browse(id)
            order_line.serial_no = serial_list[j]
            j = j+1
            
        stock.move_ids_without_package = ids
        stock.sale_id = sale_order.id
        stock.action_confirm()
        stock.action_assign()

        
        # TODO sle: the unreserve of the next moves could be less brutal
        for return_move in self.product_return_moves.mapped('move_id'):
            return_move.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._do_unreserve()

        # create new picking for returned products
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id or self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'origin': _("Return of %s") % self.picking_id.name,
            'location_id': self.picking_id.location_dest_id.id,
            'location_dest_id': picking_exist.location_id.id})
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        returned_lines = 0
        for return_line in self.product_return_moves:
            if not return_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed."))
            # TODO sle: float_is_zero?
            if return_line.quantity:
                returned_lines += 1
                vals = self._prepare_move_default_values(return_line, new_picking)
                r = return_line.move_id.copy(vals)
                vals = {}
                move_orig_to_link = return_line.move_id.move_dest_ids.mapped('returned_move_ids')
                move_dest_to_link = return_line.move_id.move_orig_ids.mapped('returned_move_ids')
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | return_line.move_id]
                vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)
        if not returned_lines:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id
    
    
    #@api.multi
    def replace_product(self):
        
        if self.rental_wizard_line.replace:
            if self.product_return_moves.product_id.id == False:
                raise UserError(_("Select atleast one product to Replace!"))
            
            
            if self.rental_wizard_line.product_id.id != self.product_return_moves.product_id.id:
                raise UserError(_("You have to select Same Product!"))
            
            if self.rental_wizard_line.serial_no == self.product_return_moves.serial_no:
              raise UserError(_("Serial number must be different!"))
             
            for wizard in self:
                new_picking_id, pick_type_id = wizard._create_returns()
            # Override the context to disable all the potential filters that could have been set previously
            ctx = dict(self.env.context)
            ctx.update({
                'search_default_picking_type_id': pick_type_id,
                'search_default_draft': False,
                'search_default_assigned': False,
                'search_default_confirmed': False,
                'search_default_ready': False,
                'search_default_late': False,
                'search_default_available': False,
            })
            self._cr.execute("delete from rental_wizard")
            self._cr.execute("delete from rental_order_line")
            return {
                'name': _('Returned Picking'),
                'view_type': 'form',
                'view_mode': 'form,tree,calendar',
                'res_model': 'stock.picking',
                'res_id': new_picking_id,
                'type': 'ir.actions.act_window',
                'context': ctx,
            }
#     
class RenewRental(models.TransientModel):
    _name = "renew.rental"
      
    new_entend_date = fields.Date('New Extended Date')
    
    #@api.multi
    def renew_rental(self):
        sale_obj = self.env['sale.order'].search([])
        for sale in sale_obj:
            line_dic = {'end_date' : self.new_entend_date}
            res = sale_obj.write(line_dic)



