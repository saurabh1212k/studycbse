"""
StudyOS - PDF Vault (Phase 6)
Upload and view static PDF files directly inside the app.
"""

import streamlit as st
import base64
from services.db import get_db

st.set_page_config(page_title="StudyOS | PDF Notes", page_icon="📁", layout="wide")

st.title("📁 PDF Notes Vault")
st.caption("Upload and organize your important custom PDF notes.")
st.divider()

db = get_db()

# 1. Upload Section
st.subheader("📤 Upload a new PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    if st.button("💾 Save PDF to Vault", type="primary"):
        with st.spinner("Uploading..."):
            try:
                # Read file as bytes
                file_bytes = uploaded_file.read()
                file_name = uploaded_file.name
                
                # Upload to Supabase Storage 'pdfs' bucket
                res = db.storage.from_("pdfs").upload(
                    file=file_bytes,
                    path=file_name,
                    file_options={"content-type": "application/pdf"}
                )
                
                st.success(f"Successfully uploaded {file_name}!")
                st.rerun()
            except Exception as e:
                # Supabase raises an error if the file already exists
                if "Duplicate" in str(e) or "already exists" in str(e).lower():
                    st.error(f"A file named '{file_name}' already exists in the vault.")
                else:
                    st.error(f"Error uploading file: {e}")

st.markdown("---")

# 2. View Section
st.subheader("📚 My PDF Notes")

try:
    # List files in the 'pdfs' bucket
    files = db.storage.from_("pdfs").list()
    
    # Filter out hidden/system files (like .emptyFolderPlaceholder)
    pdf_files = [f for f in files if f['name'].endswith('.pdf')]
    
    if not pdf_files:
        st.info("No PDFs uploaded yet. Upload one above!")
    else:
        # Create a dropdown to select a PDF
        file_names = [f['name'] for f in pdf_files]
        selected_pdf = st.selectbox("Select a PDF to view:", file_names)
        
        if selected_pdf:
            st.markdown(f"**Viewing:** `{selected_pdf}`")
            
            # Download the file bytes to display it
            pdf_bytes = db.storage.from_("pdfs").download(selected_pdf)
            
            # Embed PDF using base64 and HTML iframe
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            # Provide a delete button
            if st.button("🗑️ Delete this PDF"):
                db.storage.from_("pdfs").remove([selected_pdf])
                st.warning(f"Deleted {selected_pdf}.")
                st.rerun()

except Exception as e:
    st.error(f"Could not load PDFs. Did you create the 'pdfs' bucket in Supabase and make it Public? Error: {e}")
