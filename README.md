# Product Archive & Replace Enhanced - v3.0

Archive products and create replacements with different type + PDF Audit Report

## 🎯 Features

### Core Functionality
- **Archive products** and create replacements with different product type
- **Mass migration** by category or manual selection
- **Migrate all references**:
  - Sales Order Lines
  - Purchase Order Lines
  - Bills of Materials (BOMs)
  - Pricelist Rules
  - Vendor Records
- **Transfer stock quantities** automatically
- **Complete audit trail** in chatter

### 🆕 Version 3.0 Features
- ✨ **Product preview list** with color-coded indicators
- 📄 **Professional PDF audit report** for paper archive
- 📊 **Detailed migration statistics**
- ✅ **Complete traceability** for audit and compliance
- 🎨 **Visual indicators** (stock, references)

## 📋 Requirements

- Odoo 16.0 (compatible with 17.x with minor adjustments)
- Modules:
  - `product` (required)
  - `stock` (required)
  - `sale_management` (required)
  - `purchase` (required)
  - `mrp` (optional - for BOM migration)

## 🚀 Installation

### 1. Copy Files

```bash
cd /path/to/odoo/addons/
git clone <this-repo> ics_product_archive_replace
# OR manually copy all files
```

### 2. Update Module List

In Odoo:
1. Go to **Apps**
2. Click **Update Apps List**
3. Search for "Product Archive Replace"
4. Click **Install**

### 3. Verify Installation

Check the menu: **Inventory > Configuration > Archive and Replace Products**

## 📖 Usage

### Scenario 1: Manual Selection

1. Go to **Inventory > Configuration > Archive and Replace Products**
2. Select **"Selected Products"** mode
3. Choose products to replace
4. Click **"📋 Show Products List"** to preview
5. Select new product type
6. Configure migration options
7. Click **"Archive and Replace"**
8. Click **"📄 Download PDF Audit Report"**

### Scenario 2: Category Selection

1. Select **"By Category"** mode
2. Choose categories (+ subcategories)
3. Optionally filter by current type
4. **Always preview** the list for mass operations
5. Execute and download report

## 📄 PDF Report Contents

The generated audit report includes:

1. **Executive Summary**
   - Migration date and user
   - Total products processed
   - Success/failure counts

2. **Migration Statistics**
   - Total sales lines migrated
   - Total purchase lines migrated
   - Total BOMs migrated
   - Total stock transferred

3. **Detailed Results Table**
   - Product-by-product breakdown
   - Type changes
   - Individual counts
   - Error messages for failures

4. **Migration Options Applied**
   - Which options were enabled

5. **Signature Section**
   - For approval and archiving

## 🎨 Visual Indicators

### Preview List Color Codes

| Color | Meaning | Action |
|-------|---------|--------|
| 🟠 **Orange** | Product has stock | Verify stock transfer |
| 🔵 **Blue** | Product has references | Migration needed |
| ⚪ **White** | Clean product | Simple migration |

## ⚠️ Important Notes

### Before Migration

1. **ALWAYS backup your database**
   ```bash
   pg_dump your_database > backup_$(date +%Y%m%d).sql
   ```

2. **Test on development first**

3. **Use the preview feature** for mass operations

### During Migration

4. Enable **"Continue on Error"** for mass migrations (50+ products)

5. Don't close the browser during execution

### After Migration

6. **Export PDF immediately** (wizard is transient)

7. Archive PDF with naming convention:
   ```
   MIGRATION_PRODUITS_YYYY-MM-DD_HH-MM.pdf
   ```

8. Verify a few products manually

## 🐛 Troubleshooting

### "No products to process"
All selected products already have the target type.

### "Failed to create new product"
Constraint violation (barcode/reference) - handled automatically.

### PDF not generating
Install wkhtmltopdf:
```bash
sudo apt-get install wkhtmltopdf
```

### Wizard stuck on "Loading..."
Too many products (500+). Reduce selection or wait 30-60 seconds.

## 📊 Performance

| Products | Time | Recommendation |
|----------|------|----------------|
| 1-10 | < 1 min | ✅ OK |
| 10-50 | 1-5 min | ✅ OK |
| 50-100 | 5-10 min | ⚠️ Wait |
| 100-500 | 10-30 min | ⚠️ Plan ahead |
| 500+ | 30+ min | ❌ Split into batches |

## 🔒 Security

**Required Group**: `stock.group_stock_manager`

## 📝 License

LGPL-3

## 👨‍💻 Support

For issues or questions, please contact your Odoo administrator.

## 🔄 Changelog

### v3.0.0 (2024)
- ✨ NEW: Product preview list with color codes
- ✨ NEW: Professional PDF audit report
- ✨ NEW: Detailed migration statistics
- ✨ NEW: Result storage and tracking
- 🔧 IMPROVED: User interface
- 🔧 IMPROVED: Error handling

### v2.1.0
- ✨ Category selection mode
- ✨ Type filtering
- 🔧 detailed_type field handling

### v2.0.0
- ✨ Complete reference migration
- ✨ Automatic stock transfer
- 🔧 Enhanced error handling

### v1.0.0
- 🎉 Initial release

---

**Made for Odoo 16.0** | **© 2025 iCloud Solutions**
