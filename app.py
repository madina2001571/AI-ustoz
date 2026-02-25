# ================================================================================
# 🎓 AL-USTOZ: AQILLI REPETITOR PLATFORMASI
# ================================================================================
# Versiya: 3.0 Professional
# Muallif: AI-Ustoz Team
# Oxirgi yangilanish: 2026
# 
# FUNKSIYALAR:
# - Mavzu bo'yicha aqlli qidiruv (RAG)
# - Test tizimi (faqat inglizcha so'zlar)
# - Ball va daraja tizimi
# - Xatolar daftari
# - Video timestamp qo'llab-quvvatlash
# ================================================================================

import streamlit as st
import re
import random
import json
import os
import time
from sentence_transformers import SentenceTransformer, util
import torch

# ================================================================================
# 🎛️ 1. SAHIFA SOZLAMALARI
# ================================================================================
st.set_page_config(
    page_title="Al-Ustoz",           # Brauzer sarlavhasi
    page_icon="🎓",                   # Sahifa ikonchasi
    layout="centered",                # Sahifa kengligi (centered yoki wide)
    initial_sidebar_state="expanded"  # Sidebar holati
)

# ================================================================================
# 🎨 2. CSS STYLES — ZAMONAVIY DIZAYN
# ================================================================================
st.markdown("""
<style>
    /* Chat xabarlari — yumaloq burchaklar va soya */
    .stChatMessage { 
        border-radius: 15px; 
        padding: 12px 16px; 
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Input maydoni — pastda joylashgan, yumaloq */
    .stChatFloatingInputContainer {
        bottom: 20px;
        border-radius: 20px;
    }
    
    /* Sidebar sarlavha — ko'k rang, qalin */
    .sidebar-header { 
        font-size: 1.2em; 
        font-weight: bold; 
        color: #1f77b4; 
    }
    
    /* Metric kartalar — kulrang fon */
    .metric-card { 
        background: #f0f2f6; 
        padding: 10px; 
        border-radius: 8px; 
    }
    
    /* Alertlar — yumaloq burchaklar */
    .stAlert { 
        border-radius: 8px; 
    }
    
    /* Metric qiymati — katta shrift */
    div[data-testid="stMetricValue"] { 
        font-size: 1.5em; 
    }
    
    /* Welcome banner — gradient fon */
    .welcome-banner { 
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Chat input — padding */
    .stChatInputContainer { 
        padding: 20px 0; 
    }
    
    /* Assistant xabarlari — ko'k fon, chapda chiziq */
    [data-testid="stChatMessage"]:has([data-testid="avatarIcon"]:contains("🤖")) {
        background: #f0f7ff;
        border-left: 4px solid #1f77b4;
    }
    
    /* User xabarlari — yashil fon, o'ngda chiziq */
    [data-testid="stChatMessage"]:has([data-testid="avatarIcon"]:contains("👤")) {
        background: #f0fff4;
        border-right: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# ================================================================================
# 🧠 3. MODELNI YUKLASH — AI ENGINE
# ================================================================================
@st.cache_resource
def yukla_model():
    """
    Sentence Transformer modelini yuklaydi.
    @st.cache_resource — modelni bir marta yuklab, keshda saqlaydi.
    """
    return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Modelni yuklash jarayoni — foydalanuvchiga ko'rsatiladi
with st.spinner("🧠 AI modeli yuklanmoqda... (birinchi marta 20-30 soniya)"):
    model = yukla_model()

# ================================================================================
# 📄 4. FAYLDAN MA'LUMOT O'QISH
# ================================================================================
def dars_faylini_oku(fayl_nomi="dars.txt"):
    """
    dars.txt faylidan transkript o'qiydi.
    
    Parametrlar:
        fayl_nomi (str): O'qiladigan fayl nomi
    
    Qaytaradi:
        list: Transkript ma'lumotlari (text, time)
        None: Agar fayl topilmasa
    """
    # Fayl mavjudligini tekshirish
    if not os.path.exists(fayl_nomi):
        return None
    
    try:
        # Faylni ochish va o'qish
        with open(fayl_nomi, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Bo'sh faylni tekshirish
        if not content:
            return None
        
        # Har bir qatorni ajratish (faqat 10 belgidan uzun qatorlar)
        qatorlar = [q.strip() for q in content.split('\n') if len(q.strip()) > 10]
        
        if not qatorlar:
            return None
        
        # Transkript formatiga keltirish
        transkript = []
        for i, gap in enumerate(qatorlar):
            transkript.append({
                "text": gap,      # Gap matni
                "time": i * 5     # Har bir gap 5 soniyadan keyin
            })
        
        return transkript
    
    except Exception as e:
        st.error(f"❌ Faylni o'qishda xatolik: {str(e)}")
        return None

# ================================================================================
# 📚 5. NAMUNA MA'LUMOTLAR (agar dars.txt topilmasa)
# ================================================================================
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

# ================================================================================
# 🧠 6. AI MIYA KLASSI — ASOSIY MANTIQ
# ================================================================================
class AI_Miya:
    """
    AI-Ustoz ning asosiy miyasi.
    Barcha qidiruv, test va javob generatsiya funksiyalari shu klassda.
    """
    
    def __init__(self, transkript):
        """
        Klass initsializatsiyasi.
        
        Parametrlar:
            transkript (list): Darslik ma'lumotlari
        """
        self.data = transkript
        self.matnlar = [item['text'] for item in transkript]
        self.vaqtler = [item['time'] for item in transkript]
        # Barcha matnlarni vektorlarga aylantirish (bir marta)
        self.vektorlar = model.encode(self.matnlar, convert_to_tensor=True)
        
        # Test uchun inglizcha gaplarni ajratib olish
        self.inglizcha_gaplar = [
            item for item in transkript 
            if re.search(r'[a-zA-Z]{3,}', item['text']) and len(item['text']) < 150
        ]

    # ============================================================================
    # 6.1 SAVOLNI TOZALASH
    # ============================================================================
    def normalize_query(self, query):
        """
        Foydalanuvchi savolini tozalaydi va standartlashtiradi.
        
        Parametrlar:
            query (str): Foydalanuvchi savoli
        
        Qaytaradi:
            str: Tozalangan savol
        """
        query = query.lower().strip()                    # Kichik harf, bo'sh joylarni olib tashlash
        query = re.sub(r'\btobe\b', 'to be', query)      # "tobe" → "to be"
        query = re.sub(r'\btobe\b', 'to be', query)      # Qayta tekshirish
        query = re.sub(r'\s+', ' ', query)               # Ko'p bo'shliqlarni bittaga
        return query

    # ============================================================================
    # 6.2 MAVZUNI ANIQLASH
    # ============================================================================
    def aniqlash_mavzu(self, savol):
        """
        Savoldan qaysi mavzu so'ralganini aniqlaydi.
        
        Parametrlar:
            savol (str): Foydalanuvchi savoli
        
        Qaytaradi:
            str: Mavzu nomi yoki None
        """
        savol_past = savol.lower()
        
        # Mavzu kalit so'zlari
        mavzu_kalitlari = {
            "present_simple": [
                "present simple", "odat", "har kuni", "every day", 
                "do/does", "don't", "plays", "works", "studies"
            ],
            "to_be": [
                "to be", "am is are", "bo'lmoq", "was were", "will be"
            ],
            "past_simple": [
                "past simple", "o'tgan zamon", "edim", "edi", "-di", "yesterday"
            ],
            "future": [
                "future", "kelajak", "will", "bo'laman"
            ],
        }
        
        # Har bir mavzuni tekshirish
        for mavzu, kalitlar in mavzu_kalitlari.items():
            if any(kalit in savol_past for kalit in kalitlar):
                return mavzu
        
        return None

    # ============================================================================
    # 6.3 FAQAT INGLIZCHA QISMNI AJRATISH — YANGI FUNKSIYA! ✨
    # ============================================================================
    def faqat_inglizcha_qism(self, gap):
        """
        Gapdan faqat inglizcha qismni ajratib oladi.
        Tarjima qismini olib tashlaydi.
        
        Misol:
            "I am a student. Men talabaman." → "I am a student"
        
        Parametrlar:
            gap (str): Inglizcha + o'zbekcha gap
        
        Qaytaradi:
            str: Faqat inglizcha qism
        """
        # 1-USUL: Kirill harf topilguncha olamiz
        for i, char in enumerate(gap):
            # Kirill harflar diapazoni
            if '\u0400' <= char <= '\u04FF' or char in 'ўўққғғҳҳ':
                return gap[:i].strip()
        
        # 2-USUL: Agar kirill topilmasa, nuqtagacha olamiz
        if '.' in gap:
            parts = gap.split('.')
            # Birinchi qism inglizcha bo'lishi kerak
            if re.search(r'[a-zA-Z]', parts[0]):
                return parts[0].strip()
        
        # 3-USUL: Hech narsa topilmasa, to'g'ridan-to'g'ri qaytarish
        return gap.strip()

    # ============================================================================
    # 6.4 VEKTOR QIDIRUV — PROFESSIONAL
    # ============================================================================
    def qidiruv(self, savol):
        """
        PROFESSIONAL QIDIRUV:
        - Aniq mavzu mosligini tekshirish
        - AQILLI kontekst kengaytirish (faqat bir mavzudagi gaplar)
        - Vektor o'xshashligi bo'yicha reyting
        
        Parametrlar:
            savol (str): Foydalanuvchi savoli
        
        Qaytaradi:
            list: Natijalar ro'yxati (text, time, score, mavzu)
        """
        savol_norm = self.normalize_query(savol)
        
        # 1-QADAM: Mavzuni aniqlash
        aniqlangan_mavzu = self.aniqlash_mavzu(savol)
        
        # 2-QADAM: Vektor qidiruv
        savol_v = model.encode(savol_norm, convert_to_tensor=True)
        scores = util.cos_sim(savol_v, self.vektorlar)[0].clone()
        
        # 3-QADAM: Mavzuga ko'ra ballarni sozlash
        if aniqlangan_mavzu:
            for i, matn in enumerate(self.matnlar):
                matn_past = matn.lower()
                
                # Mavzuga oidlikni tekshirish
                mavzuga_oid = False
                if aniqlangan_mavzu == "present_simple":
                    mavzuga_oid = any(x in matn_past for x in [
                        "present simple", "odat", "har kuni", "every", 
                        "do", "does", "don't", "plays", "works", "studies"
                    ])
                elif aniqlangan_mavzu == "to_be":
                    mavzuga_oid = any(x in matn_past for x in [
                        "to be", "am", "is", "are", "bo'lmoq", "was", "were"
                    ])
                elif aniqlangan_mavzu == "past_simple":
                    mavzuga_oid = any(x in matn_past for x in [
                        "past", "o'tgan", "was", "were", "edi", "yesterday"
                    ])
                elif aniqlangan_mavzu == "future":
                    mavzuga_oid = any(x in matn_past for x in [
                        "future", "kelajak", "will", "bo'laman"
                    ])
                
                # Agar mavzuga oid bo'lsa, ballini 50% oshirish
                if mavzuga_oid:
                    original_score = scores[i].item()
                    scores[i] = min(original_score * 1.5, 1.0)
        
        # 4-QADAM: Eng yaxshi 3 ta natijani olish
        top_k = min(3, len(self.matnlar))
        top_results = torch.topk(scores, k=top_k)
        indices = top_results.indices.tolist()
        
        natijalar = []
        for idx in indices:
            score = scores[idx].item()
            
            # Ishonchlilik chegarasi (threshold)
            if score < 0.25:
                continue
            
            # 5-QADAM: AQILLI KONTEKST KENGAYTIRISH
            # Faqat bir xil mavzudagi qo'shni gaplarni olish
            kontekst_gaplar = [self.matnlar[idx]]
            
            # Oldingi gaplarni tekshirish
            for i in range(idx - 1, max(idx - 3, -1), -1):
                if i >= 0:
                    qoshni_gap = self.matnlar[i].lower()
                    
                    mavzuga_oid = False
                    if aniqlangan_mavzu == "present_simple":
                        mavzuga_oid = any(x in qoshni_gap for x in [
                            "present simple", "odat", "every", "do", "does", 
                            "plays", "works", "studies", "har kuni"
                        ])
                    elif aniqlangan_mavzu == "to_be":
                        mavzuga_oid = any(x in qoshni_gap for x in [
                            "to be", "am", "is", "are", "bo'lmoq", "was", "were"
                        ])
                    elif aniqlangan_mavzu == "past_simple":
                        mavzuga_oid = any(x in qoshni_gap for x in [
                            "past", "o'tgan", "was", "were", "edi"
                        ])
                    elif aniqlangan_mavzu == "future":
                        mavzuga_oid = any(x in qoshni_gap for x in [
                            "future", "kelajak", "will"
                        ])
                    
                    if mavzuga_oid:
                        kontekst_gaplar.insert(0, self.matnlar[i])
                    else:
                        break  # Boshqa mavzuga o'tdi, to'xtatish
            
            # Keyingi gaplarni tekshirish
            for i in range(idx + 1, min(idx + 3, len(self.matnlar))):
                qoshni_gap = self.matnlar[i].lower()
                
                mavzuga_oid = False
                if aniqlangan_mavzu == "present_simple":
                    mavzuga_oid = any(x in qoshni_gap for x in [
                        "present simple", "odat", "every", "do", "does", 
                        "plays", "works", "studies", "har kuni"
                    ])
                elif aniqlangan_mavzu == "to_be":
                    mavzuga_oid = any(x in qoshni_gap for x in [
                        "to be", "am", "is", "are", "bo'lmoq", "was", "were"
                    ])
                elif aniqlangan_mavzu == "past_simple":
                    mavzuga_oid = any(x in qoshni_gap for x in [
                        "past", "o'tgan", "was", "were", "edi"
                    ])
                elif aniqlangan_mavzu == "future":
                    mavzuga_oid = any(x in qoshni_gap for x in [
                        "future", "kelajak", "will"
                    ])
                
                if mavzuga_oid:
                    kontekst_gaplar.append(self.matnlar[i])
                else:
                    break  # Boshqa mavzuga o'tdi, to'xtatish
            
            # Kontekstni birlashtirish
            kengaytirilgan_matn = " ".join(kontekst_gaplar)
            
            natijalar.append({
                "text": kengaytirilgan_matn,
                "time": self.vaqtler[idx],
                "score": score,
                "exact_match": idx,
                "mavzu": aniqlangan_mavzu
            })
        
        return natijalar

    # ============================================================================
    # 6.5 JAVOBN FORMATLASH — AQILLI SHABLONLAR
    # ============================================================================
    def format_javob(self, natijalar, savol):
        """
        AQILLI JAVOB GENERATOR:
        - Mavzuni aniq aniqlash
        - Savol turiga qarab shablon
        - Samimiy tonus
        
        Parametrlar:
            natijalar (list): Qidiruv natijalari
            savol (str): Foydalanuvchi savoli
        
        Qaytaradi:
            str: Formatlangan javob
        """
        if not natijalar or natijalar[0]['score'] < 0.25:
            return None
        
        top = natijalar[0]
        savol_lower = savol.lower()
        aniqlangan_mavzu = top.get('mavzu')
        
        # Samimiy qo'shimchalar (random tanlanadi)
        samimiy_qo_shimchalar = [
            "😊", "👍", "🎯", "✨", "🌟",
            "Ajoyib savol!", "Tushunarli bo'ldimi?", 
            "Yana savollaringiz bormi?", "Birga o'rganamiz! 🚀"
        ]
        
        # Mavzuga qarab maxsus javob
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
            # Umumiy javob — savol turiga qarab
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
        
        # Ishonch darajasi indikatori
        if top['score'] > 0.8:
            shablon += "\n\n🎯 _Juda aniq javob topildi!_"
        elif top['score'] > 0.6:
            shablon += "\n\n⚠️ _Yaxshi javob, lekin boshqa manbalarga ham qarang._"
        
        # Samimiy qo'shimcha
        shablon += f"\n\n{random.choice(samimiy_qo_shimchalar)}"
        
        return shablon

    # ============================================================================
    # 6.6 ZAXIRA JAVOB — AGAR TOPILMASA
    # ============================================================================
    def get_fallback_javob(self):
        """
        AI topa olmasa, chiroyli rad etish javoblari.
        
        Qaytaradi:
            str: Zaxira javob
        """
        fallback_javoblar = [
            "🤔 Bu savol hozircha mening bilim doiramdan tashqari. Boshqacha so'zlab ko'rasizmi?",
            "📚 Bu haqda darslikda aniq ma'lumot topolmadim. Balki o'qituvchidan so'rash kerakdir?",
            "🚀 Men hali o'rganayapman! Bu savolni eslab qoldim, keyinroq javob berishga harakat qilaman.",
            "💭 Qiziqarli savol! Hozircha faqat darslikdagi mavzularga javob bera olaman.",
            "🙏 Kechirasiz, bu haqda ma'lumotim yo'q. Boshqa savol bering, albatta yordam beraman!"
        ]
        return random.choice(fallback_javoblar)

    # ============================================================================
    # 6.7 TEST UCHUN GAP TANLASH — YANGILANGAN! ✨
    # ============================================================================
    def test_gap_ol(self):
        """
        Test uchun FAQAT toza inglizcha gaplarni tanlash.
        Tarjima qismini avtomatik olib tashlaydi.
        
        Qaytaradi:
            dict: Test gap (text, time) yoki None
        """
        toza_gaplar = []
        
        for item in self.data:
            gap = item['text']
            
            # ✅ MUHIM: Faqat inglizcha qismni ajratib olish
            inglizcha = self.faqat_inglizcha_qism(gap)
            
            # Inglizcha qism yetarlicha uzunligini tekshirish
            if len(inglizcha) > 10 and len(inglizcha.split()) >= 3:
                # To be fe'li borligini tekshirish
                if re.search(r'\b(am|is|are|was|were)\b', inglizcha):
                    toza_gaplar.append({
                        "text": inglizcha,  # Faqat inglizcha qism!
                        "time": item['time']
                    })
        
        # Tasodifiy gap tanlash
        if toza_gaplar:
            return random.choice(toza_gaplar)
        
        return None

    # ============================================================================
    # 6.8 TEST JAVOBINI TEKSHIRISH
    # ============================================================================
    def tekshirish(self, user_javob, to_g_ri_javob):
        """
        Test javobini tekshirish.
        Katta-kichik harf va tinish belgilariga qaramaydi.
        
        Parametrlar:
            user_javob (str): Foydalanuvchi javobi
            to_g_ri_javob (str): To'g'ri javob
        
        Qaytaradi:
            tuple: (to'g'rimi, foiz)
        """
        # Tinish belgilari va katta-kichik harflarni olib tashlash
        user_clean = re.sub(r'[^\w\s]', '', user_javob.lower()).strip()
        correct_clean = re.sub(r'[^\w\s]', '', to_g_ri_javob.lower()).strip()
        
        # To'liq moslik
        if user_clean == correct_clean:
            return True, 1.0
        
        # So'zlar bo'yicha qisman moslik (Jaccard)
        user_words = set(user_clean.split())
        correct_words = set(correct_clean.split())
        
        if not correct_words:
            return False, 0.0
        
        overlap = len(user_words & correct_words) / len(correct_words)
        return overlap >= 0.8, overlap

    # ============================================================================
    # 6.9 DAVOM ETISH NIYATINI TUSHUNISH
    # ============================================================================
    def davom_etishni_tushun(self, javob):
        """
        Foydalanuvchi javobidan davom etish yoki to'xtash niyatini aniqlash.
        
        Parametrlar:
            javob (str): Foydalanuvchi javobi
        
        Qaytaradi:
            bool: Davom etish (True/False) yoki None (noaniq)
        """
        javob = javob.lower().strip()
        
        # DAVOM ETISH NIYATI
        davom_belgilari = [
            'ha', 'haa', 'albatta', 'davom', 'davom et', 'davom ettir',
            'yana', 'yana bitta', 'yana bir', 'ok', 'okay', 'mayli', 'boshladik',
            'yur', 'ketdik', 'ber', 'bering', 'tushundim', 'ready', 'go', 'next',
            'keyingisi', 'keyingi', 'test', 'sinab ko', 'sinab koramiz'
        ]
        
        # TO'XTASH NIYATI
        toxtash_belgilari = [
            'yo', 'yoq', 'bas', 'yetarli', 'yetar', 'to', 'toxta',
            'kerak emas', 'kerakemas', 'keyin', 'keyinroq', 'hozircha',
            'rahmat', 'raxmat', 'tashakkur', 'stop', 'no', 'finish', 'tamom',
            'bo', 'boldi', 'charchadim', 'dam olaman'
        ]
        
        # Kalit so'zlar bo'yicha tekshirish
        for belgi in davom_belgilari:
            if belgi in javob:
                return True
        for belgi in toxtash_belgilari:
            if belgi in javob:
                return False
        
        # Semantik qidiruv (agar kalit so'z topilmasa)
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
        
        # Agar aniqlab bo'lmasa, savolga qarab taxmin qilish
        if '?' in javob or 'nima' in javob or 'qanday' in javob:
            return None  # Noaniq, savol berayapti
        
        # Default: ijobiy deb hisoblaymiz (optimistik yondashuv)
        return True

    # ============================================================================
    # 6.10 TEST DAVOMI SAVOLI
    # ============================================================================
    def test_davom_etish_savoli(self):
        """
        Testdan keyin davom etish haqida savol.
        
        Qaytaradi:
            str: Tasodifiy savol
        """
        savollar = [
            "🔄 **Yana test yechamizmi?** (`ha` yoki `yo'q` deb yozing)",
            "🎯 **Bilimingizni yana sinab ko'ramizmi?** (`davom` yoki `yetarli`)",
            "✨ **Yana bir gapni tartiblab ko'rasizmi?** (`ha` / `yo'q`)",
            "🚀 **Keyingi testga o'tamizmi?** (`yur` yoki `to'xta`)"
        ]
        return random.choice(savollar)

# ================================================================================
# 💾 7. SESSION STATE — XOTIRA
# ================================================================================
def init_session():
    """
    Session state ni boshlang'ich holatga keltirish.
    Barcha o'zgaruvchilar shu funksiyada e'lon qilinadi.
    """
    # AI Ustozni yuklash
    if "ustoz" not in st.session_state:
        fayl_darsi = dars_faylini_oku("dars.txt")
        if fayl_darsi:
            st.session_state.ustoz = AI_Miya(fayl_darsi)
            st.success("✅ dars.txt fayli muvaffaqiyatli yuklandi!")
        else:
            st.session_state.ustoz = AI_Miya(NAMUNA_TRANSKRIPT)
            st.info("ℹ️ Namuna ma'lumotlar ishlatilmoqda (dars.txt topilmadi)")
    
    # Chat tarixi
    if "chat" not in st.session_state:
        st.session_state.chat = []
    
    # Xatolar ro'yxati
    if "xatolar" not in st.session_state:
        st.session_state.xatolar = []
    
    # Ball tizimi
    if "ball" not in st.session_state:
        st.session_state.ball = 0
    
    # Chat holati (oddiy, test_tekshir, test_davom_so'ra, taklif)
    if "holat" not in st.session_state:
        st.session_state.holat = "oddiy"
    
    # Test uchun tanlangan gap
    if "savol_gapi" not in st.session_state:
        st.session_state.savol_gapi = None
    
    # Welcome message — birinchi kirishda
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

# Session state ni boshlash
init_session()

# ================================================================================
# 🎛️ 8. SIDEBAR — O'QUVCHI PROFILI
# ================================================================================
with st.sidebar:
    st.markdown('<p class="sidebar-header">📊 O\'quvchi Profili</p>', unsafe_allow_html=True)
    
    # Ball va daraja
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🏆 Ball", st.session_state.ball)
    with col2:
        daraja = st.session_state.ball // 10
        st.metric("📈 Daraja", f"{daraja}-level")
    
    st.markdown("---")
    
    # Dars ma'lumoti
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
    
    # JSON fayl yuklash (qo'shimcha)
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
    
    # Xatolar daftari
    st.subheader("⚠️ Xatolar daftari")
    if st.session_state.xatolar:
        unikal_xatolar = list(set(st.session_state.xatolar))[-5:]
        for xato in unikal_xatolar:
            st.warning(f"❌ {xato[:50]}...")
    else:
        st.info("✨ Xatolar yo'q. Barakalla!")
    
    st.markdown("---")
    
    # Reset tugmasi
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

# ================================================================================
# 💬 9. ASOSIY CHAT INTERFEYSI
# ================================================================================

# Welcome Banner — faqat chat bo'sh bo'lsa
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

# Chat tarixini ko'rsatish
chat_container = st.container()
with chat_container:
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("video_time") is not None:
                st.caption(f"🎥 Darsning **{m['video_time']}**-soniyasida")

# Chat input — foydalanuvchi savol yozadi
prompt = st.chat_input("Savolingizni yozing... (masalan: 'to be haqida ma'lumot ber' yoki 'test')")

if prompt:
    # Foydalanuvchi xabarini xotiraga saqlash
    st.session_state.chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    ustoz = st.session_state.ustoz
    javob = ""
    video_time = None
    
    # ============================================================================
    # 9.1 TEST DAVOM ETTIRISHNI SO'RASH
    # ============================================================================
    if st.session_state.holat == "test_davom_so'ra":
        davom_etish = ustoz.davom_etishni_tushun(prompt)
        
        if davom_etish is True:
            # Foydalanuvchi davom etmoqchi — yangi test berish
            test_gap = ustoz.test_gap_ol()
            if test_gap:
                st.session_state.savol_gapi = test_gap
                
                # ✅ MUHIM: Faqat inglizcha qismni olamiz va tinish belgilarini tozalaymiz
                inglizcha_matn = ustoz.faqat_inglizcha_qism(test_gap['text'])
                inglizcha_matn = re.sub(r'[.!?]+$', '', inglizcha_matn)
                sozlar = inglizcha_matn.split()
                random.shuffle(sozlar)
                
                javob = f"📝 **Yangi vazifa:** Quyidagi so'zlardan to'g'ri inglizcha gap tuzing:\n\n"
                javob += f"`{' / '.join(sozlar)}`\n\n"
                javob += "_✍️ Javobingizni yozing, men tekshiraman!_"
                st.session_state.holat = "test_tekshir"
            else:
                javob = "⚠️ Test uchun boshqa gaplar topilmadi. Boshqa mavzuga o'tamizmi?"
                st.session_state.holat = "oddiy"
                
        elif davom_etish is False:
            # Foydalanuvchi to'xtamoqchi — xulosa chiqarish
            javob = f"✅ **Ajoyib!** Bugun {st.session_state.ball} ball to'pladingiz! 🎉\n\n"
            javob += "💡 **Maslahat:** Xato qilgan gaplaringizni sidebar'dagi 'Xatolar daftari' dan takrorlang.\n\n"
            javob += "👋 Yana savollaringiz bo'lsa, har doim shu yerdaman!"
            st.session_state.holat = "oddiy"
            
        else:
            # Noaniq javob — tushuntirib so'rash
            javob = "🤔 Tushunmadim, aniqroq yozib bersangiz:\n\n"
            javob += "- `ha` yoki `davom` — yana test beraman\n"
            javob += "- `yo'q` yoki `yetarli` — testni to'xtatamiz\n\n"
            javob += "Siz nima deysiz? 😊"
    
    # ============================================================================
    # 9.2 TEST TEKSHIRISH
    # ============================================================================
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
        
        # Testdan keyin davom etishni so'rash
        javob += f"\n\n---\n{ustoz.test_davom_etish_savoli()}"
        st.session_state.holat = "test_davom_so'ra"
    
    # ============================================================================
    # 9.3 TEST BOSHLASH
    # ============================================================================
    elif prompt.lower().strip() in ['ha', 'test', 'ok', 'mayli', 'boshladik', "sinab ko'ramiz", "yur"]:
        test_gap = ustoz.test_gap_ol()
        if test_gap:
            st.session_state.savol_gapi = test_gap
            
            # ✅ MUHIM: Faqat inglizcha qismni olamiz va tinish belgilarini tozalaymiz
            inglizcha_matn = ustoz.faqat_inglizcha_qism(test_gap['text'])
            inglizcha_matn = re.sub(r'[.!?]+$', '', inglizcha_matn)
            sozlar = inglizcha_matn.split()
            random.shuffle(sozlar)
            
            javob = f"📝 **Vazifa:** Quyidagi so'zlardan to'g'ri inglizcha gap tuzing:\n\n"
            javob += f"`{' / '.join(sozlar)}`\n\n"
            javob += "_✍️ Javobingizni yozing, men tekshiraman!_"
            st.session_state.holat = "test_tekshir"
        else:
            javob = "⚠️ Test uchun inglizcha gap topilmadi. Boshqa savol bering."
    
    # ============================================================================
    # 9.4 ODDIY SAVOL — RAG QIDIRUV
    # ============================================================================
    else:
        natijalar = ustoz.qidiruv(prompt)
        
        if natijalar:
            top_natija = natijalar[0]
            video_time = top_natija['time']
            
            formatted = ustoz.format_javob(natijalar, prompt)
            javob = formatted if formatted else f"🤖 {top_natija['text']}"
            
            # Test taklifi
            javob += "\n\n---\n🧐 **Bilimingizni sinab ko'ramizmi?** (`test` deb yozing)"
            st.session_state.holat = "taklif"
        else:
            # Fallback javob — chiroyli rad etish
            javob = ustoz.get_fallback_javob()
            javob += "\n\n💡 **Maslahat**:\n"
            javob += "- Boshqa so'zlar bilan so'rang\n"
            javob += "- Mavzuni aniqroq yozing\n"
            javob += "- Yoki `test` deb bilimingizni sinab ko'ring"
    
    # Assistant javobini chiqarish
    with st.chat_message("assistant"):
        st.markdown(javob)
        if video_time is not None:
            st.caption(f"🎥 Bu ma'lumot videoning **{video_time}**-soniyasida")
    
    # Xotiraga saqlash
    st.session_state.chat.append({
        "role": "assistant",
        "content": javob,
        "video_time": video_time
    })
    
    # Sahifani yangilash
    st.rerun()

# ================================================================================
# 🦶 10. FOOTER
# ================================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: small; padding: 20px;'>
    🎓 <b>Al-Ustoz v3.0 Professional</b> | Aqlli ta'lim platformasi<br>
    📄 <b>dars.txt</b> fayli asosida ishlayapti | 
    💡 Savol bering yoki test yeching
</div>
""", unsafe_allow_html=True)

# ================================================================================
# 📋 11. YO'RIQNOMA — EXPANDER
# ================================================================================
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
    - Kelajakda shu soniyadan video boshlanadi
    
    ### 🧠 AI Qanday Ishlaydi?
    - **Mavzu aniqlash:** Savoldan mavzuni aniqlaydi (Present Simple, To Be, etc.)
    - **Kontekst kengaytirish:** Faqat bir mavzudagi qo'shni gaplar birlashtiriladi
    - **Aqlli shablonlar:** Savol turiga qarab javob formati o'zgaradi
    - **Semantik qidiruv:** Ma'no bo'yicha qidiradi, faqat kalit so'z emas
    - **Aqlli test davomi:** Testdan keyin davom etishni so'raydi
    - **Faqat inglizcha test:** Tarjima aralashmaydi, faqat inglizcha so'zlar
    """)

# ================================================================================
# 🏁 KOD TUGADI
# ================================================================================