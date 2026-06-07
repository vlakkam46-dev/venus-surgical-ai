import sqlite3
import streamlit as st
from google import genai 

# ==========================================
# ૧. પેજનું સેટિંગ
# ==========================================
st.set_page_config(page_title="Venus Surgical AI", page_icon="🏥", layout="wide")

st.title("🏥 Venus Surgical - AI સેલ્સ મેનેજર")
st.write("ગ્રાહકના મેસેજ અહીં લખો અને AI ને જવાબ બનાવવાનું કહો.")

# ==========================================
# ૨. ડેટાબેઝમાંથી સ્ટોક લાવવાનું ફંક્શન
# ==========================================
def get_current_stock():
    conn = sqlite3.connect("venus_surgical.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, stock FROM Products")
    all_items = cursor.fetchall()
    conn.close()

    stock_info = ""
    for item in all_items:
        stock_info += f"{item[0]}: {item[1]} નંગ, "
    return stock_info

# સાઈડબારમાં કરંટ સ્ટોક બતાવો
st.sidebar.header("📦 ગોડાઉનનો કરંટ સ્ટોક")
current_stock = get_current_stock()
st.sidebar.info(current_stock)

# ==========================================
# ૪. નવો સ્ટોક અપડેટ કરવાનું સેટિંગ (Admin Panel)
# ==========================================
st.sidebar.markdown("---") 
st.sidebar.header("🔄 નવો સ્ટોક ઉમેરો / બદલો")

update_item = st.sidebar.text_input("પ્રોડક્ટનું નામ લખો (દા.ત. Surgical Gown):")
update_qty = st.sidebar.number_input("નવો સ્ટોક (નંગ):", min_value=0, step=1)

if st.sidebar.button("સ્ટોક અપડેટ કરો"):
    if update_item == "":
        st.sidebar.warning("કૃપા કરીને પ્રોડક્ટનું નામ લખો!")
    else:
        conn = sqlite3.connect("venus_surgical.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE Products SET stock = ? WHERE name = ?", (update_qty, update_item))
        conn.commit()
        conn.close()
        
        st.sidebar.success(f"✅ {update_item} નો નવો સ્ટોક {update_qty} અપડેટ થઈ ગયો!")
        st.sidebar.info("નવો સ્ટોક જોવા માટે ઉપર જમણી બાજુ 'Rerun' પર ક્લિક કરો અથવા પેજ રિફ્રેશ કરો.")

# ==========================================
# ૩. ગ્રાહકનો મેસેજ અને AI નું સેટિંગ
# ==========================================
# ⚠️ તમારી API key અહી મૂકવાનું ભૂલતા નહિ
my_api_key = st.secrets["GEMINI_API_KEY"]

customer_message = st.text_area("ગ્રાહકનો મેસેજ અહી પેસ્ટ કરો:", placeholder="ઉદાહરણ: મારે તાત્કાલિક 500 Surgical Gown જોઈએ છે...")

# જ્યારે યુઝર બટન દબાવે ત્યારે શું થવું જોઈએ?
if st.button("🤖 AI પાસે જવાબ લખાવો", type="primary"):
    
    if customer_message == "":
        st.warning("કૃપા કરીને પહેલા ગ્રાહકનો મેસેજ લખો!")
    else:
        with st.spinner("AI મેનેજર ગ્રાહક માટે જવાબ ટાઈપ કરી રહ્યો છે..."):
            try:
                client = genai.Client(api_key=my_api_key)
                
                prompt = f"""
                તું 'Venus Surgical' કંપનીનો બહુ જ સ્માર્ટ અને નમ્ર સેલ્સ મેનેજર છે.
                તારી પાસે ગોડાઉનનો આ લેટેસ્ટ સ્ટોક છે: {current_stock}

                એક ગ્રાહકનો મેસેજ આવ્યો છે: "{customer_message}"

                આ ગ્રાહકને પ્રોફેશનલ ગુજરાતીમાં જવાબ લખ. 
                જો સ્ટોક માંગ્યા કરતા ઓછો હોય, તો નમ્રતાથી જણાવજે કે અત્યારે કેટલા હાજર છે અને બાકીના ક્યારે બની શકશે.
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