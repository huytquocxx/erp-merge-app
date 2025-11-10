"""
ERP Master Data Merger (S4 vs ECC)
Streamlit web app for merging SAP S/4HANA and ECC country master data files.
"""

import streamlit as st
import pandas as pd
import requests
import io
from typing import Tuple, Dict, Any, List, Optional
import openpyxl

# Page configuration
st.set_page_config(
    page_title="ERP Master Data Merger",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def convert_google_sheets_url(url: str) -> str:
    """Convert Google Sheets edit URL to export URL."""
    # Pattern: https://docs.google.com/spreadsheets/d/{FILE_ID}/edit...
    if 'docs.google.com/spreadsheets' in url and '/edit' in url:
        # Extract file ID
        file_id = None
        if '/d/' in url:
            parts = url.split('/d/')
            if len(parts) > 1:
                file_id = parts[1].split('/')[0].split('?')[0]
        
        if file_id:
            # Convert to export format (xlsx)
            export_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx&id={file_id}"
            return export_url
    
    return url


def load_excel_from_url(url: str) -> pd.DataFrame:
    """Load Excel file from URL (supports Google Sheets)."""
    try:
        # Convert Google Sheets URL if needed
        export_url = convert_google_sheets_url(url)
        
        # Set headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(export_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Check if response is actually an Excel file
        content_type = response.headers.get('content-type', '').lower()
        if 'html' in content_type or response.content[:2] == b'<!':
            raise ValueError("URL returned HTML instead of Excel file. Make sure the file is publicly accessible or use the export link.")
        
        return pd.read_excel(
            io.BytesIO(response.content),
            engine='openpyxl',
            dtype=str,
            keep_default_na=False
        )
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching file from URL: {str(e)}")
        raise
    except Exception as e:
        st.error(f"Error reading Excel file from URL: {str(e)}")
        raise


def load_excel_from_upload(uploaded_file) -> pd.DataFrame:
    """Load Excel file from Streamlit upload."""
    try:
        return pd.read_excel(
            uploaded_file,
            engine='openpyxl',
            dtype=str,
            keep_default_na=False
        )
    except Exception as e:
        st.error(f"Error reading uploaded Excel file: {str(e)}")
        raise


def normalize_key(key: str) -> str:
    """Normalize key for case-insensitive matching."""
    if pd.isna(key):
        return ""
    return str(key).strip().upper()


def create_composite_key(row: pd.Series, key_fields: list) -> str:
    """Create a composite normalized key from multiple fields."""
    key_parts = []
    for field in key_fields:
        if field in row:
            normalized = normalize_key(row[field])
            key_parts.append(normalized)
        else:
            key_parts.append("")
    return "|".join(key_parts)  # Use pipe separator for composite keys


def generate_mdg_key(row: pd.Series, key_fields: list) -> str:
    """Generate MDGKey based on all key fields (format: key1-key2-key3...)."""
    if not key_fields:
        return ""
    
    key_parts = []
    for field in key_fields:
        if field in row:
            normalized = normalize_key(row[field])
            if normalized:  # Only add non-empty normalized values
                key_parts.append(normalized)
    
    # Join all key parts with hyphens
    return "-".join(key_parts) if key_parts else ""


def validate_dataframe(df: pd.DataFrame, source_name: str, required_columns: list = None) -> Tuple[bool, str]:
    """Validate DataFrame structure."""
    if df.empty:
        return False, f"{source_name} file is empty."
    
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return False, f"{source_name} is missing required columns: {', '.join(missing_cols)}"
    
    return True, "OK"


def merge_erp_data(s4_df: pd.DataFrame, ecc_df: pd.DataFrame, 
                   key_fields: Optional[List[str]] = None,
                   column_prefix: str = 'ERP') -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Merge S4 and ECC ERP master data.
    
    Args:
        s4_df: S4 master data DataFrame
        ecc_df: ECC master data DataFrame
        key_fields: List of key fields for matching (required)
    
    Returns:
        md_table: Unique records with S4 priority
        md_mapping: All records (S4 + ECC)
        validation_summary: Dictionary with validation metrics
    """
    # Validate inputs
    if s4_df.empty and ecc_df.empty:
        raise ValueError("Both S4 and ECC dataframes are empty.")
    
    if not key_fields:
        raise ValueError("At least one key field must be specified.")
    
    # Validate that key fields exist in at least one dataset
    s4_cols = set(s4_df.columns) if not s4_df.empty else set()
    ecc_cols = set(ecc_df.columns) if not ecc_df.empty else set()
    all_cols = s4_cols | ecc_cols
    
    missing_fields = [field for field in key_fields if field not in all_cols]
    if missing_fields:
        raise ValueError(f"Key field(s) not found in either dataset: {', '.join(missing_fields)}")
    
    # Create normalized key columns for matching
    s4_df = s4_df.copy()
    ecc_df = ecc_df.copy()
    
    # Create composite normalized key from multiple fields
    s4_df['_normalized_key'] = s4_df.apply(lambda row: create_composite_key(row, key_fields), axis=1)
    ecc_df['_normalized_key'] = ecc_df.apply(lambda row: create_composite_key(row, key_fields), axis=1)
    
    # Generate MDGKey (using first key field)
    s4_df['MDGKey'] = s4_df.apply(lambda row: generate_mdg_key(row, key_fields), axis=1)
    ecc_df['MDGKey'] = ecc_df.apply(lambda row: generate_mdg_key(row, key_fields), axis=1)
    
    # Add source identifier
    s4_df['_source'] = 'S4'
    ecc_df['_source'] = 'ECC'
    
    # Get unique keys from both sources
    s4_keys = set(s4_df['_normalized_key'].dropna())
    ecc_keys = set(ecc_df['_normalized_key'].dropna())
    
    # Find overlaps and unique keys
    overlapping_keys = s4_keys & ecc_keys
    s4_only_keys = s4_keys - ecc_keys
    ecc_only_keys = ecc_keys - s4_keys
    
    # Build MDtable: S4 priority (S4 records + ECC-only records)
    md_table_parts = []
    
    # Add all S4 records
    md_table_parts.append(s4_df.copy())
    
    # Add ECC-only records
    ecc_only_df = ecc_df[ecc_df['_normalized_key'].isin(ecc_only_keys)].copy()
    if not ecc_only_df.empty:
        md_table_parts.append(ecc_only_df)
    
    # Combine and remove duplicates (S4 has priority)
    if md_table_parts:
        md_table = pd.concat(md_table_parts, ignore_index=True)
        # Remove duplicates based on normalized key, keeping first occurrence (S4 first)
        md_table = md_table.drop_duplicates(subset=['_normalized_key'], keep='first')
    else:
        md_table = pd.DataFrame()
    
    # Build MDmapping: include all columns from both sources with prefix
    helper_columns = {'_normalized_key', '_source', 'MDGKey'}
    all_source_columns = set()
    if not s4_df.empty:
        all_source_columns.update(s4_df.columns)
    if not ecc_df.empty:
        all_source_columns.update(ecc_df.columns)

    data_columns = sorted([col for col in all_source_columns if col not in helper_columns])
    prefixed_columns = [f"{column_prefix}{col}" for col in data_columns]

    md_mapping_records = []

    def build_record(row: pd.Series, system: str) -> Dict[str, Any]:
        record = {
            'MDGKey': row.get('MDGKey', ''),
            'ERPSystem': system
        }
        for col, prefixed in zip(data_columns, prefixed_columns):
            value = row.get(col, '')
            if pd.isna(value):
                value = ''
            record[prefixed] = value
        return record

    if not s4_df.empty:
        for _, row in s4_df.iterrows():
            md_mapping_records.append(build_record(row, 'S4'))

    if not ecc_df.empty:
        for _, row in ecc_df.iterrows():
            md_mapping_records.append(build_record(row, 'ECC'))

    if md_mapping_records:
        md_mapping = pd.DataFrame(md_mapping_records)
        md_mapping = md_mapping[['MDGKey', 'ERPSystem'] + prefixed_columns]
    else:
        md_mapping = pd.DataFrame(columns=['MDGKey', 'ERPSystem'] + prefixed_columns)
 
    # Clean up temporary columns from md_table only
    if not md_table.empty:
        if '_normalized_key' in md_table.columns:
            md_table.drop(columns=['_normalized_key'], inplace=True)
        if '_source' in md_table.columns:
            md_table.drop(columns=['_source'], inplace=True)
        # Ensure MDGKey is the first column
        if 'MDGKey' in md_table.columns:
            remaining_cols = [c for c in md_table.columns if c != 'MDGKey']
            md_table = md_table[['MDGKey'] + remaining_cols]
    
    # Build validation summary
    validation_summary = {
        's4_count': len(s4_df),
        'ecc_count': len(ecc_df),
        'mdtable_count': len(md_table),
        'mdmapping_count': len(md_mapping),
        'overlapping_key_count': len(overlapping_keys),
        's4_only_key_count': len(s4_only_keys),
        'ecc_only_key_count': len(ecc_only_keys),
        'overlapping_keys_list': sorted(list(overlapping_keys)),
        's4_only_keys_list': sorted(list(s4_only_keys)),
        'ecc_only_keys_list': sorted(list(ecc_only_keys)),
        'key_fields_used': key_fields,
        'mdmapping_columns': ['MDGKey', 'ERPSystem'] + prefixed_columns
    }
    
    return md_table, md_mapping, validation_summary


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    return output.getvalue()


# Main App
def main():
    st.markdown('<div class="main-header">📊 ERP Master Data Merger (S4 vs ECC)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload or link your SAP S/4HANA and ECC master data files to generate consolidated outputs.</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'md_table' not in st.session_state:
        st.session_state.md_table = None
    if 'md_mapping' not in st.session_state:
        st.session_state.md_mapping = None
    if 'validation_summary' not in st.session_state:
        st.session_state.validation_summary = None
    if 'key_fields' not in st.session_state:
        st.session_state.key_fields = []
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Section",
            ["📤 Upload/URL Input", "👁️ Preview Data", "⚙️ Run Merge", "📥 Results & Downloads"]
        )
    
    # Page 1: Upload/URL Input
    if page == "📤 Upload/URL Input":
        st.header("📤 Data Input")
        
        upload_option = st.radio(
            "How would you like to provide data?",
            ["Upload files", "Provide URLs"],
            horizontal=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("S4 Master Data")
            if upload_option == "Upload files":
                s4_file = st.file_uploader(
                    "Upload S4 dataset (Excel)",
                    type=["xlsx", "xls"],
                    key="s4_upload"
                )
                s4_url = None
            else:
                s4_url = st.text_input(
                    "S4 file URL",
                    key="s4_url",
                    placeholder="https://docs.google.com/spreadsheets/d/... or direct file URL"
                )
                s4_file = None
                st.caption("💡 Supports Google Sheets links (will auto-convert) and direct Excel file URLs")
        
        with col2:
            st.subheader("ECC Master Data")
            if upload_option == "Upload files":
                ecc_file = st.file_uploader(
                    "Upload ECC dataset (Excel)",
                    type=["xlsx", "xls"],
                    key="ecc_upload"
                )
                ecc_url = None
            else:
                ecc_url = st.text_input(
                    "ECC file URL",
                    key="ecc_url",
                    placeholder="https://docs.google.com/spreadsheets/d/... or direct file URL"
                )
                ecc_file = None
                st.caption("💡 Supports Google Sheets links (will auto-convert) and direct Excel file URLs")
        
        # Load and validate data
        s4_df = None
        ecc_df = None
        
        if upload_option == "Upload files":
            if s4_file is not None:
                try:
                    s4_df = load_excel_from_upload(s4_file)
                    st.success(f"✅ S4 file loaded: {len(s4_df)} rows, {len(s4_df.columns)} columns")
                except Exception as e:
                    st.error(f"❌ Error loading S4 file: {str(e)}")
            
            if ecc_file is not None:
                try:
                    ecc_df = load_excel_from_upload(ecc_file)
                    st.success(f"✅ ECC file loaded: {len(ecc_df)} rows, {len(ecc_df.columns)} columns")
                except Exception as e:
                    st.error(f"❌ Error loading ECC file: {str(e)}")
        else:
            # Show Google Sheets help
            if 'docs.google.com' in (s4_url or '') or 'docs.google.com' in (ecc_url or ''):
                st.info("📝 **Google Sheets Note:** Make sure your Google Sheet is set to 'Anyone with the link can view' for the URL to work. The app will automatically convert the edit link to an export format.")
            
            if s4_url:
                try:
                    with st.spinner("Loading S4 file from URL..."):
                        s4_df = load_excel_from_url(s4_url)
                        st.success(f"✅ S4 file loaded: {len(s4_df)} rows, {len(s4_df.columns)} columns")
                except Exception as e:
                    error_msg = str(e)
                    if 'html' in error_msg.lower() or 'not a zip file' in error_msg.lower():
                        st.error(f"❌ Error loading S4 file from URL: {error_msg}")
                        st.warning("💡 **Troubleshooting:** If using Google Sheets, ensure the file is publicly accessible (set sharing to 'Anyone with the link can view'). Alternatively, download the file as Excel and upload it directly.")
                    else:
                        st.error(f"❌ Error loading S4 file from URL: {error_msg}")
            
            if ecc_url:
                try:
                    with st.spinner("Loading ECC file from URL..."):
                        ecc_df = load_excel_from_url(ecc_url)
                        st.success(f"✅ ECC file loaded: {len(ecc_df)} rows, {len(ecc_df.columns)} columns")
                except Exception as e:
                    error_msg = str(e)
                    if 'html' in error_msg.lower() or 'not a zip file' in error_msg.lower():
                        st.error(f"❌ Error loading ECC file from URL: {error_msg}")
                        st.warning("💡 **Troubleshooting:** If using Google Sheets, ensure the file is publicly accessible (set sharing to 'Anyone with the link can view'). Alternatively, download the file as Excel and upload it directly.")
                    else:
                        st.error(f"❌ Error loading ECC file from URL: {error_msg}")
        
        # Store in session state
        if s4_df is not None:
            st.session_state.s4_df = s4_df
        if ecc_df is not None:
            st.session_state.ecc_df = ecc_df
        
        # Show data preview if available
        if s4_df is not None or ecc_df is not None:
            st.subheader("Quick Preview")
            preview_col1, preview_col2 = st.columns(2)
            
            with preview_col1:
                if s4_df is not None:
                    st.write("**S4 Data Preview**")
                    st.dataframe(s4_df.head(5), use_container_width=True)
            
            with preview_col2:
                if ecc_df is not None:
                    st.write("**ECC Data Preview**")
                    st.dataframe(ecc_df.head(5), use_container_width=True)
    
    # Page 2: Preview Data
    elif page == "👁️ Preview Data":
        st.header("👁️ Data Preview")
        
        if 's4_df' not in st.session_state and 'ecc_df' not in st.session_state:
            st.warning("⚠️ Please load data files first in the 'Upload/URL Input' section.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 's4_df' in st.session_state:
                st.subheader("S4 Master Data")
                s4_df = st.session_state.s4_df
                st.write(f"**Rows:** {len(s4_df)} | **Columns:** {len(s4_df.columns)}")
                st.dataframe(s4_df, use_container_width=True, height=400)
                
                st.write("**Column Names:**")
                st.write(list(s4_df.columns))
            else:
                st.info("S4 data not loaded yet.")
        
        with col2:
            if 'ecc_df' in st.session_state:
                st.subheader("ECC Master Data")
                ecc_df = st.session_state.ecc_df
                st.write(f"**Rows:** {len(ecc_df)} | **Columns:** {len(ecc_df.columns)}")
                st.dataframe(ecc_df, use_container_width=True, height=400)
                
                st.write("**Column Names:**")
                st.write(list(ecc_df.columns))
            else:
                st.info("ECC data not loaded yet.")
    
    # Page 3: Run Merge
    elif page == "⚙️ Run Merge":
        st.header("⚙️ Run Merge Process")
        
        if 's4_df' not in st.session_state or 'ecc_df' not in st.session_state:
            st.error("❌ Please load both S4 and ECC data files first in the 'Upload/URL Input' section.")
            return
        
        s4_df = st.session_state.s4_df
        ecc_df = st.session_state.ecc_df
        
        # Key Fields Configuration - Make it very prominent
        st.markdown("---")
        st.subheader("🔑 **Key Fields Configuration** (Required)")
        st.markdown("**Select one or more columns to use as key fields for matching records between S4 and ECC data.**")
        st.info("💡 Key fields are used to identify matching records. Records with the same key field values will be considered duplicates (S4 takes priority).")
        
        # Get available columns from both datasets
        s4_cols = list(s4_df.columns) if not s4_df.empty else []
        ecc_cols = list(ecc_df.columns) if not ecc_df.empty else []
        all_available_cols = sorted(list(set(s4_cols + ecc_cols)))
        
        if not all_available_cols:
            st.error("❌ No columns available in the loaded datasets.")
            st.stop()
        
        # Show available columns
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Available Columns in S4:**")
            st.write(s4_cols if s4_cols else "None")
        with col2:
            st.write("**Available Columns in ECC:**")
            st.write(ecc_cols if ecc_cols else "None")
        
        # Multi-select for key fields - Make it very visible
        existing_selection = st.session_state.get('key_field_selector', st.session_state.get('key_fields', []))
        existing_selection = [kf for kf in existing_selection if kf in all_available_cols]
        if not existing_selection and all_available_cols:
            existing_selection = [all_available_cols[0]]

        st.markdown("#### **Select Key Fields:**")
        selected_key_fields = st.multiselect(
            "Choose columns to use for matching records (you can select multiple):",
            options=all_available_cols,
            default=existing_selection,
            help="Select one or more columns that uniquely identify records. Records will be matched based on these fields (case-insensitive).",
            label_visibility="collapsed",
            key="key_field_selector"
        )

        # Store selected key fields in session state
        st.session_state.key_fields = selected_key_fields

        if selected_key_fields:
            st.success(f"✅ **Selected Key Fields:** {', '.join(selected_key_fields)}")
        else:
            st.error("⚠️ **Please select at least one key field to proceed.**")
            st.stop()
        
        st.markdown("---")
        st.info("ℹ️ MDmapping output will include every column from your source files with an `ERP` prefix (e.g., `ERPDivision`), alongside `MDGKey` and `ERPSystem`.")
        st.markdown("---")
        
        # Validation
        st.subheader("Data Validation")
        
        s4_valid, s4_msg = validate_dataframe(s4_df, "S4", selected_key_fields)
        ecc_valid, ecc_msg = validate_dataframe(ecc_df, "ECC", selected_key_fields)
        
        if not s4_valid:
            st.error(f"❌ {s4_msg}")
        else:
            st.success(f"✅ {s4_msg}")
        
        if not ecc_valid:
            st.error(f"❌ {ecc_msg}")
        else:
            st.success(f"✅ {ecc_msg}")
        
        if not (s4_valid and ecc_valid):
            st.stop()
        
        # Merge button
        st.subheader("Execute Merge")
        
        if st.button("🚀 Run Merge Process", type="primary", use_container_width=True):
            with st.spinner("Processing merge..."):
                try:
                    md_table, md_mapping, validation_summary = merge_erp_data(
                        s4_df, ecc_df, selected_key_fields
                    )
                    
                    # Store results in session state
                    st.session_state.md_table = md_table
                    st.session_state.md_mapping = md_mapping
                    st.session_state.validation_summary = validation_summary
                    
                    st.success("✅ Merge completed successfully!")
                    
                    # Display summary
                    st.subheader("Merge Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("S4 Records", validation_summary['s4_count'])
                    with col2:
                        st.metric("ECC Records", validation_summary['ecc_count'])
                    with col3:
                        st.metric("MDtable Rows", validation_summary['mdtable_count'])
                    with col4:
                        st.metric("MDmapping Rows", validation_summary['mdmapping_count'])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Matching Keys", validation_summary['overlapping_key_count'])
                    with col2:
                        st.metric("S4-Only Keys", validation_summary['s4_only_key_count'])
                    with col3:
                        st.metric("ECC-Only Keys", validation_summary['ecc_only_key_count'])
                    
                    # Show overlapping keys
                    if validation_summary['overlapping_keys_list']:
                        with st.expander("📋 View Matching Keys"):
                            st.write(validation_summary['overlapping_keys_list'])
                    
                    # Show S4-only keys
                    if validation_summary['s4_only_keys_list']:
                        with st.expander("📋 View S4-Only Keys"):
                            st.write(validation_summary['s4_only_keys_list'])
                    
                    # Show ECC-only keys
                    if validation_summary['ecc_only_keys_list']:
                        with st.expander("📋 View ECC-Only Keys"):
                            st.write(validation_summary['ecc_only_keys_list'])
                    
                except Exception as e:
                    st.error(f"❌ Error during merge: {str(e)}")
                    st.exception(e)
    
    # Page 4: Results & Downloads
    elif page == "📥 Results & Downloads":
        st.header("📥 Results & Downloads")
        
        if st.session_state.md_table is None or st.session_state.md_mapping is None:
            st.warning("⚠️ Please run the merge process first in the 'Run Merge' section.")
            return
        
        md_table = st.session_state.md_table
        md_mapping = st.session_state.md_mapping
        validation_summary = st.session_state.validation_summary
        
        # Display results
        st.subheader("Merged Data Preview")
        
        tab1, tab2 = st.tabs(["MDtable (Unique Records)", "MDmapping (All Records)"])
        
        with tab1:
            st.write(f"**Total Rows:** {len(md_table)}")
            st.dataframe(md_table, use_container_width=True, height=400)
            st.caption(f"Columns: {', '.join(md_table.columns.astype(str))}")
 
        with tab2:
            st.write(f"**Total Rows:** {len(md_mapping)}")
            st.dataframe(md_mapping, use_container_width=True, height=400)
            mapping_columns = validation_summary.get('mdmapping_columns', list(md_mapping.columns))
            st.caption(f"Columns: {', '.join(mapping_columns)}")
        
        # Download section
        st.subheader("📥 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                mdtable_bytes = dataframe_to_excel_bytes(md_table)
                st.download_button(
                    label="📥 Download MDtable.xlsx",
                    data=mdtable_bytes,
                    file_name="MDtable.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating MDtable download: {str(e)}")
        
        with col2:
            try:
                mdmapping_bytes = dataframe_to_excel_bytes(md_mapping)
                st.download_button(
                    label="📥 Download MDmapping.xlsx",
                    data=mdmapping_bytes,
                    file_name="MDmapping.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating MDmapping download: {str(e)}")
        
        # Validation summary
        if validation_summary:
            st.subheader("📊 Data Quality Summary")
            
            key_fields_str = ', '.join(validation_summary.get('key_fields_used', ['N/A']))
            summary_text = f"""
**Key Fields Used:**
- {key_fields_str}

**Source Data:**
- S4 Records: {validation_summary['s4_count']}
- ECC Records: {validation_summary['ecc_count']}

**Output Data:**
- MDtable Records: {validation_summary['mdtable_count']}
- MDmapping Records: {validation_summary['mdmapping_count']}

**Key Analysis:**
- Matching Keys: {validation_summary['overlapping_key_count']}
- S4-Only Keys: {validation_summary['s4_only_key_count']}
- ECC-Only Keys: {validation_summary['ecc_only_key_count']}
"""
            st.code(summary_text, language="text")


if __name__ == "__main__":
    main()
