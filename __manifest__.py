# -*- coding: utf-8 -*-
{
    'name': 'Product Archive & Replace Enhanced',
    'version': '16.0.4.0.0',  # Updated version
    'summary': 'Archive products and replace with structured tracking + PDF Audit Report',
    'description': """
Product Archive & Replace Enhanced
===================================

Features:
---------
* Archive products and create replacements with different type
* **Structured replacement tracking with dedicated fields**
* Mass migration by category or manual selection
* Migrate all references (Sales, Purchases, BOMs, Pricelists, Vendors)
* Transfer stock quantities automatically
* Preview products list before execution
* Generate PDF audit report for paper archive
* Detailed migration results with statistics
* Color-coded visual indicators
* **Replacement chain visualization and tracking**

Perfect for:
-----------
* Changing product types (Storable → Service/Consumable)
* Mass product migrations
* Inventory reorganization
* Audit and compliance requirements

Version 4.0 Features (NEW):
---------------------------
* **Structured replacement links** using dedicated database fields
* **Auto-verification** of replacement integrity
* **Replacement chain tracking** with history
* **Enhanced validation** in receipt validation module
* **Reliable replacement detection** without parsing chatter
* Store original product type and replacement metadata
* Complete audit trail with timestamps and users

Technical Features:
------------------
* `replacement_template_id`: Links to replacement product
* `replaced_template_id`: Links to original product
* `replacement_date`: Timestamp of replacement
* `replacement_user_id`: User who executed replacement
* `original_type`: Product type before replacement
* Replacement chain navigation and visualization
* Automated validation in receipt operations

    """,
    'author': 'Nabil Jelassi',
    'website': 'https://icloud-solutions.net',
    'category': 'Inventory/Inventory',
    'depends': [
        'product',
        'stock',
        'sale_management',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',  # NEW
        'wizard/product_archive_replace_wizard_view.xml',
        'report/product_archive_replace_report.xml',
        'report/product_archive_replace_report_template.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
