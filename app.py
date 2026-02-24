import streamlit as st
import re
import random
import json
import os
import time
from sentence_transformers import SentenceTransformer, util
import torch

# ================================
# 🎛️ SAHIFA SOZLAMALARI (YANGILANDI)
# ================================
st.set_page_config(
    page_title="Al-Ustoz",  # O'zgardi: "AI-Ustoz" → "Al-Ustoz"
    page_icon="🎓",
    layout="centered",  # O'zgardi: "wide" → "centered"
    initial_sidebar_state="expanded"
)

# ================================
# 🎨 CSS STYLES (YANGILANDI - ZAMONAVIY DIZAYN)
# ================================
st.markdown("""
<style>
    /* Chat xabarlari */
    .stChatMessage { 
        border-radius: 15px; 
        padding: 12px 16px; 
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Input maydoni */
    .stChatFloatingInputContainer {
        bottom: 20px;
        border-radius: 20px;
    }
    
    /* Sidebar sarlavha */
    .sidebar-header { 
        font-size: 1.2em; 
        font-weight: bold; 
        color: #1f77b4; 
    }
    
    /* Metric kartalar */
    .metric-card { 
        background: #f0f2f6; 
        padding: 10px; 
        border-radius: 8px; 
    }
    
    /* Alertlar */
    .stAlert { 
        border-radius: 8px; 
    }
    
    /* Metric qiymati */
    div[data-testid="stMetricValue"] { 
        font-size: 1.5em; 
    }
    
    /* Welcome banner */
    .welcome-banner { 
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Chat input sozlamalari */
    .stChatInputContainer { 
        padding: 20px 0; 
    }
    
    /* Assistant xabarlari uchun maxsus stil */
    [data-testid="stChatMessage"]:has([data-testid="avatarIcon"]:contains("🤖")) {
        background: #f0f7ff;
        border-left: 4px solid #1f77b4;
    }
    
    /* User xabarlari uchun maxsus stil */
    [data-testid="stChatMessage"]:has([data-testid="avatarIcon"]:contains("👤")) {
        background: #f0fff4;
        border-right: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# ================================
# 🧠 MODELNI YUKLASH
# ================================
@st.cache_resource
def yukla_model():
    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

with st.spinner("🧠 AI modeli yuklanmoqda... (birinchi marta 20-30 soniya)"):
    model = yukla_model()

# ================================
# 📄 FAYLDAN MA'LUMOT O'QISH
# ================================
def dars_faylini_oku(fayl_nomi="dars.txt"):
    """dars.txt faylidan transkript o'qish"""
    if not os.path.exists(fayl_nomi):
        return None
    
    try:
        with open(fayl_nomi, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            return None
        
        qatorlar = [q.strip() for q in content.split('\n') if len(q.strip()) > 10]
        
        if not qatorlar:
            return None
        
        transkript = []
        for i, gap in enumerate(qatorlar):
            transkript.append({
                "text": gap,
                "time": i * 5
            })
        
        return transkript
    
    except Exception as e:
        st.error(f"❌ Faylni o'qishda xatolik: {str(e)}")
        return None

# Namuna ma'lumotlar
NAMUNA_TRANSKRIPT = [
    {"text": "To be fe'li ingliz tilida bo'lmoq degani. Bu eng muhim fe'llardan biri.", "time": 0},
    {"text": "Hozirgi zamonda to be fe'lining uchta shakli bor: am, is, are.", "time": 5},
    {"text": "I am - men ...man. Masalan: I am a student. Men talabaman.", "time": 10},
    {"text": "He is, She is, It is - u ...dir. Masalan: She is smart. U aqlli.", "time": 15},
    {"text": "We are, You are, They are - biz/siz/ular. They are doctors. Ular shifokorlar.", "time": 20},
    {"text": "Present Simple odatiy ish-harakatlar uchun ishlatiladi.", "time": 25},
    {"text": "I study every day. Men har kuni o'qiyman.", "time": 30},
    {"text": "He plays football. U futbol o'ynaydi. Uchinchi shaxsda -s qo'shiladi.", "time": 35},
    {"text": "Savol gap tuzish uchun Do/Does yordamchi fe'llari ishlatiladi. Do you study?", "time": 40},
    {"text": "Inkor gap uchun don't/doesn't ishlatiladi. I don't know. Men bilmayman.", "time": 45},
]

# ================================
# 🧠 AI MIYA KLASSI
# ================================
class AI_Miya:
    def __init__(self, transkript):
        self.data = transkript
        self.matnlar = [item['text'] for item in transkript]
        self.vaqtler = [item['time'] for item in transkript]
        self.vektorlar = model.encode(self.matnlar, convert_to_tensor=True)
        
        self.inglizcha_gaplar = [
            item for item in transkript 
            if re.search(r'[a-zA-Z]{3,}', item['text']) and len(item['text']) < 150
        ]

    def normalize_query(self, query):
        query = query.lower().strip()
        query = re.sub(r'\btobe\b', 'to be', query)
        query = re.sub(r'\btobe\b', 'to be', query)
        query = re.sub(r'\s+', ' ', query)
        return query

    def aniqlash_mavzu(self, savol):
        """Savoldan mavzuni aniqlash"""
        savol_past = savol.lower()
        
        mavzu_kalitlari = {
            "present_simple": ["present simple", "odat", "har kuni", "every day", "do/does", "don't", "plays", "works", "studies"],
            "to_be": ["to be", "am is are", "bo'lmoq", "was were", "will be"],
            "past_simple": ["past simple", "o'tgan zamon", "edim", "edi", "-di", "yesterday"],
            "future": ["future", "kelajak", "will", "bo'laman"],
        }
        
        for mavzu, kalitlar in mavzu_kalitlari.items():
            if any(kalit in savol_past for kalit in kalitlar):
                return mavzu
        
        return None

    def qidiruv(self, savol):
        """
        PROFESSIONAL QIDIRUV: 
        - Aniq mavzu mosligini tekshirish
        - AQILLI kontekst kengaytirish (faqat bir mavzudagi gaplar)
        """
        savol_norm = self.normalize_query(savol)
        savol_past = savol_norm.lower()
        
        # 1-QADAM: Mavzuni aniqlash
        aniqlangan_mavzu = self.aniqlash_mavzu(savol)
        
        # 2-QADAM: Vektor qidiruv
        savol_v = model.encode(savol_norm, convert_to_tensor=True)
        scores = util.cos_sim(savol_v, self.vektorlar)[0].clone()
        
        # 3-QADAM: Mavzuga ko'ra ballarni sozlash
        if aniqlangan_mavzu:
            for i, matn in enumerate(self.matnlar):
                matn_past = matn.lower()
                
                mavzuga_oid = False
                if aniqlangan_mavzu == "present_simple":
                    mavzuga_oid = any(x in matn_past for x in ["present simple", "odat", "har kuni", "every", "do", "does", "don't", "plays", "works", "studies"])
                elif aniqlangan_mavzu == "to_be":
                    mavzuga_oid = any(x in matn_past for x in ["to be", "am", "is", "are", "bo'lmoq", "was", "were"])
                elif aniqlangan_mavzu == "past_simple":
                    mavzuga_oid = any(x in matn_past for x in ["past", "o'tgan", "was", "were", "edi", "yesterday"])
                elif aniqlangan_mavzu == "future":
                    mavzuga_oid = any(x in matn_past for x in ["future", "kelajak", "will", "bo'laman"])
                
                if mavzuga_oid:
                    original_score = scores[i].item()
                    scores[i] = min(original_score * 1.5, 1.0)
        
        # 4-QADAM: Eng yaxshi natijalarni olish
        top_k = min(3, len(self.matnlar))
        top_results = torch.topk(scores, k=top_k)
        indices = top_results.indices.tolist()
        
        natijalar = []
        for idx in indices:
            score = scores[idx].item()
            
            if score < 0.25:
                continue
            
            # 5-QADAM: AQILLI KONTEKST KENGAYTIRISH
            kontekst_gaplar = [self.matnlar[idx]]
            
            # Oldingi gaplarni tekshirish
            for i in range(idx - 1, max(idx - 3, -1), -1):
                if i >= 0:
                    qoshni_gap = self.matnlar[i].lower()
                    
                    mavzuga_oid = False
                    if aniqlangan_mavzu == "present_simple":
                        mavzuga_oid = any(x in qoshni_gap for x in ["present simple", "odat", "every", "do", "does", "plays", "works", "studies", "har kuni"])
                    elif aniqlangan_mavzu == "to_be":
                        mavzuga_oid = any(x in qoshni_gap for x in ["to be", "am", "is", "are", "bo'lmoq", "was", "were"])
                    elif aniqlangan_mavzu == "past_simple":
                        mavzuga_oid = any(x in qoshni_gap for x in ["past", "o'tgan", "was", "were", "edi"])
                    elif aniqlangan_mavzu == "future":
                        mavzuga_oid = any(x in qoshni_gap for x in ["future", "kelajak", "will"])
                    
                    if mavzuga_oid:
                        kontekst_gaplar.insert(0, self.matnlar[i])
                    else:
                        break
            
            # Keyingi gaplarni tekshirish
            for i in range(idx + 1, min(idx + 3, len(self.matnlar))):
                qoshni_gap = self.matnlar[i].lower()
                
                mavzuga_oid = False
                if aniqlangan_mavzu == "present_simple":
                    mavzuga_oid = any(x in qoshni_gap for x in ["present simple", "odat", "every", "do", "does", "plays", "works", "studies", "har kuni"])
                elif aniqlangan_mavzu == "to_be":
                    mavzuga_oid = any(x in qoshni_gap for x in ["to be", "am", "is", "are", "bo'lmoq", "was", "were"])
                elif aniqlangan_mavzu == "past_simple":
                    mavzuga_oid = any(x in qoshni_gap for x in ["past", "o'tgan", "was", "were", "edi"])
                elif aniqlangan_mavzu == "future":
                    mavzuga_oid = any(x in qoshni_gap for x in ["future", "kelajak", "will"])
                
                if mavzuga_oid:
                    kontekst_gaplar.append(self.matnlar[i])
                else:
                    break
            
            kengaytirilgan_matn = " ".join(kontekst_gaplar)
            
            natijalar.append({
                "text": kengaytirilgan_matn,
                "time": self.vaqtler[idx],
                "score": score,
                "exact_match": idx,
                "mavzu": aniqlangan_mavzu
            })
        
        return natijalar

    def format_javob(self, natijalar, savol):
        if not natijalar or natijalar[0]['score'] < 0.25:
            return None
        
        top = natijalar[0]
        savol_lower = savol.lower()
        aniqlangan_mavzu = top.get('mavzu')
        
        samimiy_qo_shimchalar = [
            "😊", "👍", "🎯", "✨", "🌟",
            "Ajoyib savol!", "Tushunarli bo'ldimi?", 
            "Yana savollaringiz bormi?", "Birga o'rganamiz! 🚀"
        ]
        
        if aniqlangan_mavzu == "present_simple":
            shablon = f"""📚 **Present Simple (Odatiy Zamon):**

{top['text']}

📖 Bu ma'lumot darsning **{top['time']}**-soniyasida batafsil tushuntirilgan.

🎯 **Eslatma:** Present Simple har kungi odatlar, doimiy holatlar va umumiy haqiqatlar uchun ishlatiladi.

💡 **Misol:** I study every day. (Men har kuni o'qiyman.)"""
            
        elif aniqlangan_mavzu == "to_be":
            shablon = f"""💡 **To Be Fe'li (Bo'lmoq):**

{top['text']}

📖 Bu ma'lumot darsning **{top['time']}**-soniyasida batafsil tushuntirilgan.

🎯 **Eslatma:** To be fe'li holat, kasb, yosh va joylashuvni bildiradi.

💡 **Misol:** I am a student. (Men talabaman.)"""
            
        elif aniqlangan_mavzu == "past_simple":
            shablon = f"""⏪ **Past Simple (O'tgan Zamon):**

{top['text']}

📖 Bu ma'lumot darsning **{top['time']}**-soniyasida batafsil tushuntirilgan.

🎯 **Eslatma:** Past Simple o'tgan zamonda tugagan ish-harakatlar uchun ishlatiladi.

💡 **Misol:** I studied yesterday. (Men kecha o'qidim.)"""
            
        elif aniqlangan_mavzu == "future":
            shablon = f"""⏩ **Future Simple (Kelajak Zamon):**

{top['text']}

📖 Bu ma'lumot darsning **{top['time']}**-soniyasida batafsil tushuntirilgan.

🎯 **Eslatma:** Future Simple kelajakda bo'ladigan ish-harakatlar uchun ishlatiladi.

💡 **Misol:** I will study tomorrow. (Men ertaga o'qiyman.)"""
            
        else:
            if any(word in savol_lower for word in ["nima", "haqida", "ta'rif", "tushuntir", "bu nima"]):
                shablon = f"""💡 **Tushuncha:**

{top['text']}

📖 Bu ma'lumot darsning **{top['time']}**-soniyasida batafsil tushuntirilgan.

💭 **Savol:** Ushbu qoidani qanday qo'llashni tushundingizmi?"""
            elif any(word in savol_lower for word in ["qanday", "qilib", "usul", "formula", "qoida", "ishlatiladi"]):
                shablon = f"""🛠 **Qo'llanish tartibi:**

{top['text']}

🎯 **Amaliyot:** Mana shu qoidaga asosan bir gap tuzib ko'ring!

💡 Maslahat: Xato qilishdan qo'rqmang - bu o'rganish jarayoni."""
            else:
                shablon = f"""✅ **Topilgan ma'lumot:**

{top['text']}

⏱️ Darsning **{top['time']}**-soniyasida

💡 **Davom etamizmi?** Savolingiz bo'lsa, bemalol so'rang!"""
        
        if top['score'] > 0.8:
            shablon += "\n\n🎯 _Juda aniq javob topildi!_"
        elif top['score'] > 0.6:
            shablon += "\n\n⚠️ _Yaxshi javob, lekin boshqa manbalarga ham qarang._"
        
        shablon += f"\n\n{random.choice(samimiy_qo_shimchalar)}"
        
        return shablon

    def get_fallback_javob(self):
        fallback_javoblar = [
            "🤔 Bu savol hozircha mening bilim doiramdan tashqari. Boshqacha so'zlab ko'rasizmi?",
            "📚 Bu haqda darslikda aniq ma'lumot topolmadim. Balki o'qituvchidan so'rash kerakdir?",
            "🚀 Men hali o'rganayapman! Bu savolni eslab qoldim, keyinroq javob berishga harakat qilaman.",
            "💭 Qiziqarli savol! Hozircha faqat darslikdagi mavzularga javob bera olaman.",
            "🙏 Kechirasiz, bu haqda ma'lumotim yo'q. Boshqa savol bering, albatta yordam beraman!"
        ]
        return random.choice(fallback_javoblar)

    def test_gap_ol(self):
        toza_inglizcha_gaplar = []
        
        for item in self.data:
            gap = item['text']
            
            lotin_harflar = len(re.findall(r'[a-zA-Z]', gap))
            kirill_harflar = len(re.findall(r'[а-яА-ЯёЁўўққғғҳҳ]', gap))
            
            ozbekcha_belgilar = ['fe', 'li', 'da', 'uchun', 'ishlatiladi', 
                                'bo', 'lgan', 'degani', 'tarjima', 'qilinadi']
            
            gap_past = gap.lower()
            ozbekcha_so_z_bormi = any(soz in gap_past for soz in ozbekcha_belgilar)
            
            if (lotin_harflar > kirill_harflar * 3 and
                not ozbekcha_so_z_bormi and
                len(gap.split()) >= 2 and
                len(gap) < 80 and
                re.search(r'\b(am|is|are|was|were)\b', gap)):
                
                toza_inglizcha_gaplar.append(item)
        
        if toza_inglizcha_gaplar:
            return random.choice(toza_inglizcha_gaplar)
        
        fallback_gaplar = [
            item for item in self.data 
            if re.search(r'[a-zA-Z]{3,}', item['text']) and 
               len(item['text']) < 100
        ]
        
        return random.choice(fallback_gaplar) if fallback_gaplar else None

    def tekshirish(self, user_javob, to_g_ri_javob):
        user_clean = re.sub(r'[^\w\s]', '', user_javob.lower()).strip()
        correct_clean = re.sub(r'[^\w\s]', '', to_g_ri_javob.lower()).strip()
        
        if user_clean == correct_clean:
            return True, 1.0
        
        user_words = set(user_clean.split())
        correct_words = set(correct_clean.split())
        
        if not correct_words:
            return False, 0.0
        
        overlap = len(user_words & correct_words) / len(correct_words)
        return overlap >= 0.8, overlap

    def davom_etishni_tushun(self, javob):
        javob = javob.lower().strip()
        
        davom_belgilari = [
            'ha', 'haa', 'albatta', 'davom', 'davom et', 'davom ettir',
            'yana', 'yana bitta', 'yana bir', 'ok', 'okay', 'mayli', 'boshladik',
            'yur', 'ketdik', 'ber', 'bering', 'tushundim', 'ready', 'go', 'next',
            'keyingisi', 'keyingi', 'test', 'sinab ko', 'sinab koramiz'
        ]
        
        toxtash_belgilari = [
            'yo', 'yoq', 'bas', 'yetarli', 'yetar', 'to', 'toxta',
            'kerak emas', 'kerakemas', 'keyin', 'keyinroq', 'hozircha',
            'rahmat', 'raxmat', 'tashakkur', 'stop', 'no', 'finish', 'tamom',
            'bo', 'boldi', 'charchadim', 'dam olaman'
        ]
        
        for belgi in davom_belgilari:
            if belgi in javob:
                return True
        for belgi in toxtash_belgilari:
            if belgi in javob:
                return False
        
        davom_frazalar = ["davom etmoqchiman", "yana sinab ko'raman", "tayyorman"]
        toxtash_frazalar = ["yetarli", "boshqa kerak emas", "dam olaman"]
        
        savol_v = model.encode(javob, convert_to_tensor=True)
        
        for fraza in davom_frazalar:
            fraza_v = model.encode(fraza, convert_to_tensor=True)
            if util.cos_sim(savol_v, fraza_v).item() > 0.7:
                return True
        
        for fraza in toxtash_frazalar:
            fraza_v = model.encode(fraza, convert_to_tensor=True)
            if util.cos_sim(savol_v, fraza_v).item() > 0.7:
                return False
        
        if '?' in javob or 'nima' in javob or 'qanday' in javob:
            return None
        
        return True

    def test_davom_etish_savoli(self):
        savollar = [
            "🔄 **Yana test yechamizmi?** (`ha` yoki `yo'q` deb yozing)",
            "🎯 **Bilimingizni yana sinab ko'ramizmi?** (`davom` yoki `yetarli`)",
            "✨ **Yana bir gapni tartiblab ko'rasizmi?** (`ha` / `yo'q`)",
            "🚀 **Keyingi testga o'tamizmi?** (`yur` yoki `to'xta`)"
        ]
        return random.choice(savollar)

# ================================
# 💾 SESSION STATE
# ================================
def init_session():
    if "ustoz" not in st.session_state:
        fayl_darsi = dars_faylini_oku("dars.txt")
        if fayl_darsi:
            st.session_state.ustoz = AI_Miya(fayl_darsi)
            st.success("✅ dars.txt fayli muvaffaqiyatli yuklandi!")
        else:
            st.session_state.ustoz = AI_Miya(NAMUNA_TRANSKRIPT)
            st.info("ℹ️ Namuna ma'lumotlar ishlatilmoqda (dars.txt topilmadi)")
    
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "xatolar" not in st.session_state:
        st.session_state.xatolar = []
    if "ball" not in st.session_state:
        st.session_state.ball = 0
    if "holat" not in st.session_state:
        st.session_state.holat = "oddiy"
    if "savol_gapi" not in st.session_state:
        st.session_state.savol_gapi = None
    
    if len(st.session_state.chat) == 0:
        welcome_msgs = [
            "👋 **Assalomu alaykum!** Men Al-Ustozman. Bugun nima o'rganamiz?",
            "🎓 **Salom!** Ingliz tili sirlarini birga ochamiz. Savolingiz bormi?",
            "✨ **Xush kelibsiz!** Men sizning shaxsiy repetitoringizman. Boshlaymizmi?",
            "🌟 **Assalomu alaykum!** Bilim olish — bu sarguzasht! Qaysi mavzuni o'rganamiz?",
            "🤖 **Salom!** Men Al-Ustozman. Sizga yordam berish uchun shu yerdaman. 😊"
        ]
        st.session_state.chat.append({
            "role": "assistant",
            "content": random.choice(welcome_msgs),
            "video_time": None
        })

init_session()

# ================================
# 🎛️ SIDEBAR
# ================================
with st.sidebar:
    st.markdown('<p class="sidebar-header">📊 O\'quvchi Profili</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🏆 Ball", st.session_state.ball)
    with col2:
        daraja = st.session_state.ball // 10
        st.metric("📈 Daraja", f"{daraja}-level")
    
    st.markdown("---")
    
    st.subheader("📁 Dars ma'lumoti")
    if os.path.exists("dars.txt"):
        st.success("✅ dars.txt topildi")
        try:
            with open("dars.txt", 'r', encoding='utf-8') as f:
                qator_soni = len([q for q in f.read().split('\n') if q.strip()])
            st.info(f"📝 {qator_soni} ta gap yuklangan")
        except:
            st.warning("⚠️ Faylni o'qishda xatolik")
    else:
        st.warning("⚠️ dars.txt topilmadi")
        st.caption("Namuna ma'lumotlar ishlatilmoqda")
    
    uploaded_file = st.file_uploader("📤 Boshqa transkript (JSON)", type="json")
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            if isinstance(data, list) and all('text' in item and 'time' in item for item in data):
                st.session_state.ustoz = AI_Miya(data)
                st.session_state.chat = []
                st.success("✅ Yangi dars yuklandi!")
            else:
                st.error("❌ Noto'g'ri JSON formati!")
        except Exception as e:
            st.error(f"❌ Xatolik: {str(e)}")
    
    st.markdown("---")
    
    st.subheader("⚠️ Xatolar daftari")
    if st.session_state.xatolar:
        unikal_xatolar = list(set(st.session_state.xatolar))[-5:]
        for xato in unikal_xatolar:
            st.warning(f"❌ {xato[:50]}...")
    else:
        st.info("✨ Xatolar yo'q. Barakalla!")
    
    st.markdown("---")
    
    if st.button("🔄 Boshidan boshlash", use_container_width=True, type="secondary"):
        st.session_state.update({
            "xatolar": [],
            "ball": 0,
            "chat": [],
            "holat": "oddiy",
            "savol_gapi": None
        })
        fayl_darsi = dars_faylini_oku("dars.txt")
        if fayl_darsi:
            st.session_state.ustoz = AI_Miya(fayl_darsi)
        st.rerun()

# ================================
# 💬 ASOSIY CHAT
# ================================

if len(st.session_state.chat) <= 1:
    st.markdown("""
    <div class="welcome-banner">
        <h2>🎓 Al-Ustozga Xush Kelibsiz!</h2>
        <p>Videodarslaringiz bilan interaktiv muloqot qiling • Savol bering yoki test yeching</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("🎓 Al-Ustoz: Aqlli Repetitor")
    st.caption("Videodarslaringiz bilan interaktiv muloqot qiling")

chat_container = st.container()
with chat_container:
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("video_time") is not None:
                st.caption(f"🎥 Darsning **{m['video_time']}**-soniyasida")

prompt = st.chat_input("Savolingizni yozing... (masalan: 'to be haqida ma'lumot ber' yoki 'test')")

if prompt:
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    ustoz = st.session_state.ustoz
    javob = ""
    video_time = None
    
    if st.session_state.holat == "test_davom_so'ra":
        davom_etish = ustoz.davom_etishni_tushun(prompt)
        
        if davom_etish is True:
            test_gap = ustoz.test_gap_ol()
            if test_gap:
                st.session_state.savol_gapi = test_gap
                sozlar = test_gap['text'].split()
                random.shuffle(sozlar)
                javob = f"📝 **Yangi vazifa:** Quyidagi so'zlardan to'g'ri inglizcha gap tuzing:\n\n"
                javob += f"`{' / '.join(sozlar)}`\n\n"
                javob += "_✍️ Javobingizni yozing, men tekshiraman!_"
                st.session_state.holat = "test_tekshir"
            else:
                javob = "⚠️ Test uchun boshqa gaplar topilmadi. Boshqa mavzuga o'tamizmi?"
                st.session_state.holat = "oddiy"
                
        elif davom_etish is False:
            javob = f"✅ **Ajoyib!** Bugun {st.session_state.ball} ball to'pladingiz! 🎉\n\n"
            javob += "💡 **Maslahat:** Xato qilgan gaplaringizni sidebar'dagi 'Xatolar daftari' dan takrorlang.\n\n"
            javob += "👋 Yana savollaringiz bo'lsa, har doim shu yerdaman!"
            st.session_state.holat = "oddiy"
            
        else:
            javob = "🤔 Tushunmadim, aniqroq yozib bersangiz:\n\n"
            javob += "- `ha` yoki `davom` — yana test beraman\n"
            javob += "- `yo'q` yoki `yetarli` — testni to'xtatamiz\n\n"
            javob += "Siz nima deysiz? 😊"
        
    elif st.session_state.holat == "test_tekshir":
        correct_item = st.session_state.savol_gapi
        if correct_item:
            correct_text = correct_item['text']
            is_correct, overlap = ustoz.tekshirish(prompt, correct_text)
            
            if is_correct:
                javob = f"✅ **Ajoyib!** To'g'ri topdingiz:\n\n`{correct_text}`\n\n🎉 +10 ball!"
                st.session_state.ball += 10
            else:
                javob = f"❌ **Xato.** To'g'ri variant:\n\n`{correct_text}`\n\n💡 Maslahat: So'zlar tartibiga va imloga e'tibor bering!"
                if correct_text not in st.session_state.xatolar:
                    st.session_state.xatolar.append(correct_text)
        else:
            javob = "⚠️ Test xatosi. Iltimos, qaytadan `test` deb yozing."
        
        javob += f"\n\n---\n{ustoz.test_davom_etish_savoli()}"
        st.session_state.holat = "test_davom_so'ra"
    
    elif prompt.lower().strip() in ['ha', 'test', 'ok', 'mayli', 'boshladik', "sinab ko'ramiz", "yur"]:
        test_gap = ustoz.test_gap_ol()
        if test_gap:
            st.session_state.savol_gapi = test_gap
            sozlar = test_gap['text'].split()
            random.shuffle(sozlar)
            
            javob = f"📝 **Vazifa:** Quyidagi so'zlardan to'g'ri inglizcha gap tuzing:\n\n"
            javob += f"`{' / '.join(sozlar)}`\n\n"
            javob += "_✍️ Javobingizni yozing, men tekshiraman!_"
            st.session_state.holat = "test_tekshir"
        else:
            javob = "⚠️ Test uchun inglizcha gap topilmadi. Boshqa savol bering."
    
    else:
        natijalar = ustoz.qidiruv(prompt)
        
        if natijalar:
            top_natija = natijalar[0]
            video_time = top_natija['time']
            
            formatted = ustoz.format_javob(natijalar, prompt)
            javob = formatted if formatted else f"🤖 {top_natija['text']}"
            
            javob += "\n\n---\n🧐 **Bilimingizni sinab ko'ramizmi?** (`test` deb yozing)"
            st.session_state.holat = "taklif"
        else:
            javob = ustoz.get_fallback_javob()
            javob += "\n\n💡 **Maslahat**:\n"
            javob += "- Boshqa so'zlar bilan so'rang\n"
            javob += "- Mavzuni aniqroq yozing\n"
            javob += "- Yoki `test` deb bilimingizni sinab ko'ring"
    
    with st.chat_message("assistant"):
        st.markdown(javob)
        if video_time is not None:
            st.caption(f"🎥 Bu ma'lumot videoning **{video_time}**-soniyasida")
    
    st.session_state.chat.append({
        "role": "assistant",
        "content": javob,
        "video_time": video_time
    })
    
    st.rerun()

# ================================
# 🦶 FOOTER
# ================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: small; padding: 20px;'>
    🎓 <b>Al-Ustoz v3.0 Professional</b> | Aqlli ta'lim platformasi<br>
    📄 <b>dars.txt</b> fayli asosida ishlayapti | 
    💡 Savol bering yoki test yeching
</div>
""", unsafe_allow_html=True)

# ================================
# 📋 YO'RIQNOMA
# ================================
with st.expander("📖 Qanday ishlatish kerak?"):
    st.markdown("""
    ### 💬 Savol berish
    - "to be haqida ma'lumot ber"
    - "present simple qanday ishlatiladi?"
    - "am is are farqi nima?"
    - "o'tgan zamon qanday?"
    
    ### 📝 Test yechish
    - "test" deb yozing
    - "ha" deb javob bering
    - Gapni to'g'ri tartiblang
    
    ### 📁 O'z darsingizni yuklash
    1. `dars.txt` fayl yarating
    2. Har bir gapni yangi qatorda yozing
    3. Dasturni qayta ishga tushiring
    
    ### 🎥 Video vaqti
    - Har bir javob ostida videoning qaysi soniyasida bu ma'lumot aytilgani ko'rsatiladi
    
    ### 🧠 AI Qanday Ishlaydi?
    - **Mavzu aniqlash:** Savoldan mavzuni aniqlaydi (Present Simple, To Be, etc.)
    - **Kontekst kengaytirish:** Faqat bir mavzudagi qo'shni gaplar birlashtiriladi
    - **Aqlli shablonlar:** Savol turiga qarab javob formati o'zgaradi
    - **Semantik qidiruv:** Ma'no bo'yicha qidiradi
    - **Aqlli test davomi:** Testdan keyin davom etishni so'raydi
    """)