import streamlit as st
import gspread
from google import genai 
import json
# ==========================================
# ૧. પેજનું સેટિંગ
# ==========================================
st.set_page_config(page_title="Venus Surgical AI", page_icon="🏥", layout="wide")
st.title("🏥 Venus Surgical - AI સેલ્સ મેનેજર (Google Sheets 🟢)")
st.write("હવે તમારો સ્ટોક સીધો ગૂગલ શીટ સાથે જોડાયેલો છે!")

# ==========================================
# ૨. Google Sheets સાથે જોડાણ
# ==========================================
# credentials.json ફાઈલનો ઉપયોગ કરીને રોબોટને બોલાવ્યો
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
    records = sheet.get_all_records() # શીટનો બધો ડેટા વાંચશે
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
# ૪. નવો સ્ટોક અપડેટ કરવાનું સેટિંગ (Admin Panel)
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
            # શીટમાં એ પ્રોડક્ટ કઈ લાઈનમાં છે તે શોધશે
            cell = sheet.find(update_item)
            # તે જ લાઈનમાં બાજુના ખાનામાં (કોલમ ૨) નવો સ્ટોક લખશે
            sheet.update_cell(cell.row, 2, update_qty)
            
            st.sidebar.success(f"✅ ગૂગલ શીટમાં {update_item} નો નવો સ્ટોક અપડેટ થઈ ગયો!")
            get_current_stock.clear()
            st.rerun()
        except gspread.exceptions.CellNotFound:
            st.sidebar.error("આ નામની પ્રોડક્ટ ગૂગલ શીટમાં મળી નથી. સ્પેલિંગ ચેક કરો.")

# ==========================================
# ૫. ગ્રાહકનો મેસેજ અને AI નું સેટિંગ
# ==========================================
my_api_key = st.secrets["GEMINI_API_KEY"]

customer_message = st.text_area("ગ્રાહકનો મેસેજ અહી પેસ્ટ કરો:", placeholder="ઉદાહરણ: મારે તાત્કાલિક 500 Surgical Gown જોઈએ છે...")

if st.button("🤖 AI પાસે જવાબ લખાવો", type="primary"):
    if customer_message == "":
        st.warning("કૃપા કરીને પહેલા ગ્રાહકનો મેસેજ લખો!")
    else:
        with st.spinner("AI મેનેજર ગૂગલ શીટ જોઈને જવાબ ટાઈપ કરી રહ્યો છે..."):
            try:
                client = genai.Client(api_key=my_api_key)
                prompt = f"""
                તું 'Venus Surgical' કંપનીનો બહુ જ સ્માર્ટ અને નમ્ર સેલ્સ મેનેજર છે.
                તારી પાસે ગોડાઉનનો આ લેટેસ્ટ સ્ટોક છે: {current_stock}
                એક ગ્રાહકનો મેસેજ આવ્યો છે: "{customer_message}"
                આ ગ્રાહકને પ્રોફેશનલ ગુજરાતીમાં જવાબ લખ. 
                જો સ્ટોક માંગ્યા કરતા ઓછો હોય, તો નમ્રતાથી જણાવજે.
                """
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                st.success("✅ જવાબ તૈયાર છે!")
                st.write("==================================================")
                st.write(response.text)
                st.write("==================================================")
            except Exception as e:
                st.error(f"કંઈક ભૂલ થઈ: {e}")