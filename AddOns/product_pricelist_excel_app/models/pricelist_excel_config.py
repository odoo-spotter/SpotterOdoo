# -*- coding: utf-8 -*-


from odoo import api, fields, models


class PricelistConfig(models.Model):
    _name = 'pricelist.config'
    _description ="PriceList Configuration"

    name = fields.Char('Name')
    pricelist_id = fields.Many2one('product.pricelist',string='Pricelist')
    file_name = fields.Char('File Name')
    is_category = fields.Boolean('Category')
    color_name = fields.Char('Color')
    sheet_name = fields.Char('Sheet Name')
    header_location = fields.Char('Header Loaction')
    is_company = fields.Boolean('Company Name')
    is_company_logo = fields.Boolean('Company Logo')
    is_currency = fields.Boolean('Currency Name')
    is_date = fields.Boolean('Date')

    company_logo_img_width = fields.Float('Image Width', default=100.0)
    company_logo_img_height = fields.Float('Image Height', default=150.0)

    company_logo_cell_width = fields.Float('Cell Width', default=50.0)
    company_logo_cell_height = fields.Float('Cell Height', default=75.0)

    company_logo_cell_location = fields.Char('Company Logo Cell Location')
    company_cell_location = fields.Char('Company Cell Location')
    currency_cell_location = fields.Char('Currency Cell Location')
    date_cell_location = fields.Char('Date Cell Location')

    qty_count = fields.Selection([('one','One'),('two','Two'),('three','Three'),('four','Four'),('five','Five')],string='Quantity')
    template_type = fields.Selection([('template_1','Product Pricelist'),
                                      ('template_2','Product Pricelist With Extra Features'),
                                      ('template_3','Product Pricelist And Company Logo With Extra Features')], 'Template')

    qty_count_one = fields.Boolean('Quantity One')
    qty_count_two = fields.Boolean('Quantity Two')
    qty_count_three = fields.Boolean('Quantity Three')
    qty_count_four = fields.Boolean('Quantity Four')
    qty_count_five = fields.Boolean('Quantity Five')

    qty1_cell_location = fields.Char('First Quantity')
    qty2_cell_location = fields.Char('Second Quantity')
    qty3_cell_location = fields.Char('Third Quantity')
    qty4_cell_location = fields.Char('Fourth Quantity')
    qty5_cell_location = fields.Char('Fifth Quantity')

    is_product_code = fields.Boolean('Product Internal Reference')
    is_product_name = fields.Boolean('Product Name')
    is_product_attributes = fields.Boolean('Product Attributes')
    is_product_taxes = fields.Boolean('Taxes')
    is_product_uom = fields.Boolean('Product UOM')
    is_product_qty_case = fields.Boolean('QTY/Case')
    is_product_on_hand = fields.Boolean('On Hand')
    is_product_ean = fields.Boolean('EAN')
    is_product_weight = fields.Boolean('Weight (kg)')
    is_product_volume = fields.Boolean('Volume (m3)')
    is_product_description = fields.Boolean('Description')
    is_product_lead_time = fields.Boolean('Lead Time')
    is_product_retail_price = fields.Boolean('Retail Price')
    is_product_wholesale_price = fields.Boolean('Wholesale Price')

    product_code_cell_location = fields.Char('Code Cell Location')
    product_name_location = fields.Char('Product Cell Location')
    product_attributes_cell_location = fields.Char('Product Attributes Cell Location')
    product_taxes_cell_location = fields.Char('Taxes Cell Location')
    product_uom_cell_location = fields.Char('Product UOM Cell Location')
    product_qty_case_cell_location = fields.Char('Product QTY/Case Cell Location')
    product_on_hand_cell_location = fields.Char('Product On Hand Cell Location')
    product_ean_cell_location = fields.Char('Product EAN Cell Location')
    product_weight_cell_location = fields.Char('Product Weight (kg) Cell Location')
    product_volume_cell_location = fields.Char('Product Volume (m3) Cell Location')
    product_description_cell_location = fields.Char('Product Description Cell Location')
    product_lead_time_cell_location = fields.Char('Product Lead Time Cell Location')
    product_retail_price_cell_location = fields.Char('Product Retail Price Cell Location')
    product_wholesale_price_cell_location = fields.Char('Product Wholesale Price Cell Location')

    @api.onchange('qty_count')
    def on_change_qty_count(self):
        if self.qty_count == 'one':
            self.qty_count_one = True
            self.qty_count_two = False
            self.qty_count_three = False
            self.qty_count_four = False
            self.qty_count_five = False
        elif self.qty_count == 'two':
            self.qty_count_one = True
            self.qty_count_two = True
            self.qty_count_three = False
            self.qty_count_four = False
            self.qty_count_five = False
        elif self.qty_count == 'three':
            self.qty_count_one = True
            self.qty_count_two = True
            self.qty_count_three = True
            self.qty_count_four = False
            self.qty_count_five = False
        elif self.qty_count == 'four':
            self.qty_count_one = True
            self.qty_count_two = True
            self.qty_count_three = True
            self.qty_count_four = True
            self.qty_count_five = False
        elif self.qty_count == 'five':
            self.qty_count_one = True
            self.qty_count_two = True
            self.qty_count_three = True
            self.qty_count_four = True
            self.qty_count_five = True
        else:
            self.qty_count_one = False
            self.qty_count_two = False
            self.qty_count_three = False
            self.qty_count_four = False
            self.qty_count_five = False


class ExcelReport(models.TransientModel):
    _name = "excel.report"
    _description ="Excel Report"

    excel_file = fields.Binary('Excel Report')
    file_name = fields.Char('Excel File', size=64)


