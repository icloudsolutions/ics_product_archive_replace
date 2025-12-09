# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ========== REPLACEMENT TRACKING FIELDS ==========
    replacement_template_id = fields.Many2one(
        'product.template',
        string='Replaced By',
        help='The new product that replaced this archived product',
        index=True,
        copy=False,
        tracking=True
    )
    
    replaced_template_id = fields.Many2one(
        'product.template',
        string='Replacement For',
        help='The old product that this product replaces',
        index=True,
        copy=False,
        tracking=True
    )
    
    replacement_date = fields.Datetime(
        string='Replacement Date',
        help='When this product was replaced',
        copy=False,
        tracking=True
    )
    
    replacement_user_id = fields.Many2one(
        'res.users',
        string='Replaced By User',
        help='User who executed the replacement',
        copy=False
    )
    
    original_type = fields.Selection([
        ('product', 'Storable'),
        ('consu', 'Consumable'),
        ('service', 'Service'),
    ], string='Original Type', 
       help='Product type before replacement',
       copy=False
    )
    
    # ========== COMPUTED FIELDS ==========
    is_replacement = fields.Boolean(
        string='Is Replacement Product',
        compute='_compute_replacement_status',
        store=True,
        help='This product replaces an archived product'
    )
    
    was_replaced = fields.Boolean(
        string='Was Replaced',
        compute='_compute_replacement_status',
        store=True,
        help='This product was archived and replaced'
    )
    
    replacement_chain_count = fields.Integer(
        string='Replacement Chain Length',
        compute='_compute_replacement_chain',
        store=True,        
        help='Number of products in replacement chain'
    )
    
    # ========== COMPUTE METHODS ==========
    
    @api.depends('replacement_template_id', 'replaced_template_id')
    def _compute_replacement_status(self):
        """Compute replacement status flags"""
        for product in self:
            product.is_replacement = bool(product.replaced_template_id)
            product.was_replaced = bool(product.replacement_template_id)
    
    @api.depends('replacement_template_id', 'replaced_template_id')
    def _compute_replacement_chain(self):
        """Compute the length of the replacement chain"""
        for product in self:
            count = 0
            current = product
            visited = set()
            
            # Count forward replacements
            while current.replacement_template_id and current.id not in visited:
                visited.add(current.id)
                count += 1
                current = current.replacement_template_id
                if count > 100:  # Safety limit
                    break
            
            # Count backward replacements
            current = product
            visited = set()
            while current.replaced_template_id and current.id not in visited:
                visited.add(current.id)
                count += 1
                current = current.replaced_template_id
                if count > 100:  # Safety limit
                    break
            
            product.replacement_chain_count = count
    
    # ========== METHODS ==========
    
    def get_current_replacement(self):
        """
        Get the current active replacement in the chain.
        Returns the latest active product in the replacement chain.
        """
        self.ensure_one()
        
        current = self
        visited = set()
        
        # Follow the replacement chain to the end
        while current.replacement_template_id and current.id not in visited:
            visited.add(current.id)
            current = current.replacement_template_id
            
            # Safety check
            if len(visited) > 100:
                _logger.warning(f"Replacement chain too long for product {self.name}")
                break
        
        return current
    
    def get_replacement_chain(self):
        """
        Get the complete replacement chain.
        Returns list of products from oldest to newest.
        """
        self.ensure_one()
        
        # Find the oldest product in chain
        oldest = self
        visited = set()
        while oldest.replaced_template_id and oldest.id not in visited:
            visited.add(oldest.id)
            oldest = oldest.replaced_template_id
            if len(visited) > 100:
                break
        
        # Build chain from oldest to newest
        chain = [oldest]
        visited = set([oldest.id])
        current = oldest
        
        while current.replacement_template_id and current.replacement_template_id.id not in visited:
            current = current.replacement_template_id
            chain.append(current)
            visited.add(current.id)
            if len(visited) > 100:
                break
        
        return chain
    
    def action_view_replacement(self):
        """Open the replacement product"""
        self.ensure_one()
        
        if not self.replacement_template_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Replacement Product',
            'res_model': 'product.template',
            'res_id': self.replacement_template_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_replaced_product(self):
        """Open the product that this replaces"""
        self.ensure_one()
        
        if not self.replaced_template_id:
            return False
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Original Product',
            'res_model': 'product.template',
            'res_id': self.replaced_template_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_replacement_chain(self):
        """View all products in the replacement chain"""
        self.ensure_one()
        
        chain = self.get_replacement_chain()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Replacement Chain',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [p.id for p in chain])],
            'context': {'search_default_order_by_replacement_date': 1}
        }