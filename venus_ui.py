import streamlit as st
import gspread
from google import genai 
import json
import urllib.parse
import datetime
from fpdf import FPDF # 👈 PDF બનાવવા માટેનું નવું એન્જિન

# ==========================================
# ૧. પેજનું સેટિંગ
# ==========================================
st.set_page_config(page_title="Venus Surgical AI", page_icon="🏥", layout="wide")
st.title("🏥 Venus Surgical - AI સેલ્સ મેનેજર (Google Sheets 🟢)")
st.write("હવે તમારો સ્ટોક સીધો ગૂગલ શીટ સાથે જોડાયેલો છે!")

# ==========================================
# ૨. Google Sheets સાથે જોડાણ
# ==========================================
try:
    cred_dict = json.loads(st.secrets["GCP_CREDS"])
    gc = gspread.service_account_from_dict(cred_dict)
    sheet = gc.open("Venus_Stock").sheet1
except Exception as e:
    st.error(f"ગૂગલ શીટ સાથે જોડાઈ શકાયું નથી. ભૂલ: {e}")
    st.stop()

# ==========================================
# ૩. ગૂગલ શીટમાંથી સ્ટોક લાવવાનું ફંક્શન
# ==========================================
@st.cache_data(ttl=60)
def get_current_stock():
    records = sheet.get_all_records()
    stock_info = ""
    for row in records:
        stock_info += f"{row['Product_Name']}: {row['Stock']} નંગ, "
    return stock_info

st.sidebar.header("📦 લાઈવ ગૂગલ ગોડાઉન સ્ટોક")
try:
    current_stock = get_current_stock()
    st.sidebar.success(current_stock)
except Exception as e:
    current_stock = "સ્ટોક લોડ થઈ શક્યો નથી."
    st.sidebar.warning(current_stock)

# ==========================================
# ૪. નવો સ્ટોક અપડેટ કરવાનું સેટિંગ (Sidebar)
# ==========================================
st.sidebar.markdown("---") 
st.sidebar.header("🔄 નવો સ્ટોક અપડેટ કરો")

update_item = st.sidebar.text_input("પ્રોડક્ટનું નામ (ગૂગલ શીટ મુજબ સ્પેલિંગ):")
update_qty = st.sidebar.number_input("નવો સ્ટોક (નંગ):", min_value=0, step=1)

if st.sidebar.button("સ્ટોક અપડેટ કરો"):
    if update_item == "":
        st.sidebar.warning("પ્રોડક્ટનું નામ લખો!")
    else:
        try:
            cell = sheet.find(update_item)
            sheet.update_cell(cell.row, 2, update_qty)
            st.sidebar.success(f"✅ {update_item} નો નવો સ્ટોક અપડેટ થઈ ગયો!")
            get_current_stock.clear()
            st.rerun()
        except gspread.exceptions.CellNotFound:
            st.sidebar.error("આ નામની પ્રોડક્ટ ગૂગલ શીટમાં મળી નથી.")

# ==========================================
# ૫. બે મુખ્ય ભાગ માટે 'Tabs' બનાવ્યા 🟢
# ==========================================
tab1, tab2 = st.tabs(["🤖 AI સેલ્સ મેનેજર (WhatsApp)", "📄 PDF ક્વોટેશન બનાવો"])

# ------------------------------------------
# TAB 1: તમારો જૂનો AI અને WhatsApp વાળો ભાગ
# ------------------------------------------
with tab1:
    my_api_key = st.secrets["GEMINI_API_KEY"]
    customer_message = st.text_area("ગ્રાહકનો મેસેજ અહી પેસ્ટ કરો:", placeholder="ઉદાહરણ: મારે 500 Surgical Gown જોઈએ છે...")

    if "ai_reply" not in st.session_state:
        st.session_state.ai_reply = ""

    if st.button("🤖 AI પાસે જવાબ લખાવો", type="primary", key="ai_btn"):
        if customer_message == "":
            st.warning("કૃપા કરીને પહેલા ગ્રાહકનો મેસેજ લખો!")
        else:
            with st.spinner("AI મેનેજર જવાબ ટાઈપ કરી રહ્યો છે..."):
                try:
                    client = genai.Client(api_key=my_api_key)
                    prompt = f"""
                    તું 'Venus Surgical' કંપનીનો બહુ જ સ્માર્ટ અને નમ્ર સેલ્સ મેનેજર છે.
                    તારી પાસે ગોડાઉનનો આ લેટેસ્ટ સ્ટોક છે: {current_stock}
                    એક ગ્રાહકનો મેસેજ આવ્યો છે: "{customer_message}"
                    આ ગ્રાહકને પ્રોફેશનલ ગુજરાતીમાં જવાબ લખ.
                    """
                    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    st.session_state.ai_reply = response.text 
                except Exception as e:
                    st.error(f"ભૂલ: {e}")

    if st.session_state.ai_reply != "":
        st.success("✅ જવાબ તૈયાર છે!")
        st.write(st.session_state.ai_reply)
        st.markdown("### 🟢 આ જવાબ સીધો WhatsApp પર મોકલો")
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            phone_number = st.text_input("ગ્રાહકનો 10 આંકડાનો WhatsApp નંબર લખો:")
        with col_b:
            st.write("")
            st.write("")
            if phone_number != "" and len(phone_number.strip()) >= 10:
                clean_num = "91" + phone_number.strip()
                encoded_msg = urllib.parse.quote(st.session_state.ai_reply)
                whatsapp_link = f"https://wa.me/{clean_num}?text={encoded_msg}"
                st.link_button("💬 WhatsApp ઓપન કરો", whatsapp_link, type="primary")
            else:
                st.button("💬 WhatsApp ઓપન કરો", disabled=True)

# ------------------------------------------
# TAB 2: નવું 'PDF Quotation Generator' 🚀
# ------------------------------------------
# બેકગ્રાઉન્ડમાં PDF છાપવાનું મશીન (Function)
def create_quotation_pdf(cust_name, items, gst_rate):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    
    DARK_BLUE = (26, 54, 93) # કેટલોગનો ઓફિશિયલ કલર
    GREY = (100, 100, 100)
    
    # 1. Header (Company Info)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 10, "VENUS SURGICAL", align="L", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 5, "Your Trusted Partner in Surgical Essentials", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "ISO 9001:2015 | CE Certified (CE-11840)", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Ph: +91 9664564057 | Email: vlakkam46@gmail.com", align="L", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    # 2. Quotation Details
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 8, "PROFORMA QUOTATION", align="R", new_x="LMARGIN", new_y="NEXT")
    
    quote_no = f"VS-QT-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
    quote_date = datetime.date.today().strftime("%d-%b-%Y")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(110, 6, f"To: {cust_name.upper()}", align="L")
    pdf.cell(80, 6, f"Date: {quote_date}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(110, 6, "", align="L")
    pdf.cell(80, 6, f"Quote No: {quote_no}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    
    # 3. Table Header
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(15, 8, "Sr.", border=1, fill=True, align="C")
    pdf.cell(85, 8, "Product & Official Description", border=1, fill=True, align="L")
    pdf.cell(25, 8, "Qty", border=1, fill=True, align="C")
    pdf.cell(30, 8, "Rate (INR)", border=1, fill=True, align="R")
    pdf.cell(35, 8, "Total (INR)", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
    
    # 4. Table Body (Catalog Descriptions)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    
    catalog_data = {
        "Surgical Gown": "Fluid-resistant, full sleeves, knit cuffs",
        "Eye Drape": "80x100 cm, adhesive fenestration",
        "Plain Sheet": "120x210 cm, Non-woven protective layer",
        "Face Mask": "3-Ply disposable, high filtration barrier",
        "Buffant Cap": "Lightweight breathable non-woven cap",
        "Shoe Cover": "Slip-resistant non-woven shoe cover"
    }
    
    subtotal = 0
    for idx, item in enumerate(items, 1):
        desc = catalog_data.get(item['name'], "Hospital Disposable")
        line_tot = item['qty'] * item['price']
        subtotal += line_tot
        
        pdf.cell(15, 8, str(idx), border=1, align="C")
        pdf.cell(85, 8, f"{item['name']} ({desc})"[:52], border=1, align="L")
        pdf.cell(25, 8, f"{item['qty']} pcs", border=1, align="C")
        pdf.cell(30, 8, f"{item['price']:.2f}", border=1, align="R")
        pdf.cell(35, 8, f"{line_tot:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
        
    # 5. Totals
    gst_amt = (subtotal * gst_rate) / 100
    grand_tot = subtotal + gst_amt
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(155, 8, "Subtotal", border=1, align="R")
    pdf.cell(35, 8, f"{subtotal:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    
    if gst_rate > 0:
        pdf.cell(155, 8, f"GST ({gst_rate}%)", border=1, align="R")
        pdf.cell(35, 8, f"{gst_amt:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
        
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(155, 8, "GRAND TOTAL (INR)", border=1, fill=True, align="R")
    pdf.cell(35, 8, f"{grand_tot:.2f}", border=1, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")
    
    # 6. Footer (Bank Details)
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, "Terms & Bank Details:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 4, "1. Payment: 100% Advance against this Proforma Invoice.", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4, "2. Bank: HDFC Bank | A/C Name: VENUS SURGICAL", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4, "3. A/C No: 50200012345678 | IFSC: HDFC0001234", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(12)
    pdf.cell(0, 4, "For, VENUS SURGICAL", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.cell(0, 4, "(Authorized Signatory)", align="R")
    
    return bytes(pdf.output())

with tab2:
    st.subheader("📝 ગ્રાહક માટે ક્વોટેશન ફોર્મ")
    
    quote_cust_name = st.text_input("હોસ્પિટલ / ડોક્ટરનું નામ લખો:", placeholder="શાલબી હોસ્પિટલ, સુરત")
    
    products_list = ["-- કોઈ નહિ --", "Surgical Gown", "Eye Drape", "Plain Sheet", "Face Mask", "Buffant Cap", "Shoe Cover"]
    
    st.markdown("#### 📦 ક્વોટેશનમાં ઉમેરવાની પ્રોડક્ટ્સ (મહત્તમ ૩):")
    
    # લાઈન ૧
    c1, c2, c3 = st.columns([2, 1, 1])
    p1 = c1.selectbox("પ્રોડક્ટ ૧", products_list, index=1)
    q1 = c2.number_input("નંગ (Qty) - ૧", min_value=1, value=100)
    r1 = c3.number_input("ભાવ (₹) - ૧", min_value=0.0, value=45.0)
    
    # લાઈન ૨
    c1, c2, c3 = st.columns([2, 1, 1])
    p2 = c1.selectbox("પ્રોડક્ટ ૨", products_list, index=2)
    q2 = c2.number_input("નંગ (Qty) - ૨", min_value=1, value=50)
    r2 = c3.number_input("ભાવ (₹) - ૨", min_value=0.0, value=25.0)
    
    # લાઈન ૩
    c1, c2, c3 = st.columns([2, 1, 1])
    p3 = c1.selectbox("પ્રોડક્ટ ૩", products_list, index=0)
    q3 = c3.number_input("નંગ (Qty) - ૩", min_value=1, value=50)
    r3 = c3.number_input("ભાવ (₹) - ૩", min_value=0.0, value=10.0)
    
    st.write("")
    gst_choice = st.radio("GST નો દર પસંદ કરો:", [0, 5, 12, 18], index=2, horizontal=True)
    
    # ડેટા ભેગો કર્યો
    selected_items = []
    if p1 != "-- કોઈ નહિ --": selected_items.append({"name": p1, "qty": q1, "price": r1})
    if p2 != "-- કોઈ નહિ --": selected_items.append({"name": p2, "qty": q2, "price": r2})
    if p3 != "-- કોઈ નહિ --": selected_items.append({"name": p3, "qty": q3, "price": r3})
    
    st.markdown("---")
    
    # જો ગ્રાહકનું નામ લખાયેલું હોય, તો જ ડાઉનલોડ બટન જીવંત થશે!
    if quote_cust_name.strip() != "" and len(selected_items) > 0:
        pdf_data = create_quotation_pdf(quote_cust_name.strip(), selected_items, gst_choice)
        
        st.success("✅ ક્વોટેશન PDF રેડી છે! નીચેના બટન પર ક્લિક કરીને સેવ કરો:")
        st.download_button(
            label="📥 ફાઈનલ PDF ક્વોટેશન ડાઉનલોડ કરો",
            data=pdf_data,
            file_name=f"Quotation_{quote_cust_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.info("👆 PDF ડાઉનલોડ બટન જોવા માટે ઉપર **હોસ્પિટલનું નામ** લખવું ફરજિયાત છે.")