import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io
from datetime import date
import os
import matplotlib.pyplot as plt
from PIL import Image # <--- இந்த புதிய வரியைச் சேர்த்துள்ளேன்

# --- Configuration ---
DATA_FILE = "customer_data.csv"

# --- Data Handling Functions ---
def load_data():
    """Loads customer data from the CSV file."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, dtype={'Date': str})
    else:
        columns = ["Date", "Customer Name", "Contact Number", "Product", "Weight (grams)", "Reason for Feedback"]
        return pd.DataFrame(columns=columns)

# --- Charting Function ---
def create_reason_chart(df):
    """Creates a horizontal bar chart of feedback reasons and returns it as an in-memory image."""
    if df.empty or 'Reason for Feedback' not in df.columns:
        return None
    reason_counts = df['Reason for Feedback'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    reason_counts.sort_values().plot(kind='barh', ax=ax, color='skyblue')
    ax.set_title('Summary of Customer Feedback Reasons', fontsize=14)
    ax.set_xlabel('Number of Customers', fontsize=10)
    ax.set_ylabel('Reason', fontsize=10)
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    plt.close(fig)
    return buf

# --- PDF Generation Function ---
def create_report_pdf(report_df, chart_image=None):
    """Creates a PDF report, optionally including a chart on the first page."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setTitle("Customer Feedback Report")
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2.0, height - 0.75 * inch, "Customer Feedback Report")
    y_position = height - 1.0 * inch

    if chart_image:
        # ---- இந்த இடத்தில் மாற்றம் செய்யப்பட்டுள்ளது ----
        # Pillow-ஐப் பயன்படுத்தி படத்தைத் திறக்கிறோம்
        pil_image = Image.open(chart_image)
        # இப்போது Pillow படப் பொருளை PDF-ல் வரைகிறோம்
        c.drawInlineImage(pil_image, 1 * inch, y_position - 3.5 * inch, width=6.5 * inch, height=3.25 * inch)
        y_position -= 4.0 * inch
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, y_position, "Detailed Entries:")
    y_position -= 0.25 * inch

    for index, row in report_df.iterrows():
        if y_position < 1.5 * inch:
            c.showPage()
            y_position = height - 1.0 * inch
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1 * inch, y_position, "Detailed Entries (Continued)")
            y_position -= 0.25 * inch

        c.setFont("Helvetica", 10)
        line_height = 0.20 * inch
        
        c.drawString(1.2 * inch, y_position, f"Date: {row['Date']} | Name: {row['Customer Name']} | Contact: {row.get('Contact Number', 'N/A')}")
        y_position -= line_height
        c.drawString(1.2 * inch, y_position, f"Product: {row['Product']} | Weight: {row['Weight (grams)']}g | Reason: {row['Reason for Feedback']}")
        
        y_position -= (line_height / 2)
        c.line(1.1 * inch, y_position, width - 1.1 * inch, y_position)
        y_position -= 0.25 * inch
        
    c.save()
    buffer.seek(0)
    return buffer

# --- Streamlit Web App Interface (No changes below this line) ---
st.set_page_config(page_title="Customer Feedback System", layout="wide")
st.title("Customer Feedback System")

df = load_data()

st.header("1. Save New Customer Entry")
with st.form("entry_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        form_date = st.date_input("Date", value=date.today())
        form_name = st.text_input("Name", placeholder="Enter customer's name")
        form_contact = st.text_input("Contact", placeholder="Enter contact number")
    with col2:
        form_product = st.selectbox("Product", ["", "Bangle", "Ring", "Chain", "Earring", "Necklace", "Bracelet", "Other"])
        form_weight = st.number_input("Weight (grams)", min_value=0.0, format="%.3f")
        form_reason = st.selectbox("Reason", ["", "VA Problem", "Model Problem", "Selection Issue", "Staff Issue", "Live Shopping", "JPS Card"])
    
    if st.form_submit_button("Save Entry"):
        if not form_name or not form_product or not form_reason:
            st.warning("Please fill in Name, Product, and Reason.")
        else:
            new_entry = pd.DataFrame([{"Date": form_date.strftime("%Y-%m-%d"), "Customer Name": form_name, "Contact Number": form_contact, "Product": form_product, "Weight (grams)": f"{form_weight:.3f}", "Reason for Feedback": form_reason}])
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"✅ Entry for '{form_name}' saved successfully!")

st.divider()

st.header("2. Generate PDF Report")
if df.empty:
    st.info("No data has been saved yet.")
else:
    df['Date'] = pd.to_datetime(df['Date'])
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", df['Date'].min().date())
    with col2:
        end_date = st.date_input("End Date", date.today())
    
    include_chart = st.checkbox("Create Bar Chart in PDF")

    if st.button("Generate PDF Report"):
        if start_date > end_date:
            st.error("Error: Start Date cannot be after End Date.")
        else:
            mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
            filtered_df = df.loc[mask]

            if filtered_df.empty:
                st.warning("No entries found for the selected date range.")
            else:
                chart_image_buffer = None
                if include_chart:
                    chart_image_buffer = create_reason_chart(filtered_df)

                pdf_buffer = create_report_pdf(filtered_df, chart_image=chart_image_buffer)
                
                st.success(f"✅ PDF report generated with {len(filtered_df)} entries!")
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_buffer,
                    file_name=f"Report_{start_date}_to_{end_date}.pdf",
                    mime="application/pdf"
                )

st.divider()
if st.checkbox("Show All Saved Data"):
    if df.empty:
        st.info("No data to display.")
    else:
        st.dataframe(df.astype(str))