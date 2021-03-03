# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class BohmCustomStockMove(models.Model):
    _name = 'stock.move'
    _inherit = 'stock.move'

    def picking_create_move(self, picking_id,  product_id, qty, location_id, location_dest_id, lot_id=None):
        move_vals = {
            'name': product_id.name,
            'product_id': product_id.id,
            'product_uom_qty': 1,
            'product_uom': product_id.uom_id.id,
            'picking_id': picking_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id
        }

        move = self.create(move_vals)
        move._action_confirm()
        move._action_assign()

        if lot_id:
            move.write({
                'move_line_ids': [(0, 0, {
                    'product_id': product_id.id,
                    'product_uom_qty': qty,
                    'product_uom_id': product_id.uom_id.id,
                    'lot_id': lot_id.id,
                    'picking_id': picking_id.id,
                    'location_id': location_id.id,
                    'qty_done': qty,
                    'location_dest_id': location_dest_id.id,
                    'package_id': False,
                    'result_package_id': False,
                })]})
            try:
                for move_line in move.move_line_ids:
                    if move_line.qty_done == 0:
                        move_line.sudo().unlink()
            except:
                pass
