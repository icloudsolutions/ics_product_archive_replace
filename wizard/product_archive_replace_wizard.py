# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductArchiveReplaceWizard(models.TransientModel):
    _name = 'product.archive.replace.wizard'
    _description = 'Archive Product & Create Replacement'

    # ========== SELECTION MODE ==========
    selection_mode = fields.Selection([
        ('single', 'Selected Products'),
        ('category', 'By Category'),
    ], default='single', string="Selection Mode", required=True)

    # ========== SINGLE PRODUCT SELECTION ==========
    product_ids = fields.Many2many(
        'product.template',
        string='Products to Replace',
        domain=[('active', '=', True)]
    )
    
    # ========== CATEGORY SELECTION ==========
    category_ids = fields.Many2many(
        'product.category',
        string='Product Categories'
    )
    include_subcategories = fields.Boolean('Include Subcategories', default=True)
    
    # ========== TYPE FILTER ==========
    filter_by_type = fields.Boolean('Filter by Current Type', default=False)
    current_type_filter = fields.Selection([
        ('product', 'Storable Product'),
        ('consu', 'Consumable'),
        ('service', 'Service'),
    ], string="Current Type Filter")
    
    new_type = fields.Selection([
        ('product', 'Storable Product'),
        ('consu', 'Consumable'),
        ('service', 'Service'),
    ], required=True, string="New Product Type")
    
    # ========== MIGRATION OPTIONS ==========
    migrate_sales = fields.Boolean('Migrate Sales Orders', default=True)
    migrate_purchases = fields.Boolean('Migrate Purchase Orders', default=True)
    migrate_boms = fields.Boolean('Migrate BOMs (if MRP installed)', default=True)
    migrate_pricelists = fields.Boolean('Migrate Pricelists', default=True)
    migrate_vendors = fields.Boolean('Migrate Vendors', default=True)
    migrate_stock = fields.Boolean('Transfer Stock (On Hand Quantities)', default=True)
    
    continue_on_error = fields.Boolean('Continue on Migration Errors', default=True)
    
    # ========== CHECK MRP AVAILABILITY ==========
    has_mrp = fields.Boolean('MRP Module Installed', compute='_compute_has_mrp')
    
    # ========== COMPUTED COUNTS ==========
    product_count = fields.Integer('Products to Process', compute='_compute_product_count')
    total_sale_count = fields.Integer('Total Sales Orders', compute='_compute_total_counts')
    total_purchase_count = fields.Integer('Total Purchase Orders', compute='_compute_total_counts')
    total_bom_count = fields.Integer('Total BOMs', compute='_compute_total_counts')
    total_pricelist_count = fields.Integer('Total Pricelists', compute='_compute_total_counts')
    total_vendor_count = fields.Integer('Total Vendors', compute='_compute_total_counts')
    total_stock_qty = fields.Float('Total Stock Quantity', compute='_compute_total_counts')
    
    # ========== PREVIEW LIST ==========
    preview_line_ids = fields.One2many(
        'product.archive.replace.preview.line',
        'wizard_id',
        string='Products Preview',
        compute='_compute_preview_lines',
        store=False
    )
    show_preview = fields.Boolean('Show Products List', default=False)
    
    # ========== AUDIT REPORT FIELDS ==========
    migration_date = fields.Datetime('Migration Date', readonly=True)
    migration_user_id = fields.Many2one('res.users', string='Executed By', readonly=True)
    success_count = fields.Integer('Successful Replacements', readonly=True)
    failed_count = fields.Integer('Failed Replacements', readonly=True)
    
    # ========== RESULTS ==========
    result_line_ids = fields.One2many(
        'product.archive.replace.result.line',
        'wizard_id',
        string='Migration Results',
        readonly=True
    )
    migration_summary = fields.Html('Migration Summary', readonly=True)
    show_results = fields.Boolean('Show Results', default=False)

    # ========== COMPUTE METHODS ==========
    
    def _compute_has_mrp(self):
        """Check if MRP module is installed"""
        for wizard in self:
            wizard.has_mrp = 'mrp.bom' in self.env

    @api.model
    def default_get(self, fields_list):
        """Pre-select products from context"""
        res = super().default_get(fields_list)
        
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model', '')
        
        _logger.info(f"Default_get called with active_ids: {active_ids}, active_model: {active_model}")
        
        if active_model == 'product.template' and active_ids:
            res['product_ids'] = [(6, 0, active_ids)]
            res['selection_mode'] = 'single'
            _logger.info(f"Pre-selected {len(active_ids)} products")
        
        return res

    def _get_target_products(self):
        """Get all products to process based on selection mode"""
        if self.selection_mode == 'single':
            products = self.product_ids
        else:
            # Category mode
            domain = []
            
            if self.filter_by_type and self.current_type_filter:
                domain.append(('type', '=', self.current_type_filter))
            
            if self.category_ids:
                categories = self.category_ids
                if self.include_subcategories:
                    categories = self.env['product.category'].search([
                        ('id', 'child_of', self.category_ids.ids)
                    ])
                domain.append(('categ_id', 'in', categories.ids))
            
            domain.append(('active', '=', True))
            products = self.env['product.template'].search(domain)
        
        # Filter out products that already have the target type
        products = products.filtered(lambda p: p.type != self.new_type)
        
        return products

    @api.depends('selection_mode', 'product_ids', 'category_ids', 'include_subcategories', 
                 'filter_by_type', 'current_type_filter', 'new_type')
    def _compute_product_count(self):
        """Count products to process"""
        for wizard in self:
            products = wizard._get_target_products()
            wizard.product_count = len(products)

    @api.depends('selection_mode', 'product_ids', 'category_ids', 'include_subcategories',
                 'filter_by_type', 'current_type_filter', 'new_type')
    def _compute_preview_lines(self):
        """Generate preview lines for each product"""
        for wizard in self:
            wizard.preview_line_ids = [(5, 0, 0)]
            
            products = wizard._get_target_products()
            
            if not products:
                continue
            
            lines = []
            for product in products:
                variants = product.product_variant_ids
                variant_ids = variants.ids
                
                sale_count = self.env['sale.order.line'].search_count([
                    ('product_id', 'in', variant_ids)
                ]) if variant_ids else 0
                
                purchase_count = self.env['purchase.order.line'].search_count([
                    ('product_id', 'in', variant_ids)
                ]) if variant_ids else 0
                
                bom_count = 0
                if wizard.has_mrp:
                    bom_main = self.env['mrp.bom'].search_count([
                        ('product_tmpl_id', '=', product.id)
                    ])
                    bom_lines = self.env['mrp.bom.line'].search_count([
                        ('product_id', 'in', variant_ids)
                    ]) if variant_ids else 0
                    bom_count = bom_main + bom_lines
                
                pricelist_count = self.env['product.pricelist.item'].search_count([
                    '|',
                    ('product_tmpl_id', '=', product.id),
                    ('product_id', 'in', variant_ids)
                ]) if variant_ids else 0
                
                vendor_count = self.env['product.supplierinfo'].search_count([
                    '|',
                    ('product_tmpl_id', '=', product.id),
                    ('product_id', 'in', variant_ids)
                ]) if variant_ids else 0
                
                stock_qty = sum(variants.mapped('qty_available'))
                
                lines.append((0, 0, {
                    'product_id': product.id,
                    'current_type': product.type,
                    'default_code': product.default_code or '',
                    'barcode': product.barcode or '',
                    'categ_id': product.categ_id.id,
                    'sale_count': sale_count,
                    'purchase_count': purchase_count,
                    'bom_count': bom_count,
                    'pricelist_count': pricelist_count,
                    'vendor_count': vendor_count,
                    'stock_qty': stock_qty,
                }))
            
            wizard.preview_line_ids = lines

    @api.depends('selection_mode', 'product_ids', 'category_ids', 'include_subcategories',
                 'filter_by_type', 'current_type_filter', 'new_type')
    def _compute_total_counts(self):
        """Compute total counts for all products"""
        for wizard in self:
            products = wizard._get_target_products()
            
            if not products:
                wizard.total_sale_count = 0
                wizard.total_purchase_count = 0
                wizard.total_bom_count = 0
                wizard.total_pricelist_count = 0
                wizard.total_vendor_count = 0
                wizard.total_stock_qty = 0
                continue
            
            try:
                all_variants = products.mapped('product_variant_ids')
                variant_ids = all_variants.ids
                template_ids = products.ids
                
                wizard.total_sale_count = self.env['sale.order.line'].search_count([
                    ('product_id', 'in', variant_ids)
                ]) if variant_ids else 0
                
                wizard.total_purchase_count = self.env['purchase.order.line'].search_count([
                    ('product_id', 'in', variant_ids)
                ]) if variant_ids else 0
                
                if wizard.has_mrp:
                    bom_main = self.env['mrp.bom'].search_count([
                        ('product_tmpl_id', 'in', template_ids)
                    ]) if template_ids else 0
                    
                    bom_lines = self.env['mrp.bom.line'].search_count([
                        ('product_id', 'in', variant_ids)
                    ]) if variant_ids else 0
                    
                    wizard.total_bom_count = bom_main + bom_lines
                else:
                    wizard.total_bom_count = 0
                
                wizard.total_pricelist_count = self.env['product.pricelist.item'].search_count([
                    '|',
                    ('product_tmpl_id', 'in', template_ids),
                    ('product_id', 'in', variant_ids)
                ]) if (template_ids or variant_ids) else 0
                
                wizard.total_vendor_count = self.env['product.supplierinfo'].search_count([
                    '|',
                    ('product_tmpl_id', 'in', template_ids),
                    ('product_id', 'in', variant_ids)
                ]) if (template_ids or variant_ids) else 0
                
                wizard.total_stock_qty = sum(all_variants.mapped('qty_available'))
                
            except Exception as e:
                _logger.error(f"Error computing counts: {e}", exc_info=True)
                wizard.total_sale_count = 0
                wizard.total_purchase_count = 0
                wizard.total_bom_count = 0
                wizard.total_pricelist_count = 0
                wizard.total_vendor_count = 0
                wizard.total_stock_qty = 0

    # ========== ACTIONS ==========

    def action_toggle_preview(self):
        """Toggle the product list preview"""
        self.show_preview = not self.show_preview
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.archive.replace.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_replace(self):
        """Main action: Archive old, create new, migrate references"""
        self.ensure_one()
        
        products = self._get_target_products()
        
        if not products:
            raise UserError(_("No products to process. Check your selection."))
        
        self.migration_date = fields.Datetime.now()
        self.migration_user_id = self.env.user
        
        _logger.info("="*80)
        _logger.info(f"STARTING MASS ARCHIVE & REPLACE")
        _logger.info(f"Products to process: {len(products)}")
        _logger.info(f"Target type: {self.new_type}")
        _logger.info(f"Executed by: {self.env.user.name}")
        _logger.info("="*80)
        
        summary_lines = []
        summary_lines.append(f"<h3>🔄 Mass Archive & Replace Summary</h3>")
        summary_lines.append(f"<p><strong>Processed {len(products)} products</strong></p>")
        summary_lines.append("<hr/>")
        
        success_count = 0
        failed_count = 0
        result_lines = []
        
        for product in products:
            try:
                result_data = self._process_single_product(product)
                summary_lines.append(result_data['html'])
                
                result_lines.append((0, 0, {
                    'old_product_id': product.id,
                    'old_product_name': product.name,
                    'old_default_code': product.default_code or '',
                    'old_barcode': product.barcode or '',
                    'old_type': product.type,
                    'new_product_id': result_data.get('new_product_id'),
                    'new_product_name': result_data.get('new_product_name', ''),
                    'new_type': self.new_type,
                    'status': 'success',
                    'sales_migrated': result_data.get('sales_count', 0),
                    'purchases_migrated': result_data.get('purchases_count', 0),
                    'boms_migrated': result_data.get('boms_count', 0),
                    'pricelists_migrated': result_data.get('pricelists_count', 0),
                    'vendors_migrated': result_data.get('vendors_count', 0),
                    'stock_transferred': result_data.get('stock_qty', 0),
                    'error_message': '',
                }))
                
                success_count += 1
                
            except Exception as e:
                error_msg = f"<p style='color: red;'>❌ <strong>{product.name}</strong>: {str(e)}</p>"
                summary_lines.append(error_msg)
                _logger.error(f"Failed to process {product.name}: {e}", exc_info=True)
                
                result_lines.append((0, 0, {
                    'old_product_id': product.id,
                    'old_product_name': product.name,
                    'old_default_code': product.default_code or '',
                    'old_barcode': product.barcode or '',
                    'old_type': product.type,
                    'new_type': self.new_type,
                    'status': 'failed',
                    'error_message': str(e),
                }))
                
                failed_count += 1
                
                if not self.continue_on_error:
                    raise
        
        summary_lines.append("<hr/>")
        summary_lines.append(f"<p><strong>Results:</strong></p>")
        summary_lines.append(f"<ul>")
        summary_lines.append(f"<li style='color: green;'>✅ Success: {success_count}</li>")
        if failed_count > 0:
            summary_lines.append(f"<li style='color: red;'>❌ Failed: {failed_count}</li>")
        summary_lines.append(f"</ul>")
        
        self.migration_summary = ''.join(summary_lines)
        self.show_results = True
        self.success_count = success_count
        self.failed_count = failed_count
        self.result_line_ids = result_lines
        
        _logger.info("="*80)
        _logger.info(f"MASS MIGRATION COMPLETED")
        _logger.info(f"Success: {success_count}, Failed: {failed_count}")
        _logger.info("="*80)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.archive.replace.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _process_single_product(self, old_product):
        """Process a single product replacement - returns structured data"""
        log_lines = []
        log_lines.append(f"<p><strong>📦 {old_product.name}</strong></p>")
        log_lines.append("<ul>")
        
        _logger.info(f"Processing product: {old_product.name} (ID: {old_product.id})")
        
        barcode = old_product.barcode
        default_code = old_product.default_code
        
        copy_vals = {
            'name': old_product.name,
            'type': self.new_type,
            'barcode': barcode,
            'default_code': default_code,
            'active': True,
        }
        
        if hasattr(old_product, 'detailed_type'):
            type_to_detailed = {
                'product': 'product',
                'consu': 'consu', 
                'service': 'service',
            }
            copy_vals['detailed_type'] = type_to_detailed.get(self.new_type, self.new_type)
        
        try:
            old_product.write({'barcode': False, 'default_code': False})
            new_product = old_product.copy(copy_vals)
            log_lines.append(f"<li>✅ Created new product (ID: {new_product.id})</li>")
            _logger.info(f"Created new product ID: {new_product.id}")
        except Exception as e:
            try:
                old_product.write({'barcode': barcode, 'default_code': default_code})
            except:
                pass
            raise UserError(f"Failed to create new product: {e}")
        
        counts = {
            'new_product_id': new_product.id,
            'new_product_name': new_product.name,
            'sales_count': 0,
            'purchases_count': 0,
            'boms_count': 0,
            'pricelists_count': 0,
            'vendors_count': 0,
            'stock_qty': 0,
        }
        
        if self.migrate_sales:
            count = self._migrate_sales_orders(old_product, new_product)
            counts['sales_count'] = count
            if count > 0:
                log_lines.append(f"<li>✅ Sales: {count} lines migrated</li>")
        
        if self.migrate_purchases:
            count = self._migrate_purchase_orders(old_product, new_product)
            counts['purchases_count'] = count
            if count > 0:
                log_lines.append(f"<li>✅ Purchases: {count} lines migrated</li>")
        
        if self.migrate_boms and self.has_mrp:
            count = self._migrate_boms(old_product, new_product)
            counts['boms_count'] = count
            if count > 0:
                log_lines.append(f"<li>✅ BOMs: {count} records migrated</li>")
        
        if self.migrate_pricelists:
            count = self._migrate_pricelists(old_product, new_product)
            counts['pricelists_count'] = count
            if count > 0:
                log_lines.append(f"<li>✅ Pricelists: {count} rules migrated</li>")
        
        if self.migrate_vendors:
            count = self._migrate_vendors(old_product, new_product)
            counts['vendors_count'] = count
            if count > 0:
                log_lines.append(f"<li>✅ Vendors: {count} records migrated</li>")
        
        if self.migrate_stock and old_product.type == 'product':
            qty = self._transfer_stock(old_product, new_product)
            counts['stock_qty'] = qty
            if qty != 0:
                log_lines.append(f"<li>✅ Stock: {qty} units transferred</li>")
        
        try:
            old_product.active = False
            log_lines.append(f"<li>✅ Archived old product</li>")
        except Exception as e:
            log_lines.append(f"<li>⚠️ Could not archive: {e}</li>")
        
        try:
            old_product.message_post(
                body=f"<p>🔄 <strong>Replaced by:</strong> {new_product.name} (ID: {new_product.id})</p>",
                subject="Product Replaced"
            )
            new_product.message_post(
                body=f"<p>✅ <strong>Replacement for:</strong> {old_product.name} (ID: {old_product.id})</p>",
                subject="Product Created"
            )
        except:
            pass
        
        log_lines.append("</ul>")
        counts['html'] = ''.join(log_lines)
        
        return counts

    # ========== MIGRATION METHODS ==========

    def _migrate_sales_orders(self, old_product, new_product):
        """Migrate sales order lines"""
        try:
            old_variants = old_product.product_variant_ids
            new_variant = new_product.product_variant_ids[0]
            lines = self.env['sale.order.line'].search([('product_id', 'in', old_variants.ids)])
            count = 0
            for line in lines:
                try:
                    line.product_id = new_variant
                    count += 1
                except Exception as e:
                    _logger.warning(f"Failed to migrate SO line {line.id}: {e}")
                    if not self.continue_on_error:
                        raise
            return count
        except Exception as e:
            _logger.error(f"Sales migration error: {e}")
            if not self.continue_on_error:
                raise
            return 0

    def _migrate_purchase_orders(self, old_product, new_product):
        """Migrate purchase order lines"""
        try:
            old_variants = old_product.product_variant_ids
            new_variant = new_product.product_variant_ids[0]
            lines = self.env['purchase.order.line'].search([('product_id', 'in', old_variants.ids)])
            count = 0
            for line in lines:
                try:
                    line.product_id = new_variant
                    count += 1
                except Exception as e:
                    _logger.warning(f"Failed to migrate PO line {line.id}: {e}")
                    if not self.continue_on_error:
                        raise
            return count
        except Exception as e:
            _logger.error(f"Purchase migration error: {e}")
            if not self.continue_on_error:
                raise
            return 0

    def _migrate_boms(self, old_product, new_product):
        """Migrate bills of materials"""
        if not self.has_mrp:
            return 0
        try:
            old_variants = old_product.product_variant_ids
            new_variant = new_product.product_variant_ids[0]
            count = 0
            boms = self.env['mrp.bom'].search([('product_tmpl_id', '=', old_product.id)])
            for bom in boms:
                try:
                    bom.write({
                        'product_tmpl_id': new_product.id,
                        'product_id': new_variant.id if bom.product_id else False
                    })
                    count += 1
                except Exception as e:
                    _logger.warning(f"Failed to migrate BOM {bom.id}: {e}")
                    if not self.continue_on_error:
                        raise
            bom_lines = self.env['mrp.bom.line'].search([('product_id', 'in', old_variants.ids)])
            for line in bom_lines:
                try:
                    line.product_id = new_variant
                    count += 1
                except Exception as e:
                    _logger.warning(f"Failed to migrate BOM line {line.id}: {e}")
                    if not self.continue_on_error:
                        raise
            return count
        except Exception as e:
            _logger.error(f"BOM migration error: {e}")
            if not self.continue_on_error:
                raise
            return 0

    def _migrate_pricelists(self, old_product, new_product):
        """Migrate pricelist items"""
        try:
            old_variants = old_product.product_variant_ids
            new_variant = new_product.product_variant_ids[0]
            items = self.env['product.pricelist.item'].search([
                '|', ('product_tmpl_id', '=', old_product.id),
                ('product_id', 'in', old_variants.ids)
            ])
            count = 0
            for item in items:
                try:
                    item.write({
                        'product_tmpl_id': new_product.id if item.product_tmpl_id else False,
                        'product_id': new_variant.id if item.product_id else False
                    })
                    count += 1
                except Exception as e:
                    _logger.warning(f"Failed to migrate pricelist {item.id}: {e}")
                    if not self.continue_on_error:
                        raise
            return count
        except Exception as e:
            _logger.error(f"Pricelist migration error: {e}")
            if not self.continue_on_error:
                raise
            return 0

    def _migrate_vendors(self, old_product, new_product):
        """Migrate vendor records"""
        try:
            old_variants = old_product.product_variant_ids
            new_variant = new_product.product_variant_ids[0]
            suppliers = self.env['product.supplierinfo'].search([
                '|', ('product_tmpl_id', '=', old_product.id),
                ('product_id', 'in', old_variants.ids)
            ])
            count = 0
            for supplier in suppliers:
                try:
                    supplier.write({
                        'product_tmpl_id': new_product.id if supplier.product_tmpl_id else False,
                        'product_id': new_variant.id if supplier.product_id else False
                    })
                    count += 1
                except Exception as e:
                    _logger.warning(f"Failed to migrate vendor {supplier.id}: {e}")
                    if not self.continue_on_error:
                        raise
            return count
        except Exception as e:
            _logger.error(f"Vendor migration error: {e}")
            if not self.continue_on_error:
                raise
            return 0

    def _transfer_stock(self, old_product, new_product):
        """Transfer stock quantities"""
        try:
            if old_product.type != 'product':
                return 0
            old_variants = old_product.product_variant_ids
            new_variant = new_product.product_variant_ids[0]
            total_qty = 0
            quants = self.env['stock.quant'].search([
                ('product_id', 'in', old_variants.ids),
                ('location_id.usage', '=', 'internal')
            ])
            for quant in quants:
                if quant.quantity == 0:
                    continue
                try:
                    qty = quant.quantity
                    self.env['stock.quant'].with_context(inventory_mode=True)._update_available_quantity(
                        new_variant, quant.location_id, qty,
                        lot_id=quant.lot_id, package_id=quant.package_id, owner_id=quant.owner_id
                    )
                    self.env['stock.quant'].with_context(inventory_mode=True)._update_available_quantity(
                        quant.product_id, quant.location_id, -qty,
                        lot_id=quant.lot_id, package_id=quant.package_id, owner_id=quant.owner_id
                    )
                    total_qty += qty
                except Exception as e:
                    _logger.warning(f"Failed to transfer stock in location {quant.location_id.name}: {e}")
                    if not self.continue_on_error:
                        raise
            return total_qty
        except Exception as e:
            _logger.error(f"Stock transfer error: {e}")
            if not self.continue_on_error:
                raise
            return 0

    def action_print_audit_report(self):
        """Generate PDF audit report"""
        self.ensure_one()
        return self.env.ref('ics_product_archive_replace.action_report_product_archive_replace').report_action(self)

    def action_export_excel(self):
        """Export results to Excel"""
        self.ensure_one()
        raise UserError(_("Excel export will be available in next version"))

    def action_view_new_products(self):
        """View all newly created products"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('create_date', '>=', fields.Datetime.now())],
            'context': {'search_default_filter_to_sell': 1}
        }


# ============================================================================
# PREVIEW LINE MODEL
# ============================================================================

class ProductArchiveReplacePreviewLine(models.TransientModel):
    _name = 'product.archive.replace.preview.line'
    _description = 'Product Replace Preview Line'
    _order = 'product_name'

    wizard_id = fields.Many2one('product.archive.replace.wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.template', string='Product', required=True)
    product_name = fields.Char(related='product_id.name', string='Product Name', readonly=True)
    default_code = fields.Char(string='Internal Reference', readonly=True)
    barcode = fields.Char(string='Barcode', readonly=True)
    current_type = fields.Selection([
        ('product', 'Storable'),
        ('consu', 'Consumable'),
        ('service', 'Service'),
    ], string='Current Type', readonly=True)
    categ_id = fields.Many2one('product.category', string='Category', readonly=True)
    
    sale_count = fields.Integer('Sales Lines', readonly=True)
    purchase_count = fields.Integer('Purchase Lines', readonly=True)
    bom_count = fields.Integer('BOMs', readonly=True)
    pricelist_count = fields.Integer('Pricelists', readonly=True)
    vendor_count = fields.Integer('Vendors', readonly=True)
    stock_qty = fields.Float('Stock Qty', readonly=True)
    
    has_references = fields.Boolean(compute='_compute_has_references', store=False)
    has_stock = fields.Boolean(compute='_compute_has_stock', store=False)
    
    @api.depends('sale_count', 'purchase_count', 'bom_count', 'pricelist_count', 'vendor_count')
    def _compute_has_references(self):
        for line in self:
            line.has_references = any([
                line.sale_count > 0,
                line.purchase_count > 0,
                line.bom_count > 0,
                line.pricelist_count > 0,
                line.vendor_count > 0
            ])
    
    @api.depends('stock_qty')
    def _compute_has_stock(self):
        for line in self:
            line.has_stock = line.stock_qty != 0


# ============================================================================
# RESULT LINE MODEL
# ============================================================================

class ProductArchiveReplaceResultLine(models.TransientModel):
    _name = 'product.archive.replace.result.line'
    _description = 'Product Replacement Result Line'
    _order = 'old_product_name'

    wizard_id = fields.Many2one('product.archive.replace.wizard', required=True, ondelete='cascade')
    
    old_product_id = fields.Many2one('product.template', string='Old Product', readonly=True)
    old_product_name = fields.Char('Old Product Name', readonly=True)
    old_default_code = fields.Char('Old Ref', readonly=True)
    old_barcode = fields.Char('Old Barcode', readonly=True)
    old_type = fields.Selection([
        ('product', 'Storable'),
        ('consu', 'Consumable'),
        ('service', 'Service'),
    ], string='Old Type', readonly=True)
    
    new_product_id = fields.Many2one('product.template', string='New Product', readonly=True)
    new_product_name = fields.Char('New Product Name', readonly=True)
    new_type = fields.Selection([
        ('product', 'Storable'),
        ('consu', 'Consumable'),
        ('service', 'Service'),
    ], string='New Type', readonly=True)
    
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
    ], string='Status', readonly=True)
    
    sales_migrated = fields.Integer('Sales Lines', readonly=True)
    purchases_migrated = fields.Integer('Purchase Lines', readonly=True)
    boms_migrated = fields.Integer('BOMs', readonly=True)
    pricelists_migrated = fields.Integer('Pricelists', readonly=True)
    vendors_migrated = fields.Integer('Vendors', readonly=True)
    stock_transferred = fields.Float('Stock Transferred', readonly=True)
    
    error_message = fields.Text('Error Message', readonly=True)
    
    type_change = fields.Char('Type Change', compute='_compute_type_change', store=False)
    
    @api.depends('old_type', 'new_type')
    def _compute_type_change(self):
        for line in self:
            type_map = {
                'product': 'Storable',
                'consu': 'Consumable',
                'service': 'Service',
            }
            old = type_map.get(line.old_type, line.old_type)
            new = type_map.get(line.new_type, line.new_type)
            line.type_change = f"{old} → {new}"            