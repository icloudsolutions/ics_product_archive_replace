# -*- coding: utf-8 -*-
# __manifest__.py

{
    'name': 'Product Archive & Replace Enhanced',
    'version': '16.0.3.0.0',
    'summary': 'Archive products and replace with new type + PDF Audit Report',
    'description': """
Product Archive & Replace Enhanced
===================================

Features:
---------
* Archive products and create replacements with different type
* Mass migration by category or manual selection
* Migrate all references (Sales, Purchases, BOMs, Pricelists, Vendors)
* Transfer stock quantities automatically
* Preview products list before execution
* Generate PDF audit report for paper archive
* Detailed migration results with statistics
* Color-coded visual indicators

Perfect for:
-----------
* Changing product types (Storable → Service/Consumable)
* Mass product migrations
* Inventory reorganization
* Audit and compliance requirements

Version 3.0 Features:
--------------------
Product preview list with color codes
Professional PDF audit report
Detailed migration statistics
Complete traceability for audit

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