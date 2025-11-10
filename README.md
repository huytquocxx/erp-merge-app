# ERP Master Data Merger (S4 vs ECC)

A Streamlit web application for merging SAP S/4HANA and ECC country master data files.

## Features

- 📤 Upload Excel files or provide Google Sheets URLs
- 🔑 Configurable key fields for matching records
- 🔄 Automatic merge with S4 priority
- 📊 Generate MDtable (unique records) and MDmapping (all records)
- 📥 Download results as Excel files

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app:**
   ```bash
   streamlit run erp_merge_app.py
   ```

3. **Open in browser:**
   The app will open at `http://localhost:8501`

## Project Structure

```
ERP_Merge/
├── erp_merge_app.py      # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Requirements

- Python 3.8+
- streamlit >= 1.28.0
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- requests >= 2.31.0

## Usage

1. **Upload/URL Input:** Load your S4 and ECC Excel files
2. **Preview Data:** Review the loaded data
3. **Run Merge:** 
   - Select key fields for matching
   - Review the MDmapping column preview
   - Execute merge
4. **Results & Downloads:** View results and download Excel files

## Output Files

- **MDtable.xlsx:** Unique records with S4 priority
- **MDmapping.xlsx:** All records with every source column (largest schema) prefixed with `ERP` (e.g., `ERPDivision`), plus:
  - `MDGKey`
  - `ERPSystem` (S4 or ECC)

## License

MIT

