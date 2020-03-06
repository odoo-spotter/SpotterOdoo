# -*- coding: utf-8 -*-


import base64
from datetime import datetime

from odoo import api, fields, models, tools, _
import xlsxwriter
from xlsxwriter.utility import xl_cell_to_rowcol
from odoo.tools import float_round
from PIL import Image


def ListCalculation(lists):
    result = {}
    for card,value in lists:
        if card not in result:
            result[card] = [value]
        else :
            result.update({card : result[card] + [value]})
    return list(result.items())


class ProductPriceList(models.TransientModel):
    _inherit = 'product.price_list'  

    qty4 = fields.Integer('Quantity-4', default=15)
    qty5 = fields.Integer('Quantity-5', default=20)
    template_type = fields.Selection([('template_1','Product Pricelist'),
                                      ('template_2','Product Pricelist With Extra Features'),
                                      ('template_3','Product Pricelist And Company Logo With Extra Features')], 'Template')
    configuration_id = fields.Many2one('pricelist.config', 'PriceList Configuration')

    @api.onchange('template_type', 'price_list')
    def template_type_onchange(self):
        pricelist_configuration_ids = self.env['pricelist.config'].search([])
        configuration_list = []
        if pricelist_configuration_ids:
            for j in pricelist_configuration_ids:
                if j.template_type == self.template_type and j.pricelist_id == self.price_list:
                    configuration_list.append(j.id)
            return {'domain': {'configuration_id': [('id', 'in', configuration_list)]}}

    def _get_excel_report_values(self, data):
        data = data if data is not None else {}
        pricelist = self.env['product.pricelist'].browse(data['price_list'])
        products = self.env['product.product'].browse(data['data'])
        quantities = self._get_quantity(data)
        return {
            'doc_ids': data.get('ids', data.get('active_ids')),
            'doc_model': 'product.pricelist',
            'docs': products,
            'data': dict(data,
                         pricelist=pricelist,
                         quantities=quantities,
                         categories_data=self._get_categories(pricelist, products, quantities)
                        ),
        }

    def _get_quantity(self, data):
        return sorted([data[key] for key in data if key.startswith('qty') and data[key]])

    def _get_categories(self, pricelist, products, quantities):
        categ_data = []
        categories = self.env['product.category']
        for product in products:
            categories |= product.categ_id
        for category in categories:
            categ_products = products.filtered(lambda product: product.categ_id == category)
            prices = {}
            for categ_product in categ_products:
                prices[categ_product.id] = dict.fromkeys(quantities, 0.0)
                for quantity in quantities:
                    prices[categ_product.id][quantity] = self._get_price(pricelist, categ_product, quantity)
            categ_data.append({
            'category': category,
            'products': categ_products,
            'prices': prices,
            })
        return categ_data

    def _get_price(self, pricelist, product, qty):
        sale_price_digits = self.env['decimal.precision'].precision_get('Product Price')
        price = pricelist.get_product_price(product, qty, False)
        if not price:
            price = product.list_price
        return float_round(price, precision_digits=sale_price_digits)

    def _get_pricelist(self):
        datas = {'ids': self.env.context.get('active_ids', [])}
        res = self.read(['price_list', 'qty1', 'qty2', 'qty3', 'qty4', 'qty5', 'template_type'])
        res = res and res[0] or {}
        res['price_list'] = res['price_list'][0]
        pricelist_config_id = self.configuration_id
        res['pricelist_config'] = pricelist_config_id
        res['data'] = datas.get('ids')
        datas['form'] = res
        return res

    def print_excel(self):
        pricelist_report_data = self._get_pricelist()
        product_data = self._get_excel_report_values(pricelist_report_data)

        filename = pricelist_report_data.get('pricelist_config').file_name
        if filename:
            filename += '.xlsx'
        else:
            filename = 'Product Pricelist.xlsx'

        product_categ_list = []
        for pro in pricelist_report_data.get('data'):
            product_product_obj = self.env['product.product'].browse(pro)
            product_categ_list.append(product_product_obj.categ_id.name)
        new_list = []
        for pro in pricelist_report_data.get('data'):
            product_id = self.env['product.product'].browse(pro)
            new_list.append([product_id.categ_id.name,product_id.id])
        my_list = ListCalculation(new_list)
        workbook = xlsxwriter.Workbook('/tmp/' + filename)

        header_format = workbook.add_format({'bold': True,'border': 1,'align': 'center','valign':'vcenter','font_size':16,'bg_color':'#b2babb'})
        data_header_format = workbook.add_format({'bold': True,'border': 1,'align': 'center','valign':'vcenter','font_size':12})
        data_header1_format = workbook.add_format({'bold': True,'align': 'center','valign':'vcenter','font_size':12})
        data_header2_format = workbook.add_format({'bold': True,'align': 'right','valign':'vcenter','font_size':12})
        data_value_left_format = workbook.add_format({'border': 1,'align': 'left','valign':'vcenter','font_size':12})
        data_value_center_format = workbook.add_format({'border': 1,'align': 'center','valign':'vcenter','font_size':12})
        data_categ_format = workbook.add_format({'bold': True,'border': 1,'align': 'left','valign':'vcenter','font_size':13,'font_color': 'white','bg_color' : '#43bdcb'})
        #merge_format = workbook.add_format({'bold': 1,'border': 1,'align': 'center','valign': 'vcenter','fg_color': 'yellow'})
        worksheet = workbook.add_worksheet(pricelist_report_data.get('pricelist_config').sheet_name)

        template_type = pricelist_report_data.get('template_type')

        header_cell = pricelist_report_data.get('pricelist_config').header_location
        company_cell = pricelist_report_data.get('pricelist_config').company_cell_location
        company_logo_cell = pricelist_report_data.get('pricelist_config').company_logo_cell_location
        currency_cell = pricelist_report_data.get('pricelist_config').currency_cell_location
        date_cell = pricelist_report_data.get('pricelist_config').date_cell_location

        pro_code_cell = pricelist_report_data.get('pricelist_config').product_code_cell_location
        pro_name_cell = pricelist_report_data.get('pricelist_config').product_name_location
        pro_att_cell = pricelist_report_data.get('pricelist_config').product_attributes_cell_location
        product_tax_cell = pricelist_report_data.get('pricelist_config').product_taxes_cell_location
        product_uom_cell = pricelist_report_data.get('pricelist_config').product_uom_cell_location

        # Template 2 Extra Value
        qty_case_cell_location     = pricelist_report_data.get('pricelist_config').product_qty_case_cell_location
        on_hand_cell_location      = pricelist_report_data.get('pricelist_config').product_on_hand_cell_location
        ean_cell_location          = pricelist_report_data.get('pricelist_config').product_ean_cell_location
        weight_cell_location       = pricelist_report_data.get('pricelist_config').product_weight_cell_location
        volume_cell_location       = pricelist_report_data.get('pricelist_config').product_volume_cell_location
        lead_time_cell_location    = pricelist_report_data.get('pricelist_config').product_lead_time_cell_location
        description_cell_location  = pricelist_report_data.get('pricelist_config').product_description_cell_location

        # Template 3 Extra Value
        retail_price_cell_location    = pricelist_report_data.get('pricelist_config').product_retail_price_cell_location
        wholesale_price_cell_location = pricelist_report_data.get('pricelist_config').product_wholesale_price_cell_location


        qty1_cell = pricelist_report_data.get('pricelist_config').qty1_cell_location
        qty2_cell = pricelist_report_data.get('pricelist_config').qty2_cell_location
        qty3_cell = pricelist_report_data.get('pricelist_config').qty3_cell_location
        qty4_cell = pricelist_report_data.get('pricelist_config').qty4_cell_location
        qty5_cell = pricelist_report_data.get('pricelist_config').qty5_cell_location

        # Qty Column Count
        qty1_cell_count = qty1_cell
        qty2_cell_count = qty2_cell
        qty3_cell_count = qty3_cell
        qty4_cell_count = qty4_cell
        qty5_cell_count = qty5_cell

        worksheet.merge_range(header_cell, "Product PriceList",header_format)

        if template_type == 'template_1':

            if pricelist_report_data.get('pricelist_config').is_company:
                worksheet.merge_range(company_cell,self.env.user.company_id.name,data_header1_format)

            if pricelist_report_data.get('pricelist_config').is_currency:
                currency = pricelist_report_data.get('pricelist_config').pricelist_id.currency_id.name
                worksheet.write(currency_cell, currency, data_header2_format)

            if pricelist_report_data.get('pricelist_config').is_date:
                worksheet.write(date_cell, str(datetime.now().date()), data_header2_format)

            if pricelist_report_data.get('pricelist_config').is_product_code:
                worksheet.write(pro_code_cell,"Internal Reference",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_name:
                worksheet.write(pro_name_cell,"Name",data_header_format) 

            if pricelist_report_data.get('pricelist_config').is_product_attributes:
                worksheet.write(pro_att_cell,"Attributes",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_taxes:
                worksheet.write(product_tax_cell,"Taxes",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_uom:
                worksheet.write(product_uom_cell,"UOM",data_header_format)

            qty1 = pricelist_report_data.get('qty1')
            qty2 = pricelist_report_data.get('qty2')
            qty3 = pricelist_report_data.get('qty3')
            qty4 = pricelist_report_data.get('qty4')
            qty5 = pricelist_report_data.get('qty5')

            worksheet.set_column(0,0, 20)
            worksheet.set_column(1,1, 25)
            worksheet.set_column(2,2, 50)
            worksheet.set_column(3,4, 25)
            worksheet.set_column(5,9, 15)

            product_code        = pricelist_report_data.get('pricelist_config').is_product_code
            product_name        = pricelist_report_data.get('pricelist_config').is_product_name
            product_attributes  = pricelist_report_data.get('pricelist_config').is_product_attributes
            product_taxes       = pricelist_report_data.get('pricelist_config').is_product_taxes
            product_uom         = pricelist_report_data.get('pricelist_config').is_product_uom

            qty_count = pricelist_report_data.get('pricelist_config').qty_count

            if qty1 and qty1_cell and qty_count == 'one':
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

            elif qty2 and qty2_cell and qty_count == 'two':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

            elif qty3 and qty3_cell and qty_count == 'three':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                # Third Quantity
                qty3_data = str(qty3) + ' Units'
                worksheet.write(qty3_cell,qty3_data,data_header_format)
                qty3_cell = qty3_cell.split(":")[0]
                (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

            elif qty4 and qty4_cell and qty_count == 'four':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                # Third Quantity
                qty3_data = str(qty3) + ' Units'
                worksheet.write(qty3_cell,qty3_data,data_header_format)
                qty3_cell = qty3_cell.split(":")[0]
                (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

                # Four Quantity
                qty4_data = str(qty4) + ' Units'
                worksheet.write(qty4_cell,qty4_data,data_header_format)
                qty4_cell = qty4_cell.split(":")[0]
                (qty4_row,qty4_col) = xl_cell_to_rowcol(qty4_cell)
            else:
                if qty5 and qty5_cell and qty_count == 'five':
                    # First Quantity
                    qty1_data = str(qty1) + ' Units'
                    worksheet.write(qty1_cell,qty1_data,data_header_format)
                    qty1_cell = qty1_cell.split(":")[0]
                    (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                    # Second Quantity
                    qty2_data = str(qty2) + ' Units'
                    worksheet.write(qty2_cell,qty2_data,data_header_format)
                    qty2_cell = qty2_cell.split(":")[0]
                    (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                    # Third Quantity
                    qty3_data = str(qty3) + ' Units'
                    worksheet.write(qty3_cell,qty3_data,data_header_format)
                    qty3_cell = qty3_cell.split(":")[0]
                    (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

                    # Four Quantity
                    qty4_data = str(qty4) + ' Units'
                    worksheet.write(qty4_cell,qty4_data,data_header_format)
                    qty4_cell = qty4_cell.split(":")[0]
                    (qty4_row,qty4_col) = xl_cell_to_rowcol(qty4_cell)

                    # Five Quantity
                    qty5_data = str(qty5) + ' Units'
                    worksheet.write(qty5_cell,qty5_data,data_header_format)
                    qty5_cell = qty5_cell.split(":")[0]
                    (qty5_row,qty5_col) = xl_cell_to_rowcol(qty5_cell)

            if product_code:
                a = pro_code_cell.split(":")[0]
                b = pro_code_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_name:
                a = pro_code_cell.split(":")[0]
                b = pro_name_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_attributes:
                a = pro_code_cell.split(":")[0]
                b = pro_att_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_taxes:
                a = pro_code_cell.split(":")[0]
                b = product_tax_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_uom:
                a = pro_code_cell.split(":")[0]
                b = product_uom_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if not product_name and not product_attributes and not product_taxes and \
                        not product_uom and not product_code:
                (row, col) = (1 , 1)
                (row1, col1) = (1 , 1)

            if qty1 and qty1_cell_count and qty_count == 'one':
                a = pro_code_cell.split(":")[0]
                b = qty1_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty2 and qty2_cell_count and qty_count == 'two':
                a = pro_code_cell.split(":")[0]
                b = qty2_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty3 and qty3_cell_count and qty_count == 'three':
                a = pro_code_cell.split(":")[0]
                b = qty3_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty4 and qty4_cell_count and qty_count == 'four':
                a = pro_code_cell.split(":")[0]
                b = qty4_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            else:
                if qty5 and qty5_cell_count and qty_count == 'five':
                    a = pro_code_cell.split(":")[0]
                    b = qty5_cell_count.split(":")[1]
                    (row, col) = xl_cell_to_rowcol(a)
                    (row1, col1) = xl_cell_to_rowcol(b)

            worksheet.set_row(row, 40)

            data_row = row + 1
            data_row1 = row1 + 1
            categ_row = data_row

            for categ_line in my_list:
                if product_code and not product_name and not product_attributes and not product_taxes and not product_uom:
                    worksheet.write(data_row, col, categ_line[0], data_categ_format)
                else:
                    worksheet.merge_range(data_row,col,data_row1,col1,categ_line[0],data_categ_format)
                data_row += 1
                data_row1 += 1
                categ_row += 1

                if qty1 and qty1_cell and qty_count == 'one':
                    # First Quantity
                    qty1_row += 1
                elif qty2 and qty2_cell_count and qty_count == 'two':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                elif qty3 and qty3_cell_count and qty_count == 'three':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                    # Third Quantity
                    qty3_row +=  1
                elif qty4 and qty4_cell_count and qty_count == 'four':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                    # Third Quantity
                    qty3_row +=  1
                    # Four Quantity
                    qty4_row +=  1
                else:
                    if qty5 and qty5_cell_count and qty_count == 'five':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row +=  1
                        # Third Quantity
                        qty3_row +=  1
                        # Four Quantity
                        qty4_row +=  1
                        # Five Quantity
                        qty5_row +=  1

                for product in categ_line[1]:
                    categ_row += 1
                    row2 = data_row
                    if qty1 and qty1_cell and qty_count == 'one':
                        # First Quantity
                        qty_1 = qty1_row
                    elif qty2 and qty2_cell_count and qty_count == 'two':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                    elif qty3 and qty3_cell_count and qty_count == 'three':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                        # Third Quantity
                        qty_3 = qty3_row
                    elif qty4 and qty4_cell_count and qty_count == 'four':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                        # Third Quantity
                        qty_3 = qty3_row
                        # Four Quantity
                        qty_4 = qty4_row
                    else:
                        if qty5 and qty5_cell_count and qty_count == 'five':
                            # First Quantity
                            qty_1 = qty1_row
                            # Second Quantity
                            qty_2 = qty2_row
                            # Third Quantity
                            qty_3 = qty3_row
                            # Four Quantity
                            qty_4 = qty4_row
                            # Five Quantity
                            qty_5 = qty5_row

                    product_id = self.env['product.product'].browse(product) 
                    name_att = ' '
                    for val in product_id.product_template_attribute_value_ids:
                        name_att += val.attribute_id.name + ':' + val.name + ', '
                    customer_tax = ' '
                    for tax in product_id.taxes_id:
                        customer_tax += tax.name + ', '
                    if product_code:
                        worksheet.write(row2,col, str(product_id.default_code or ''), data_value_left_format)
                    if product_name:
                        worksheet.write(row2,col + 1, str(product_id.name or ''), data_value_left_format)
                    if product_attributes:
                        worksheet.write(row2,col + 2, str(name_att or ''), data_value_left_format)
                    if product_taxes:
                        worksheet.write(row2,col + 3, str(customer_tax or ''), data_value_left_format)
                    if product_uom:
                        worksheet.write(row2,col + 4, str(product_id.uom_id.name or ''), data_value_center_format)
                    for category in product_data['data'].get('categories_data'):
                        if 'prices' in category:
                            for prices,value in category['prices'].items():
                                if product_id.id == prices:
                                    for quantity,price in value.items():
                                        if qty1 and qty1_cell and qty_count == 'one':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty2 and qty2_cell_count and qty_count == 'two':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty3 and qty3_cell_count and qty_count == 'three':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty3 == quantity:
                                                worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty4 and qty4_cell_count and qty_count == 'four':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty3 == quantity:
                                                worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty4 == quantity:
                                                worksheet.write(qty_4 + 1,qty4_col, str('%.2f' % price or ''), data_value_center_format)
                                        else:
                                            if qty5 and qty5_cell_count and qty_count == 'five':
                                                if qty1 == quantity:
                                                    worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty2 == quantity:
                                                    worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty3 == quantity:
                                                    worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty4 == quantity:
                                                    worksheet.write(qty_4 + 1,qty4_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty5 == quantity:
                                                    worksheet.write(qty_5 + 1,qty5_col, str('%.2f' % price or ''), data_value_center_format)
                    row2 += 1
                    if qty1 and qty1_cell and qty_count == 'one':
                        # First Quantity
                        qty1_row += 1
                    elif qty2 and qty2_cell_count and qty_count == 'two':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                    elif qty3 and qty3_cell_count and qty_count == 'three':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                        # Third Quantity
                        qty3_row += 1
                    elif qty4 and qty4_cell_count and qty_count == 'four':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                        # Third Quantity
                        qty3_row += 1
                        # Four Quantity
                        qty4_row += 1
                    else:
                        if qty5 and qty5_cell_count and qty_count == 'five':
                            # First Quantity
                            qty1_row += 1
                            # Second Quantity
                            qty2_row += 1
                            # Third Quantity
                            qty3_row += 1
                            # Four Quantity
                            qty4_row += 1
                            # Five Quantity
                            qty5_row += 1

                    data_row = row2
                    data_row1 = row2

        elif template_type == 'template_2':

            if pricelist_report_data.get('pricelist_config').is_company:
                worksheet.merge_range(company_cell,self.env.user.company_id.name,data_header1_format)

            if pricelist_report_data.get('pricelist_config').is_currency:
                currency = pricelist_report_data.get('pricelist_config').pricelist_id.currency_id.name
                worksheet.write(currency_cell, currency, data_header2_format)

            if pricelist_report_data.get('pricelist_config').is_date:
                worksheet.write(date_cell, str(datetime.now().date()), data_header2_format)

            if pricelist_report_data.get('pricelist_config').is_product_code:
                worksheet.write(pro_code_cell,"Internal Reference",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_name:
                worksheet.write(pro_name_cell,"Name",data_header_format) 

            if pricelist_report_data.get('pricelist_config').is_product_attributes:
                worksheet.write(pro_att_cell,"Attributes",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_taxes:
                worksheet.write(product_tax_cell,"Taxes",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_uom:
                worksheet.write(product_uom_cell,"UOM",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_uom:
                worksheet.write(product_uom_cell,"UOM",data_header_format)

            # Template 2 Extra Value
            if pricelist_report_data.get('pricelist_config').is_product_qty_case:
                worksheet.write(qty_case_cell_location,"QTY/Case",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_on_hand:
                worksheet.write(on_hand_cell_location,"On Hand",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_ean:
                worksheet.write(ean_cell_location,"EAN",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_weight:
                worksheet.write(weight_cell_location,"Weight (kg)",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_volume:
                worksheet.write(volume_cell_location,"Volume (m3)",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_description:
                worksheet.write(description_cell_location,"Description",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_lead_time:
                worksheet.write(lead_time_cell_location,"Lead Time",data_header_format)

            qty1 = pricelist_report_data.get('qty1')
            qty2 = pricelist_report_data.get('qty2')
            qty3 = pricelist_report_data.get('qty3')
            qty4 = pricelist_report_data.get('qty4')
            qty5 = pricelist_report_data.get('qty5')

            worksheet.set_column(0,0, 20)
            worksheet.set_column(1,1, 25)
            worksheet.set_column(2,2, 50)
            worksheet.set_column(3,4, 25)
            worksheet.set_column(5,9, 15)
            worksheet.set_column(10,11, 15)
            worksheet.set_column(12,12, 25)
            worksheet.set_column(13,14, 15)
            worksheet.set_column(15,15, 50)
            worksheet.set_column(16,16, 15)

            product_code        = pricelist_report_data.get('pricelist_config').is_product_code
            product_name        = pricelist_report_data.get('pricelist_config').is_product_name
            product_attributes  = pricelist_report_data.get('pricelist_config').is_product_attributes
            product_taxes       = pricelist_report_data.get('pricelist_config').is_product_taxes
            product_uom         = pricelist_report_data.get('pricelist_config').is_product_uom

            # Template 2 Extra Value
            product_qty_case    = pricelist_report_data.get('pricelist_config').is_product_qty_case
            product_on_hand     = pricelist_report_data.get('pricelist_config').is_product_on_hand
            product_ean         = pricelist_report_data.get('pricelist_config').is_product_ean
            product_weight      = pricelist_report_data.get('pricelist_config').is_product_weight
            product_volume      = pricelist_report_data.get('pricelist_config').is_product_volume
            product_description = pricelist_report_data.get('pricelist_config').is_product_description
            product_lead_time   = pricelist_report_data.get('pricelist_config').is_product_lead_time

            qty_count = pricelist_report_data.get('pricelist_config').qty_count

            if qty1 and qty1_cell and qty_count == 'one':
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

            elif qty2 and qty2_cell and qty_count == 'two':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

            elif qty3 and qty3_cell and qty_count == 'three':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                # Third Quantity
                qty3_data = str(qty3) + ' Units'
                worksheet.write(qty3_cell,qty3_data,data_header_format)
                qty3_cell = qty3_cell.split(":")[0]
                (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

            elif qty4 and qty4_cell and qty_count == 'four':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                # Third Quantity
                qty3_data = str(qty3) + ' Units'
                worksheet.write(qty3_cell,qty3_data,data_header_format)
                qty3_cell = qty3_cell.split(":")[0]
                (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

                # Four Quantity
                qty4_data = str(qty4) + ' Units'
                worksheet.write(qty4_cell,qty4_data,data_header_format)
                qty4_cell = qty4_cell.split(":")[0]
                (qty4_row,qty4_col) = xl_cell_to_rowcol(qty4_cell)
            else:
                if qty5 and qty5_cell and qty_count == 'five':
                    # First Quantity
                    qty1_data = str(qty1) + ' Units'
                    worksheet.write(qty1_cell,qty1_data,data_header_format)
                    qty1_cell = qty1_cell.split(":")[0]
                    (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                    # Second Quantity
                    qty2_data = str(qty2) + ' Units'
                    worksheet.write(qty2_cell,qty2_data,data_header_format)
                    qty2_cell = qty2_cell.split(":")[0]
                    (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                    # Third Quantity
                    qty3_data = str(qty3) + ' Units'
                    worksheet.write(qty3_cell,qty3_data,data_header_format)
                    qty3_cell = qty3_cell.split(":")[0]
                    (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

                    # Four Quantity
                    qty4_data = str(qty4) + ' Units'
                    worksheet.write(qty4_cell,qty4_data,data_header_format)
                    qty4_cell = qty4_cell.split(":")[0]
                    (qty4_row,qty4_col) = xl_cell_to_rowcol(qty4_cell)

                    # Five Quantity
                    qty5_data = str(qty5) + ' Units'
                    worksheet.write(qty5_cell,qty5_data,data_header_format)
                    qty5_cell = qty5_cell.split(":")[0]
                    (qty5_row,qty5_col) = xl_cell_to_rowcol(qty5_cell)

            if product_code:
                a = pro_code_cell.split(":")[0]
                b = pro_code_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_name:
                a = pro_code_cell.split(":")[0]
                b = pro_name_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_attributes:
                a = pro_code_cell.split(":")[0]
                b = pro_att_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_taxes:
                a = pro_code_cell.split(":")[0]
                b = product_tax_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_uom:
                a = pro_code_cell.split(":")[0]
                b = product_uom_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)

            if not product_name and not product_attributes and not product_taxes and \
                        not product_uom and not product_code and not product_qty_case and \
                        not product_on_hand and not product_ean and \
                        not product_weight and not product_volume and not product_description and \
                        not product_lead_time:
                (row, col) = (1 , 1)
                (row1, col1) = (1 , 1)

            if qty1 and qty1_cell_count and qty_count == 'one':
                a = pro_code_cell.split(":")[0]
                b = qty1_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty2 and qty2_cell_count and qty_count == 'two':
                a = pro_code_cell.split(":")[0]
                b = qty2_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty3 and qty3_cell_count and qty_count == 'three':
                a = pro_code_cell.split(":")[0]
                b = qty3_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty4 and qty4_cell_count and qty_count == 'four':
                a = pro_code_cell.split(":")[0]
                b = qty4_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            else:
                if qty5 and qty5_cell_count and qty_count == 'five':
                    a = pro_code_cell.split(":")[0]
                    b = qty5_cell_count.split(":")[1]
                    (row, col) = xl_cell_to_rowcol(a)
                    (row1, col1) = xl_cell_to_rowcol(b)

            if product_qty_case:
                a = pro_code_cell.split(":")[0]
                b = qty_case_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_on_hand:
                a = pro_code_cell.split(":")[0]
                b = on_hand_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_ean:
                a = pro_code_cell.split(":")[0]
                b = ean_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_weight:
                a = pro_code_cell.split(":")[0]
                b = weight_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_volume:
                a = pro_code_cell.split(":")[0]
                b = volume_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_description:
                a = pro_code_cell.split(":")[0]
                b = description_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_lead_time:
                a = pro_code_cell.split(":")[0]
                b = lead_time_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)

            worksheet.set_row(row, 40)

            data_row = row + 1
            data_row1 = row1 + 1
            categ_row = data_row

            for categ_line in my_list:
                if product_code and not product_name and not product_attributes and not product_taxes and \
                        not product_uom and not product_qty_case and not product_on_hand and \
                        not product_ean and not product_weight and not product_volume and not product_description and \
                        not product_lead_time:
                    worksheet.write(data_row, col, categ_line[0], data_categ_format)
                else:
                    worksheet.merge_range(data_row,col,data_row1,col1,categ_line[0],data_categ_format)
                data_row += 1
                data_row1 += 1
                categ_row += 1

                if qty1 and qty1_cell and qty_count == 'one':
                    # First Quantity
                    qty1_row += 1
                elif qty2 and qty2_cell_count and qty_count == 'two':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                elif qty3 and qty3_cell_count and qty_count == 'three':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                    # Third Quantity
                    qty3_row +=  1
                elif qty4 and qty4_cell_count and qty_count == 'four':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                    # Third Quantity
                    qty3_row +=  1
                    # Four Quantity
                    qty4_row +=  1
                else:
                    if qty5 and qty5_cell_count and qty_count == 'five':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row +=  1
                        # Third Quantity
                        qty3_row +=  1
                        # Four Quantity
                        qty4_row +=  1
                        # Five Quantity
                        qty5_row +=  1

                for product in categ_line[1]:
                    row2 = data_row
                    if qty1 and qty1_cell and qty_count == 'one':
                        # First Quantity
                        qty_1 = qty1_row
                    elif qty2 and qty2_cell_count and qty_count == 'two':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                    elif qty3 and qty3_cell_count and qty_count == 'three':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                        # Third Quantity
                        qty_3 = qty3_row
                    elif qty4 and qty4_cell_count and qty_count == 'four':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                        # Third Quantity
                        qty_3 = qty3_row
                        # Four Quantity
                        qty_4 = qty4_row
                    else:
                        if qty5 and qty5_cell_count and qty_count == 'five':
                            # First Quantity
                            qty_1 = qty1_row
                            # Second Quantity
                            qty_2 = qty2_row
                            # Third Quantity
                            qty_3 = qty3_row
                            # Four Quantity
                            qty_4 = qty4_row
                            # Five Quantity
                            qty_5 = qty5_row

                    product_id = self.env['product.product'].browse(product)
                    name_att = ' '
                    for val in product_id.product_template_attribute_value_ids:
                        name_att += val.attribute_id.name + ':' + val.name + ', '
                    customer_tax = ' '
                    for tax in product_id.taxes_id:
                        customer_tax += tax.name + ', '
                    if product_code:
                        worksheet.write(row2,col, str(product_id.default_code or ''), data_value_left_format)
                    if product_name:
                        worksheet.write(row2,col + 1, str(product_id.name or ''), data_value_left_format)
                    if product_attributes:
                        worksheet.write(row2,col + 2, str(name_att or ''), data_value_left_format)
                    if product_taxes:
                        worksheet.write(row2,col + 3, str(customer_tax or ''), data_value_left_format)
                    if product_uom:
                        worksheet.write(row2,col + 4, str(product_id.uom_id.name or ''), data_value_center_format)
                    if product_qty_case:
                        worksheet.write(row2,col + 10, '', data_value_center_format)
                    if product_on_hand:
                        worksheet.write(row2,col + 11, product_id.qty_available, data_value_center_format)
                    if product_ean:
                        worksheet.write(row2,col + 12, str(product_id.barcode or '') , data_value_left_format)
                    if product_weight:
                        worksheet.write(row2,col + 13, str(product_id.weight or ''), data_value_center_format)
                    if product_volume:
                        worksheet.write(row2,col + 14, str(product_id.volume or ''), data_value_center_format)
                    if product_description:
                        worksheet.write(row2,col + 15, str(product_id.description_sale or ''), data_value_left_format)
                    if product_lead_time:
                        worksheet.write(row2,col + 16, str(product_id.sale_delay or ''), data_value_center_format)

                    for category in product_data['data'].get('categories_data'):
                        if 'prices' in category:
                            for prices,value in category['prices'].items():
                                if product_id.id == prices:
                                    for quantity,price in value.items():
                                        if qty1 and qty1_cell and qty_count == 'one':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty2 and qty2_cell_count and qty_count == 'two':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty3 and qty3_cell_count and qty_count == 'three':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty3 == quantity:
                                                worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty4 and qty4_cell_count and qty_count == 'four':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty3 == quantity:
                                                worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty4 == quantity:
                                                worksheet.write(qty_4 + 1,qty4_col, str('%.2f' % price or ''), data_value_center_format)
                                        else:
                                            if qty5 and qty5_cell_count and qty_count == 'five':
                                                if qty1 == quantity:
                                                    worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty2 == quantity:
                                                    worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty3 == quantity:
                                                    worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty4 == quantity:
                                                    worksheet.write(qty_4 + 1,qty4_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty5 == quantity:
                                                    worksheet.write(qty_5 + 1,qty5_col, str('%.2f' % price or ''), data_value_center_format)
                    row2 += 1
                    if qty1 and qty1_cell and qty_count == 'one':
                        # First Quantity
                        qty1_row += 1
                    elif qty2 and qty2_cell_count and qty_count == 'two':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                    elif qty3 and qty3_cell_count and qty_count == 'three':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                        # Third Quantity
                        qty3_row += 1
                    elif qty4 and qty4_cell_count and qty_count == 'four':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                        # Third Quantity
                        qty3_row += 1
                        # Four Quantity
                        qty4_row += 1
                    else:
                        if qty5 and qty5_cell_count and qty_count == 'five':
                            # First Quantity
                            qty1_row += 1
                            # Second Quantity
                            qty2_row += 1
                            # Third Quantity
                            qty3_row += 1
                            # Four Quantity
                            qty4_row += 1
                            # Five Quantity
                            qty5_row += 1

                    data_row = row2
                    data_row1 = row2

        elif template_type == 'template_3':

            if pricelist_report_data.get('pricelist_config').is_company_logo:
                company_id = self.env.user.company_id
                filenamelogo = company_id.name+ '.png'
                with open(filenamelogo, 'wb') as f:
                    f.write(company_id.logo)

                    fh = open(filenamelogo, "wb")
                    fh.write(base64.b64decode(company_id.logo))
                    fh.close()

                    img = Image.open(filenamelogo)
                    r, g, b, a = img.split()
                    img = Image.merge("RGBA", (r, g, b, a))
                    img.save(filenamelogo)
                    company_logo_cell = company_logo_cell.split(":")[0]
                    
                    # Image Width & Height
                    image_width  = pricelist_report_data.get('pricelist_config').company_logo_img_width
                    image_height = pricelist_report_data.get('pricelist_config').company_logo_img_height
                    
                    # Cell Width & Height
                    cell_width   = pricelist_report_data.get('pricelist_config').company_logo_cell_width
                    cell_height  = pricelist_report_data.get('pricelist_config').company_logo_cell_height

                    x_scale = cell_width/image_width
                    y_scale = cell_height/image_height

                    worksheet.insert_image(company_logo_cell, filenamelogo,
                                            {'x_scale': x_scale, 'y_scale': y_scale})

            if pricelist_report_data.get('pricelist_config').is_currency:
                currency = pricelist_report_data.get('pricelist_config').pricelist_id.currency_id.name
                worksheet.write(currency_cell, currency, data_header2_format)

            if pricelist_report_data.get('pricelist_config').is_date:
                worksheet.write(date_cell, str(datetime.now().date()), data_header2_format)

            if pricelist_report_data.get('pricelist_config').is_product_code:
                worksheet.write(pro_code_cell,"Internal Reference",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_name:
                worksheet.write(pro_name_cell,"Name",data_header_format) 

            if pricelist_report_data.get('pricelist_config').is_product_attributes:
                worksheet.write(pro_att_cell,"Attributes",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_taxes:
                worksheet.write(product_tax_cell,"Taxes",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_uom:
                worksheet.write(product_uom_cell,"UOM",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_uom:
                worksheet.write(product_uom_cell,"UOM",data_header_format)

            # Template 2 Extra Value
            if pricelist_report_data.get('pricelist_config').is_product_qty_case:
                worksheet.write(qty_case_cell_location,"QTY/Case",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_on_hand:
                worksheet.write(on_hand_cell_location,"On Hand",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_ean:
                worksheet.write(ean_cell_location,"EAN",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_weight:
                worksheet.write(weight_cell_location,"Weight (kg)",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_volume:
                worksheet.write(volume_cell_location,"Volume (m3)",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_description:
                worksheet.write(description_cell_location,"Description",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_lead_time:
                worksheet.write(lead_time_cell_location,"Lead Time",data_header_format)

            # Template 3 Extra Value
            if pricelist_report_data.get('pricelist_config').is_product_retail_price:
                worksheet.write(retail_price_cell_location,"Retail",data_header_format)

            if pricelist_report_data.get('pricelist_config').is_product_wholesale_price:
                worksheet.write(wholesale_price_cell_location,"Wholesale",data_header_format)

            qty1 = pricelist_report_data.get('qty1')
            qty2 = pricelist_report_data.get('qty2')
            qty3 = pricelist_report_data.get('qty3')
            qty4 = pricelist_report_data.get('qty4')
            qty5 = pricelist_report_data.get('qty5')

            worksheet.set_column(0,0, 20)
            worksheet.set_column(1,1, 25)
            worksheet.set_column(2,2, 50)
            worksheet.set_column(3,4, 25)
            worksheet.set_column(5,9, 15)
            worksheet.set_column(10,13, 15)
            worksheet.set_column(14,14, 25)
            worksheet.set_column(15,16, 15)
            worksheet.set_column(17,17, 50)
            worksheet.set_column(18,18, 15)

            product_code        = pricelist_report_data.get('pricelist_config').is_product_code
            product_name        = pricelist_report_data.get('pricelist_config').is_product_name
            product_attributes  = pricelist_report_data.get('pricelist_config').is_product_attributes
            product_taxes       = pricelist_report_data.get('pricelist_config').is_product_taxes
            product_uom         = pricelist_report_data.get('pricelist_config').is_product_uom

            # Template 2 Extra Value
            product_qty_case    = pricelist_report_data.get('pricelist_config').is_product_qty_case
            product_on_hand     = pricelist_report_data.get('pricelist_config').is_product_on_hand
            product_ean         = pricelist_report_data.get('pricelist_config').is_product_ean
            product_weight      = pricelist_report_data.get('pricelist_config').is_product_weight
            product_volume      = pricelist_report_data.get('pricelist_config').is_product_volume
            product_description = pricelist_report_data.get('pricelist_config').is_product_description
            product_lead_time   = pricelist_report_data.get('pricelist_config').is_product_lead_time

            # Template 3 Extra Value
            product_retail_price       = pricelist_report_data.get('pricelist_config').is_product_retail_price
            product_wholesale_price    = pricelist_report_data.get('pricelist_config').is_product_wholesale_price

            qty_count = pricelist_report_data.get('pricelist_config').qty_count

            if qty1 and qty1_cell and qty_count == 'one':
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

            elif qty2 and qty2_cell and qty_count == 'two':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

            elif qty3 and qty3_cell and qty_count == 'three':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                # Third Quantity
                qty3_data = str(qty3) + ' Units'
                worksheet.write(qty3_cell,qty3_data,data_header_format)
                qty3_cell = qty3_cell.split(":")[0]
                (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

            elif qty4 and qty4_cell and qty_count == 'four':
                # First Quantity
                qty1_data = str(qty1) + ' Units'
                worksheet.write(qty1_cell,qty1_data,data_header_format)
                qty1_cell = qty1_cell.split(":")[0]
                (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                # Second Quantity
                qty2_data = str(qty2) + ' Units'
                worksheet.write(qty2_cell,qty2_data,data_header_format)
                qty2_cell = qty2_cell.split(":")[0]
                (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                # Third Quantity
                qty3_data = str(qty3) + ' Units'
                worksheet.write(qty3_cell,qty3_data,data_header_format)
                qty3_cell = qty3_cell.split(":")[0]
                (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

                # Four Quantity
                qty4_data = str(qty4) + ' Units'
                worksheet.write(qty4_cell,qty4_data,data_header_format)
                qty4_cell = qty4_cell.split(":")[0]
                (qty4_row,qty4_col) = xl_cell_to_rowcol(qty4_cell)
            else:
                if qty5 and qty5_cell and qty_count == 'five':
                    # First Quantity
                    qty1_data = str(qty1) + ' Units'
                    worksheet.write(qty1_cell,qty1_data,data_header_format)
                    qty1_cell = qty1_cell.split(":")[0]
                    (qty1_row,qty1_col) = xl_cell_to_rowcol(qty1_cell)

                    # Second Quantity
                    qty2_data = str(qty2) + ' Units'
                    worksheet.write(qty2_cell,qty2_data,data_header_format)
                    qty2_cell = qty2_cell.split(":")[0]
                    (qty2_row,qty2_col) = xl_cell_to_rowcol(qty2_cell)

                    # Third Quantity
                    qty3_data = str(qty3) + ' Units'
                    worksheet.write(qty3_cell,qty3_data,data_header_format)
                    qty3_cell = qty3_cell.split(":")[0]
                    (qty3_row,qty3_col) = xl_cell_to_rowcol(qty3_cell)

                    # Four Quantity
                    qty4_data = str(qty4) + ' Units'
                    worksheet.write(qty4_cell,qty4_data,data_header_format)
                    qty4_cell = qty4_cell.split(":")[0]
                    (qty4_row,qty4_col) = xl_cell_to_rowcol(qty4_cell)

                    # Five Quantity
                    qty5_data = str(qty5) + ' Units'
                    worksheet.write(qty5_cell,qty5_data,data_header_format)
                    qty5_cell = qty5_cell.split(":")[0]
                    (qty5_row,qty5_col) = xl_cell_to_rowcol(qty5_cell)

            if product_code:
                a = pro_code_cell.split(":")[0]
                b = pro_code_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_name:
                a = pro_code_cell.split(":")[0]
                b = pro_name_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_attributes:
                a = pro_code_cell.split(":")[0]
                b = pro_att_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_taxes:
                a = pro_code_cell.split(":")[0]
                b = product_tax_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_uom:
                a = pro_code_cell.split(":")[0]
                b = product_uom_cell.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_retail_price:
                a = pro_code_cell.split(":")[0]
                b = retail_price_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_wholesale_price:
                a = pro_code_cell.split(":")[0]
                b = wholesale_price_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)

            if not product_name and not product_attributes and not product_taxes and \
                        not product_uom and not product_code and not product_qty_case and \
                        not product_retail_price and not product_wholesale_price and \
                        not product_on_hand and not product_ean and \
                        not product_weight and not product_volume and not product_description and \
                        not product_lead_time:
                (row, col) = (1 , 1)
                (row1, col1) = (1 , 1)

            if qty1 and qty1_cell_count and qty_count == 'one':
                a = pro_code_cell.split(":")[0]
                b = qty1_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty2 and qty2_cell_count and qty_count == 'two':
                a = pro_code_cell.split(":")[0]
                b = qty2_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty3 and qty3_cell_count and qty_count == 'three':
                a = pro_code_cell.split(":")[0]
                b = qty3_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            elif qty4 and qty4_cell_count and qty_count == 'four':
                a = pro_code_cell.split(":")[0]
                b = qty4_cell_count.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            else:
                if qty5 and qty5_cell_count and qty_count == 'five':
                    a = pro_code_cell.split(":")[0]
                    b = qty5_cell_count.split(":")[1]
                    (row, col) = xl_cell_to_rowcol(a)
                    (row1, col1) = xl_cell_to_rowcol(b)

            if product_qty_case:
                a = pro_code_cell.split(":")[0]
                b = qty_case_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_on_hand:
                a = pro_code_cell.split(":")[0]
                b = on_hand_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_ean:
                a = pro_code_cell.split(":")[0]
                b = ean_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_weight:
                a = pro_code_cell.split(":")[0]
                b = weight_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_volume:
                a = pro_code_cell.split(":")[0]
                b = volume_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_description:
                a = pro_code_cell.split(":")[0]
                b = description_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)
            if product_lead_time:
                a = pro_code_cell.split(":")[0]
                b = lead_time_cell_location.split(":")[1]
                (row, col) = xl_cell_to_rowcol(a)
                (row1, col1) = xl_cell_to_rowcol(b)

            worksheet.set_row(row, 40)

            data_row = row + 1
            data_row1 = row1 + 1
            categ_row = data_row

            for categ_line in my_list:
                if product_code and not product_name and not product_attributes and not product_taxes and \
                        not product_uom and not product_qty_case and not product_on_hand and \
                        not product_retail_price and not product_wholesale_price and \
                        not product_ean and not product_weight and not product_volume and not product_description and \
                        not product_lead_time:
                    worksheet.write(data_row, col, categ_line[0], data_categ_format)
                else:
                    worksheet.merge_range(data_row,col,data_row1,col1,categ_line[0],data_categ_format)
                data_row += 1
                data_row1 += 1
                categ_row += 1

                if qty1 and qty1_cell and qty_count == 'one':
                    # First Quantity
                    qty1_row += 1
                elif qty2 and qty2_cell_count and qty_count == 'two':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                elif qty3 and qty3_cell_count and qty_count == 'three':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                    # Third Quantity
                    qty3_row +=  1
                elif qty4 and qty4_cell_count and qty_count == 'four':
                    # First Quantity
                    qty1_row += 1
                    # Second Quantity
                    qty2_row +=  1
                    # Third Quantity
                    qty3_row +=  1
                    # Four Quantity
                    qty4_row +=  1
                else:
                    if qty5 and qty5_cell_count and qty_count == 'five':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row +=  1
                        # Third Quantity
                        qty3_row +=  1
                        # Four Quantity
                        qty4_row +=  1
                        # Five Quantity
                        qty5_row +=  1

                for product in categ_line[1]:
                    row2 = data_row
                    if qty1 and qty1_cell and qty_count == 'one':
                        # First Quantity
                        qty_1 = qty1_row
                    elif qty2 and qty2_cell_count and qty_count == 'two':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                    elif qty3 and qty3_cell_count and qty_count == 'three':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                        # Third Quantity
                        qty_3 = qty3_row
                    elif qty4 and qty4_cell_count and qty_count == 'four':
                        # First Quantity
                        qty_1 = qty1_row
                        # Second Quantity
                        qty_2 = qty2_row
                        # Third Quantity
                        qty_3 = qty3_row
                        # Four Quantity
                        qty_4 = qty4_row
                    else:
                        if qty5 and qty5_cell_count and qty_count == 'five':
                            # First Quantity
                            qty_1 = qty1_row
                            # Second Quantity
                            qty_2 = qty2_row
                            # Third Quantity
                            qty_3 = qty3_row
                            # Four Quantity
                            qty_4 = qty4_row
                            # Five Quantity
                            qty_5 = qty5_row

                    product_id = self.env['product.product'].browse(product)
                    name_att = ' '
                    for val in product_id.product_template_attribute_value_ids:
                        name_att += val.attribute_id.name + ':' + val.name + ', '
                    customer_tax = ' '
                    for tax in product_id.taxes_id:
                        customer_tax += tax.name + ', '
                    if product_code:
                        worksheet.write(row2,col, str(product_id.default_code or ''), data_value_left_format)
                    if product_name:
                        worksheet.write(row2,col + 1, str(product_id.name or ''), data_value_left_format)
                    if product_attributes:
                        worksheet.write(row2,col + 2, str(name_att or ''), data_value_left_format)
                    if product_taxes:
                        worksheet.write(row2,col + 3, str(customer_tax or ''), data_value_left_format)
                    if product_uom:
                        worksheet.write(row2,col + 4, str(product_id.uom_id.name or ''), data_value_center_format)
                    if product_retail_price:
                        worksheet.write(row2,col + 5, str('%.2f' % product_id.lst_price or ''), data_value_center_format)
                    if product_wholesale_price:
                        worksheet.write(row2,col + 6, str('%.2f' % product_id.standard_price or ''), data_value_center_format)
                    if product_qty_case:
                        worksheet.write(row2,col + 12, '', data_value_center_format)
                    if product_on_hand:
                        worksheet.write(row2,col + 13, product_id.qty_available, data_value_center_format)
                    if product_ean:
                        worksheet.write(row2,col + 14, str(product_id.barcode or '') , data_value_left_format)
                    if product_weight:
                        worksheet.write(row2,col + 15, str(product_id.weight or ''), data_value_center_format)
                    if product_volume:
                        worksheet.write(row2,col + 16, str(product_id.volume or ''), data_value_center_format)
                    if product_description:
                        worksheet.write(row2,col + 17, str(product_id.description_sale or ''), data_value_left_format)
                    if product_lead_time:
                        worksheet.write(row2,col + 18, str(product_id.sale_delay or ''), data_value_left_format)

                    for category in product_data['data'].get('categories_data'):
                        if 'prices' in category:
                            for prices,value in category['prices'].items():
                                if product_id.id == prices:
                                    for quantity,price in value.items():
                                        if qty1 and qty1_cell and qty_count == 'one':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty2 and qty2_cell_count and qty_count == 'two':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty3 and qty3_cell_count and qty_count == 'three':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty3 == quantity:
                                                worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                        elif qty4 and qty4_cell_count and qty_count == 'four':
                                            if qty1 == quantity:
                                                worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty2 == quantity:
                                                worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty3 == quantity:
                                                worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                            if qty4 == quantity:
                                                worksheet.write(qty_4 + 1,qty4_col, str('%.2f' % price or ''), data_value_center_format)
                                        else:
                                            if qty5 and qty5_cell_count and qty_count == 'five':
                                                if qty1 == quantity:
                                                    worksheet.write(qty_1 + 1,qty1_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty2 == quantity:
                                                    worksheet.write(qty_2 + 1,qty2_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty3 == quantity:
                                                    worksheet.write(qty_3 + 1,qty3_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty4 == quantity:
                                                    worksheet.write(qty_4 + 1,qty4_col, str('%.2f' % price or ''), data_value_center_format)
                                                if qty5 == quantity:
                                                    worksheet.write(qty_5 + 1,qty5_col, str('%.2f' % price or ''), data_value_center_format)
                    row2 += 1
                    if qty1 and qty1_cell and qty_count == 'one':
                        # First Quantity
                        qty1_row += 1
                    elif qty2 and qty2_cell_count and qty_count == 'two':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                    elif qty3 and qty3_cell_count and qty_count == 'three':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                        # Third Quantity
                        qty3_row += 1
                    elif qty4 and qty4_cell_count and qty_count == 'four':
                        # First Quantity
                        qty1_row += 1
                        # Second Quantity
                        qty2_row += 1
                        # Third Quantity
                        qty3_row += 1
                        # Four Quantity
                        qty4_row += 1
                    else:
                        if qty5 and qty5_cell_count and qty_count == 'five':
                            # First Quantity
                            qty1_row += 1
                            # Second Quantity
                            qty2_row += 1
                            # Third Quantity
                            qty3_row += 1
                            # Four Quantity
                            qty4_row += 1
                            # Five Quantity
                            qty5_row += 1

                    data_row = row2
                    data_row1 = row2

        workbook.close()
        buf = base64.b64encode(open('/tmp/' + filename, 'rb+').read())
        a =self.env['excel.report'].create({
                    'excel_file' : buf,
                    'file_name' :   filename
        })
        return {
            'res_id': a.id,
            'name': 'Files to Download',
            "view_mode": 'form,tree',
            'res_model': 'excel.report',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
