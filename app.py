import streamlit as st
import json
import os
import datetime
import calendar
import re
import random
import requests
import pandas as pd
import plotly.express as px
import xml.etree.ElementTree as ET
from groq import Groq
from supabase import create_client, Client
from streamlit_lottie import st_lottie
from streamlit_javascript import st_javascript
from datetime import timedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y PWA
# ==========================================
st.set_page_config(page_title="NutriAI | Chef Inteligente", page_icon="🌿", layout="wide")

st.components.v1.html("""
<script>
    var manifest = {
        "name": "NutriAI Chef", "short_name": "NutriAI",
        "start_url": window.location.pathname, "display": "standalone",
        "background_color": "#FDFBF7", "theme_color": "#10B981",
        "icons":[{"src": "https://cdn-icons-png.flaticon.com/512/3565/3565418.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]
    };
    var blob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
    var manifestURL = URL.createObjectURL(blob);
    var link = document.createElement('link'); link.rel = 'manifest'; link.href = manifestURL;
    document.head.appendChild(link);
</script>
""", height=0, width=0)

# ==========================================
# CSS PREMIUM (Light Theme / Soft Neumorphism)
# ==========================================
st.markdown("""
    <style>
    .stApp { background: #FDFBF7 !important; color: #1E293B !important; }
    .block-container { background: #FFFFFF !important; border-radius: 20px !important; padding-top: 3rem !important; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05) !important; border: 1px solid rgba(0, 0, 0, 0.03) !important; }[data-testid="stSidebar"] { background: #F8F9FA !important; border-right: 1px solid rgba(0, 0, 0, 0.05) !important; }
    h1, h2, h3, h4, p, label, .stMarkdown, span, div, strong, li { color: #1E293B !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div { background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 10px !important; transition: all 0.3s ease !important; }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within, div[data-baseweb="select"] > div:focus-within { border-color: #10B981 !important; box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important; }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, div[data-baseweb="select"] div { color: #1E293B !important; }[data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.02) !important; }
    [data-testid="stExpander"] summary { background-color: #F8F9FA !important; border-radius: 12px !important; color: #1E293B !important; }
    .stButton > button { background: linear-gradient(135deg, #10B981, #3B82F6) !important; color: white !important; border: none !important; border-radius: 12px !important; box-shadow: 0 6px 20px rgba(16, 185, 129, 0.25) !important; font-weight: 700 !important; transition: all 0.3s ease !important; }
    .stButton > button * { color: white !important; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(59, 130, 246, 0.35) !important; }
    .stDownloadButton > button, button[kind="secondaryFormSubmit"], button[kind="secondary"] { background: #F1F5F9 !important; border: 1px solid #CBD5E1 !important; color: #334155 !important; box-shadow: none !important; }
    button[kind="secondary"] * { color: #334155 !important; }
    button[kind="secondary"]:hover { background: #E2E8F0 !important; border-color: #94A3B8 !important; }
    button[key^="del_"] { background: transparent !important; box-shadow: none !important; color: #EF4444 !important; font-size: 1.2rem !important; }
    button[key^="del_"]:hover { transform: scale(1.1) !important; }
    .brand-logo { font-family: 'Georgia', serif; font-size: 3.5rem; font-weight: 900; text-align: center; margin-bottom: 0px; background: -webkit-linear-gradient(45deg, #10B981, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .golden-card { background: linear-gradient(135deg, #FFD700 0%, #F59E0B 100%); padding: 4px; border-radius: 20px; margin-bottom: 20px; box-shadow: 0 10px 30px rgba(245, 158, 11, 0.2); }
    .golden-card-content { background: #FFFFFF; border-radius: 18px; padding: 25px; text-align: center; }
    .hero-emoji { text-align: center; font-size: 70px; margin-bottom: -10px; }
    .nutrition-label { background: #FFFFFF; color: #000000; padding: 20px; border-radius: 12px; border: 2px solid #E2E8F0; max-width: 350px; font-family: Arial, sans-serif; }
    .nutrition-label * { color: #000000 !important; }
    .nutrition-label h2 { border-bottom: 4px solid #000000; padding-bottom: 5px; }
    .nut-row { display: flex; justify-content: space-between; border-top: 1px solid #CBD5E1; padding: 6px 0; }
    .nut-row.thick { border-top: 3px solid #000000; }
    .nut-bold { font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ANIMACIONES LOTTIE
# ==========================================
@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_cooking = load_lottieurl("https://lottie.host/81a5fcbd-3c46-4c74-a698-b8ce1aa33a2a/P2lT3zTjK1.json")

# ==========================================
# INYECCIONES JAVASCRIPT Y CONTROL DE SESIÓN
# ==========================================
if st.session_state.get("do_login_js", False):
    usr = st.session_state.current_username
    code = f"window.parent.localStorage.setItem('nutri_username', '{usr}'); window.parent.sessionStorage.removeItem('nutri_username');" if st.session_state.keep_in else f"window.parent.sessionStorage.setItem('nutri_username', '{usr}'); window.parent.localStorage.removeItem('nutri_username');"
    st.components.v1.html(f"<script>{code}</script>", height=0, width=0)
    st.session_state.do_login_js = False

if st.session_state.get("do_logout_js", False):
    st.components.v1.html("<script>window.parent.localStorage.removeItem('nutri_username'); window.parent.sessionStorage.removeItem('nutri_username');</script>", height=0, width=0)
    st.session_state.do_logout_js = False

if "auth_checked" not in st.session_state: st.session_state.auth_checked = False
if "current_username" not in st.session_state: st.session_state.current_username = None
if "current_page" not in st.session_state: st.session_state.current_page = "home"

if not st.session_state.auth_checked:
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
    with col_s2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if lottie_cooking: st_lottie(lottie_cooking, height=300, key="splash_anim")
        phrases =["Encendiendo los fogones...", "Preparando tu cocina inteligente...", "Afilando los cuchillos...", "Calentando las sartenes..."]
        st.markdown(f"<h2 style='text-align:center;'>{random.choice(phrases)}</h2>", unsafe_allow_html=True)
        
    js_val = st_javascript('window.localStorage.getItem("nutri_username") || window.sessionStorage.getItem("nutri_username") || "NONE"')
    
    if js_val == 0: st.stop()
    elif js_val == "NONE":
        st.session_state.auth_checked = True
        st.rerun()
    else:
        st.session_state.current_username = js_val
        st.session_state.auth_checked = True
        st.rerun()

def logout():
    st.session_state.current_username = None
    st.session_state.current_page = "home"
    st.session_state.step = "input"
    st.session_state.do_logout_js = True

def go_home():
    st.session_state.current_page = "home"
    st.session_state.step = "input"
    st.rerun()

# ==========================================
# CONEXIÓN A SUPABASE & FUNCIONES AUXILIARES
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    return create_client(url, key)

supabase = init_supabase()

def get_user_data(username):
    if not username: return None
    res = supabase.table("app_users_2").select("*").eq("username", username).execute()
    return res.data[0] if res.data else None

def update_user_data(username, data_dict):
    if username: supabase.table("app_users_2").update(data_dict).eq("username", username).execute()

# --- NUEVAS FUNCIONES DE CALENDARIO Y CÁLCULO SILENCIOSO ---
def get_meal_type_and_color(hour=None):
    if hour is None: hour = datetime.datetime.now().hour
    if 6 <= hour < 11.5: return "Desayuno", "#F59E0B" # Naranja
    elif 11.5 <= hour < 16: return "Almuerzo", "#10B981" # Verde
    elif 16 <= hour < 19.5: return "Snacks/Merienda", "#8B5CF6" # Morado
    else: return "Cena", "#3B82F6" # Azul

def add_to_meal_calendar(username, date_str, food_name, macros=None):
    user = get_user_data(username)
    calendar_db = user.get("meal_calendar") or {}
    
    # Cálculo silencioso si es manual
    if not macros:
        sys = "Estima los macros de este alimento. Solo devuelve JSON exacto: {'calories': 100, 'protein': 2, 'fat': 0, 'carbs': 20}"
        parsed = groq_generic_json(sys, f"Alimento: {food_name}")
        macros = parsed if parsed else {'calories': 0, 'protein': 0, 'fat': 0, 'carbs': 0}
        
    m_type, m_color = get_meal_type_and_color()
    
    if date_str not in calendar_db:
        calendar_db[date_str] =[]
        
    calendar_db[date_str].append({
        "type": m_type, "color": m_color, "food": food_name,
        "calories": macros.get('calories',0), "protein": macros.get('protein',0), 
        "fat": macros.get('fat',0), "carbs": macros.get('carbs',0)
    })
    
    update_user_data(username, {"meal_calendar": calendar_db})

# ==========================================
# FUNCIONES IA (GROQ) Y EXTRACCIÓN
# ==========================================
def call_ai_json(prompt, expected_format_hint, lang_code, u_prof, avail_ing="", avoid_tdy="", num_recipes=3):
    client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))
    system_prompt = f"""
    You are a Michelin-star Executive Chef and Clinical Nutritionist.
    Your client is {u_prof['name']}. Profile: {u_prof['age']} y/o, {u_prof['weight']} kg, {u_prof['height']} cm, Gender: {u_prof['gender']}.
    Main goal: "{u_prof['goals']}". Restrictions: "{u_prof['restrictions']}".
    [DYNAMIC GENERATION] Generate exactly {num_recipes} recipe options.
    [CHEF'S RECOMMENDATION] Tag exactly ONE recipe with `"is_chefs_recommendation": true`.
    [COHERENCE FILTER] Formulate ONLY realistic, delicious, and culturally sensible dishes. Do not invent bizarre combinations.
    """
    if avail_ing: system_prompt += f"\n[GOLDEN RULE] Recipes MUST be based EXCLUSIVELY on: {avail_ing}."
    if avoid_tdy: system_prompt += f"\n[STRICT PROHIBITION] Under NO circumstances include: {avoid_tdy}."

    final_prompt = system_prompt + f"""
    \nEXPECTED JSON FORMAT:
    {expected_format_hint}
    
    🔴[CRITICAL LANGUAGE DIRECTIVE] 🔴
    CRITICAL LANGUAGE RULE: The JSON KEYS MUST ALWAYS BE IN ENGLISH (e.g., 'recipe_name', 'nutritionist_note', 'region', 'instructions', 'name', 'description', 'time', 'difficulty'). 
    However, the JSON VALUES MUST BE STRICTLY, COMPLETELY, AND NATURALLY TRANSLATED TO {lang_code.upper()}. 
    """

    try:
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": final_prompt}, {"role": "user", "content": prompt}], response_format={"type": "json_object"}, temperature=0.4)
        return json.loads(response.choices[0].message.content)
    except: return None

def groq_generic_json(system_prompt, user_prompt):
    client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))
    try:
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], response_format={"type": "json_object"}, temperature=0.3)
        return json.loads(response.choices[0].message.content)
    except: return None

def extract_number(val_str):
    match = re.search(r'\d+', str(val_str))
    return int(match.group()) if match else 0

def format_recipe_for_download(recipe, t_dict):
    text = f"=== {recipe.get('recipe_name', recipe.get('name', '')).upper()} ===\n🌍 Origen/Estilo: {recipe.get('region', 'Global')}\n\n--- {t_dict['ingredients'].upper()} ---\n"
    for ing in recipe.get("ingredients",[]): text += f"• {ing.get('qty', '')} de {ing.get('item', '')}\n"
    text += f"\n--- {t_dict['instructions'].upper()} ---\n"
    for i, step in enumerate(recipe.get("instructions",[])): text += f"{i+1}. {step}\n"
    m = recipe.get('macros', {})
    text += f"\n--- MACROS ---\nCalorías: {m.get('calories', '0')} | Proteína: {m.get('protein', '0g')} | Grasas: {m.get('total_fat', '0g')} | Carbohidratos: {m.get('total_carbs', '0g')}\n"
    return text

@st.cache_data(ttl=timedelta(days=1), show_spinner=False)
def fetch_daily_healthy_recipes(lang_code):
    url = "https://news.google.com/rss/search?q=recetas+saludables+faciles+rapidas&hl=es&gl=ES&ceid=ES:es"
    raw_results =[]
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.text)
        for item in root.findall('./channel/item'):
            title = item.find('title').text
            link = item.find('link').text
            clean_title = title.split(" - ")[0] 
            raw_results.append({"title": clean_title, "url": link, "summary": clean_title})
            if len(raw_results) >= 15: break
        random.shuffle(raw_results)
        raw_results = raw_results[:4]
    except: return[]
    if not raw_results: return[]
        
    sys_prompt = f"""
    You are a Michelin-star Chef and an expert culinary copywriter.
    I am providing you with a JSON list of REAL daily recipes extracted from Google News.
    Your task:
    1. Rewrite the 'title' to make it sound irresistible.
    2. Write a mouth-watering 2-line 'summary'.
    3. TRANSLATE both entirely into {lang_code.upper()}.
    4. Extract and keep the EXACT original 'url' intact.
    Return STRICTLY JSON format: {{"recipes":[{{"title": "...", "summary": "...", "url": "..."}}]}}
    """
    try:
        parsed = groq_generic_json(sys_prompt, "REAL GOOGLE NEWS RECIPES:\n" + json.dumps(raw_results))
        if parsed and "recipes" in parsed and len(parsed["recipes"]) > 0: return parsed["recipes"]
    except: pass
    return raw_results

# ==========================================
# SISTEMA MULTIDIOMA Y TEXTOS
# ==========================================
TRANSLATIONS = {
    "🇪🇸 Español": {
        "lang_code": "Spanish", "title": "¡Hola {name}! ¿Qué cocinamos hoy? 🍲", "subtitle": "Tu ecosistema inteligente de nutrición y cocina.",
        "dash_mod1": "Cocina Mágica", "dash_mod2": "Mi Compra", "dash_mod3": "Mi Calendario", "dash_mod4": "Análisis IA",
        "assistant_msg": "¿Qué hay en la despensa? ¡Hagamos magia!", "avail_ing_label": "Ingredientes disponibles hoy", "avoid_today_label": "¿Algo que evitar hoy?", "find_btn": "Buscar Recetas Mágicas",
        "analyzing": "El Chef está analizando...", "here_options": "Opciones para ti:", "diff": "Dificultad", "time": "Tiempo", "health": "Salud",
        "cook_btn": "Cocinar {}", "loading_recipe": "Calculando macros exactos...", "start_over": "← Empezar de Nuevo", "note": "Nota del Nutricionista:",
        "ingredients": "🛒 Ingredientes", "save_fav": "⭐ Guardar en Favoritos", "saved": "¡Guardado!", "instructions": "👨‍🍳 Preparación", "adjust_title": "⚖️ Ajustar Macros",
        "adjust_sub": "¿Necesitas otras cantidades?", "adjust_ph": "Ej: 'Añade 20g de proteína'", "recalc_btn": "Recalcular", "recalculating": "Ajustando receta...",
        "profile": "👤 Mi Perfil", "update_prof": "Actualizar Perfil", "prof_updated": "¡Perfil actualizado!", "favs": "⭐ Favoritos", "no_favs": "Aún no hay favoritos.",
        "logout": "Cerrar Sesión", "news_title": "📰 Tendencias Nutricionales", "cook_this": "Ver receta 🍳", "download_btn": "⬇️ Descargar",
        "auth_app_name": "NutriAI 🌿", "auth_subtitle": "Tu chef y nutricionista personal impulsado por IA.", "tab_login": "🔑 Iniciar Sesión", "tab_register": "📝 Registrarse", "tab_recover": "🆘 Recuperar PIN",
        "username_label_login": "Usuario", "pin_label_login": "PIN", "login_btn": "Entrar a la Cocina 🚀", "login_error": "Usuario o PIN incorrectos.",
        "reg_section1": "1. Datos de Acceso", "create_user_label": "Usuario", "create_pin_label": "PIN", "security_question_label": "Pregunta",
        "security_options":["¿Nombre de tu primera mascota?", "¿Ciudad de nacimiento?"], "security_answer_label": "Respuesta",
        "reg_section2": "2. Perfil Clínico", "name_label": "Nombre", "age_label": "Edad", "weight_label": "Peso (kg)", "height_label": "Altura (cm)", "gender_label": "Género", "gender_options":["Masculino", "Femenino", "Otro"],
        "reg_section3": "3. Objetivos", "goals_label": "Objetivo", "rest_label": "Restricciones", "create_account_btn": "Crear Cuenta", "username_taken": "Usuario en uso.",
        "account_created": "¡Cuenta creada!", "fill_required": "Rellena los campos.", "forgot_pin_text": "¿Olvidaste tu PIN?", "search_user_label": "Usuario",
        "search_user_btn": "Buscar", "user_found": "Usuario encontrado.", "user_not_found": "Usuario no encontrado.", "recover_question_prefix": "Pregunta:", "your_answer_label": "Respuesta", "new_pin_label": "Nuevo PIN",
        "change_pin_btn": "Cambiar PIN", "pin_changed_success": "¡PIN cambiado!", "wrong_answer": "Incorrecta.", "current_weight_label": "Peso Actual",
        "profile_goals_label": "Objetivos", "profile_restrictions_label": "Restricciones", 
        "back_home": "🏠 Volver al Menú", "shop_title": "Lista de la Compra", "type_food": "Escribe un alimento suelto...", "add_to_list": "Añadir a la lista",
        "shop_list_title": "Tu Inventario", "clear_list": "🗑️ Vaciar Lista", "mac_cal": "Calorías", "mac_pro": "Proteínas", "mac_fat": "Grasas", "mac_car": "Carbohidratos",
        "nut_facts": "Información Nutricional", "nut_cal": "Calorías", "nut_tfat": "Grasa Total", "nut_sfat": "Grasa Saturada", "nut_sod": "Sodio", "nut_tcarb": "Carbohidratos Totales", "nut_fib": "Fibra", "nut_sug": "Azúcares", "nut_pro": "Proteína"
    },
    "🇬🇧 English": {
        "lang_code": "English", "title": "Hi {name}! What are we cooking today? 🍲", "subtitle": "Your smart nutrition ecosystem.",
        "dash_mod1": "Magic Kitchen", "dash_mod2": "My Groceries", "dash_mod3": "My Calendar", "dash_mod4": "AI Analysis",
        "assistant_msg": "What's in the pantry?", "avail_ing_label": "Available ingredients", "avoid_today_label": "Anything to avoid?", "find_btn": "Find Magic Recipes",
        "analyzing": "Analyzing...", "here_options": "Options:", "diff": "Difficulty", "time": "Time", "health": "Health",
        "cook_btn": "Cook {}", "loading_recipe": "Calculating macros...", "start_over": "← Start Over", "note": "Nutritionist Note:",
        "ingredients": "🛒 Ingredients", "save_fav": "⭐ Save Fav", "saved": "Saved!", "instructions": "👨‍🍳 Instructions", "adjust_title": "⚖️ Adjust Macros",
        "adjust_sub": "Need different targets?", "adjust_ph": "e.g. 'Add 20g protein'", "recalc_btn": "Recalculate", "recalculating": "Adjusting...",
        "profile": "👤 Profile", "update_prof": "Update", "prof_updated": "Updated!", "favs": "⭐ Favs", "no_favs": "No favs yet.",
        "logout": "Logout", "news_title": "📰 Nutrition Trends", "cook_this": "Cook this 🍳", "download_btn": "⬇️ Download",
        "auth_app_name": "NutriAI 🌿", "auth_subtitle": "AI Personal Chef", "tab_login": "🔑 Log In", "tab_register": "📝 Register", "tab_recover": "🆘 Recover",
        "username_label_login": "Username", "pin_label_login": "PIN", "login_btn": "Enter 🚀", "login_error": "Error.", 
        "reg_section1": "1. Access", "create_user_label": "Username", "create_pin_label": "PIN", "security_question_label": "Question",
        "security_options":["Pet?", "City?"], "security_answer_label": "Answer",
        "reg_section2": "2. Profile", "name_label": "Name", "age_label": "Age", "weight_label": "Weight", "height_label": "Height", "gender_label": "Gender", "gender_options":["Male", "Female", "Other"],
        "reg_section3": "3. Goals", "goals_label": "Goals", "rest_label": "Restrictions", "create_account_btn": "Create", "username_taken": "Taken.",
        "account_created": "Created!", "fill_required": "Fill all.", "forgot_pin_text": "Forgot PIN?", "search_user_label": "Username",
        "search_user_btn": "Search", "user_found": "Found.", "user_not_found": "Not found.", "recover_question_prefix": "Q:", "your_answer_label": "Answer", "new_pin_label": "New PIN",
        "change_pin_btn": "Change", "pin_changed_success": "Changed!", "wrong_answer": "Wrong.", "current_weight_label": "Weight",
        "profile_goals_label": "Goals", "profile_restrictions_label": "Restrictions", 
        "back_home": "🏠 Back to Home", "shop_title": "Shopping List", "type_food": "Type an item...", "add_to_list": "Add to list",
        "shop_list_title": "Your Groceries", "clear_list": "🗑️ Clear List", "mac_cal": "Calories", "mac_pro": "Protein", "mac_fat": "Fats", "mac_car": "Carbs",
        "nut_facts": "Nutrition Facts", "nut_cal": "Calories", "nut_tfat": "Total Fat", "nut_sfat": "Saturated Fat", "nut_sod": "Sodium", "nut_tcarb": "Total Carbohydrate", "nut_fib": "Fiber", "nut_sug": "Sugars", "nut_pro": "Protein"
    }
}

if "selected_lang" not in st.session_state: st.session_state.selected_lang = "🇪🇸 Español"

def handle_language_change():
    new_lang_code = TRANSLATIONS[st.session_state.selected_lang]["lang_code"]
    with st.spinner(f"Traduciendo / Translating..."):
        if st.session_state.get("options"):
            sys_p = f"Translate values to {new_lang_code.upper()}, keep English keys."
            res = groq_generic_json(sys_p, json.dumps({"options": st.session_state.options}))
            if res and "options" in res: st.session_state.options = res["options"]
        if st.session_state.get("full_recipe"):
            sys_p = f"Translate values to {new_lang_code.upper()}, keep English keys."
            res = groq_generic_json(sys_p, json.dumps(st.session_state.full_recipe))
            if res: st.session_state.full_recipe = res

cols_top = st.columns([1, 6, 1])
with cols_top[2]: 
    st.selectbox("", options=list(TRANSLATIONS.keys()), key="selected_lang", label_visibility="collapsed", on_change=handle_language_change)
    
t = TRANSLATIONS[st.session_state.selected_lang]
lang_code = t["lang_code"]

# ==========================================
# PANTALLA DE AUTENTICACIÓN
# ==========================================
if not st.session_state.current_username:
    st.markdown(f"<h1 class='brand-logo'>{t['auth_app_name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:#64748B;'>{t['auth_subtitle']}</p>", unsafe_allow_html=True)
    
    col_auth1, col_auth2, col_auth3 = st.columns([1, 2, 1])
    with col_auth2:
        tab1, tab2, tab3 = st.tabs([t["tab_login"], t["tab_register"], t["tab_recover"]])
        with tab1:
            log_user = st.text_input(t["username_label_login"], key="log_user")
            log_pin = st.text_input(t["pin_label_login"], type="password", key="log_pin")
            keep_in = st.checkbox("Mantener sesión", value=True)
            if st.button(t["login_btn"], type="primary", use_container_width=True):
                res = supabase.table("app_users_2").select("*").eq("username", log_user).eq("pin", log_pin).execute()
                if res.data:
                    st.session_state.current_username = log_user
                    st.session_state.keep_in = keep_in
                    st.session_state.do_login_js = True
                    st.rerun()
                else: st.error(t["login_error"])
                    
        with tab2:
            st.markdown(f"**{t['reg_section1']}**")
            reg_user = st.text_input(t["create_user_label"], key="reg_user")
            reg_pin = st.text_input(t["create_pin_label"], type="password", key="reg_pin")
            reg_sq = st.selectbox(t["security_question_label"], t["security_options"])
            reg_sa = st.text_input(t["security_answer_label"])
            
            st.markdown(f"**{t['reg_section2']}**")
            reg_name = st.text_input(t["name_label"])
            col1, col2, col3 = st.columns(3)
            reg_age = col1.number_input(t["age_label"], min_value=10, max_value=100, step=1, value=25)
            reg_weight = col2.number_input(t["weight_label"], min_value=30.0, max_value=200.0, step=0.1, value=70.0)
            reg_height = col3.number_input(t["height_label"], min_value=100, max_value=250, step=1, value=170)
            reg_gender = st.selectbox(t["gender_label"], t["gender_options"])
            
            st.markdown(f"**{t['reg_section3']}**")
            reg_goals = st.text_area(t["goals_label"])
            reg_rest = st.text_input(t["rest_label"])
            
            if st.button(t["create_account_btn"], type="primary", use_container_width=True):
                if reg_user and reg_pin and reg_sa and reg_name:
                    check = supabase.table("app_users_2").select("username").eq("username", reg_user).execute()
                    if check.data: st.error(t["username_taken"])
                    else:
                        # ACTUALIZADO: Añadimos 'meal_calendar' al esquema de nuevos usuarios
                        new_user = {"username": reg_user, "pin": reg_pin, "security_question": reg_sq, "security_answer": reg_sa.lower(), "name": reg_name, "age": reg_age, "weight": reg_weight, "height": reg_height, "gender": reg_gender, "goals": reg_goals, "restrictions": reg_rest, "favorites":[], "daily_logs":{}, "weekly_planner":{}, "shopping_list":[], "meal_calendar":{}}
                        supabase.table("app_users_2").insert(new_user).execute()
                        st.session_state.current_username = reg_user
                        st.session_state.keep_in = True
                        st.session_state.do_login_js = True
                        st.success(t["account_created"])
                        st.rerun()
                else: st.warning(t["fill_required"])
        
        with tab3:
            rec_user = st.text_input(t["search_user_label"], key="rec_user")
            if st.button(t["search_user_btn"]):
                res = supabase.table("app_users_2").select("security_question").eq("username", rec_user).execute()
                if res.data:
                    st.session_state.recover_user = rec_user
                    st.session_state.recover_q = res.data[0]["security_question"]
                    st.success(t["user_found"])
                else: st.error(t["user_not_found"])
                    
            if "recover_user" in st.session_state:
                st.info(f"{t['recover_question_prefix']} **{st.session_state.recover_q}**")
                rec_ans = st.text_input(t["your_answer_label"])
                new_pin = st.text_input(t["new_pin_label"], type="password")
                if st.button(t["change_pin_btn"], use_container_width=True):
                    res = supabase.table("app_users_2").select("security_answer").eq("username", st.session_state.recover_user).execute()
                    if res.data and res.data[0]["security_answer"] == rec_ans.lower():
                        supabase.table("app_users_2").update({"pin": new_pin}).eq("username", st.session_state.recover_user).execute()
                        st.success(t["pin_changed_success"])
                        del st.session_state.recover_user
                    else: st.error(t["wrong_answer"])
    st.stop()

# ==========================================
# CARGAR PERFIL DEL USUARIO ACTIVO
# ==========================================
user_profile = get_user_data(st.session_state.current_username)
if not user_profile:
    logout()
    st.rerun()

for key in["step", "options", "selected_option", "full_recipe", "avail_ing", "avoid_tdy"]:
    if key not in st.session_state: st.session_state[key] = None if key in["options", "selected_option", "full_recipe"] else ("input" if key == "step" else "")

# ==========================================
# SIDEBAR REDISEÑADA
# ==========================================
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👨‍🍳 Chef {user_profile['name']}</h2>", unsafe_allow_html=True)

    with st.expander(t["profile"], expanded=False):
        upd_weight = st.number_input(t["current_weight_label"], value=float(user_profile.get("weight",70)))
        upd_goals = st.text_area(t["profile_goals_label"], value=user_profile.get("goals",""))
        upd_rest = st.text_input(t["profile_restrictions_label"], value=user_profile.get("restrictions",""))
        if st.button(t["update_prof"], use_container_width=True):
            update_user_data(user_profile["username"], {"weight":upd_weight,"goals":upd_goals,"restrictions":upd_rest})
            st.success(t["prof_updated"])
            st.rerun()

    st.divider()
    with st.expander(t.get("news_title", "📰 Tendencias Nutricionales"), expanded=True):
        news_items = fetch_daily_healthy_recipes(lang_code)
        if news_items:
            for news in news_items:
                r_title = news.get('title', 'Receta Saludable')
                r_summary = news.get('summary', '')[:120] + "..."
                r_url = news.get('url', '#')
                st.markdown(f"""
                <div style="background: #FFFFFF; padding:12px; border-radius:10px; margin-bottom:12px; border:1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                    <h4 style="margin:0;font-size:14px;font-weight:700;color:#1E293B;line-height:1.2;">{r_title}</h4>
                    <p style="font-size:12px;margin-top:6px;margin-bottom:8px;line-height:1.4;color:#475569;">{r_summary}</p>
                    <a href="{r_url}" target="_blank" style="display:inline-block; padding:4px 0px; font-size:12px;color:#10B981;font-weight:800;text-decoration:none;">{t.get("cook_this", "Ver receta 🍳")} →</a>
                </div>
                """, unsafe_allow_html=True)
        else: st.warning("No se pudieron cargar las noticias hoy.")
        if st.button("🔄 Actualizar", use_container_width=True):
            fetch_daily_healthy_recipes.clear()
            st.rerun()
            
    st.divider()
    if st.button(t["logout"], type="secondary", use_container_width=True): logout()

# ==========================================
# RUTEO DE PÁGINAS (DASHBOARD REDISEÑADO)
# ==========================================
if st.session_state.current_page == "home":
    st.markdown("""
    <style>[data-testid="column"] div.stButton > button { min-height: 220px !important; border-radius: 24px !important; font-size: 26px !important; font-weight: 800 !important; color: #1E293B !important; background-color: #FFFFFF !important; background-image: none !important; box-shadow: 0 10px 40px rgba(0,0,0,0.06) !important; border: 2px solid #E2E8F0 !important; transition: all 0.3s ease !important; background-repeat: no-repeat !important; background-position: center top 35px !important; background-size: 70px !important; padding-top: 100px !important; }[data-testid="column"] div.stButton > button:hover { transform: translateY(-8px) !important; box-shadow: 0 20px 50px rgba(16,185,129,0.15) !important; border: 2px solid #10B981 !important; }
    [data-testid="column"]:nth-of-type(1) div.stButton:nth-of-type(1) button { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2310b981' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2l3 6 6 1-4 4 1 6-6-3-6 3 1-6-4-4 6-1z'/%3E%3C/svg%3E") !important; }
    [data-testid="column"]:nth-of-type(1) div.stButton:nth-of-type(2) button { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23f59e0b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='4' width='18' height='18' rx='2' ry='2'/%3E%3Cline x1='16' y1='2' x2='16' y2='6'/%3E%3Cline x1='8' y1='2' x2='8' y2='6'/%3E%3Cline x1='3' y1='10' x2='21' y2='10'/%3E%3C/svg%3E") !important; }
    [data-testid="column"]:nth-of-type(2) div.stButton:nth-of-type(1) button { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%233b82f6' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='9' cy='21' r='1'/%3E%3Ccircle cx='20' cy='21' r='1'/%3E%3Cpath d='M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6'/%3E%3C/svg%3E") !important; }
    [data-testid="column"]:nth-of-type(2) div.stButton:nth-of-type(2) button { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ef4444' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z'/%3E%3C/svg%3E") !important; }
    @media (max-width: 768px) { [data-testid="column"] div.stButton > button { min-height: 180px !important; font-size: 22px !important; margin-bottom: 10px; } }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<h1 class='brand-logo'>NutriAI</h1><p style='text-align:center; font-size:1.2rem; color:#64748B;'>{t['subtitle']}</p><br>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t["dash_mod1"], use_container_width=True): st.session_state.current_page = "mod1"; st.rerun()
        if st.button(t["dash_mod3"], use_container_width=True): st.session_state.current_page = "mod3"; st.rerun()
    with c2:
        if st.button(t["dash_mod2"], use_container_width=True): st.session_state.current_page = "mod2"; st.rerun()
        if st.button(t["dash_mod4"], use_container_width=True): st.session_state.current_page = "mod4"; st.rerun()

# ==========================================
# MÓDULO 1: COCINA INTELIGENTE
# ==========================================
elif st.session_state.current_page == "mod1":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()

    if st.session_state.step in ["input", "options"]:
        st.markdown(f"#### 👨‍🍳 {t['assistant_msg']}")
        available_ingredients = st.text_area(t["avail_ing_label"], placeholder="Ej: Pechuga de pollo, espinacas...", height=100)
        avoid_today = st.text_input("🚫 " + t["avoid_today_label"])
        
        if st.button(t["find_btn"], type="primary", use_container_width=True):
            if available_ingredients:
                st.session_state.avail_ing = available_ingredients
                st.session_state.avoid_tdy = avoid_today
                
                ing_count = len([x for x in re.split(r',|\sy\s|\sand\s|\set\s|\n', available_ingredients) if x.strip()])
                n_recipes = 2 if ing_count <= 4 else (3 if ing_count <= 8 else 4)
                
                lottie_placeholder = st.empty()
                with lottie_placeholder.container():
                    st.markdown("<br>", unsafe_allow_html=True)
                    if lottie_cooking: st_lottie(lottie_cooking, height=200, key="loading_anim_1")
                    st.markdown(f"<h3 style='text-align:center;'>{t['analyzing']}</h3>", unsafe_allow_html=True)
                
                prompt = f"Generate {n_recipes} recipe options strictly using the available ingredients provided."
                format_hint = """{ "options":[ { "name": "Nombre de receta", "hero_emoji": "🥘", "difficulty": "Media/Fácil", "time": "20 min", "health_score": 9, "description": "Breve descripción", "is_chefs_recommendation": true } ] }"""
                res = call_ai_json(prompt, format_hint, lang_code, user_profile, available_ingredients, avoid_today, num_recipes=n_recipes)
                lottie_placeholder.empty()
                
                if res and "options" in res:
                    res["options"].sort(key=lambda x: x.get("is_chefs_recommendation", False), reverse=True)
                    st.session_state.options = res["options"]
                    st.session_state.step = "options"
                    st.rerun()

    if st.session_state.step == "options" and st.session_state.options:
        st.divider()
        st.subheader(t["here_options"])
        for i, opt in enumerate(st.session_state.options):
            recipe_name = opt.get('name', opt.get('recipe_name', 'Receta'))
            if opt.get("is_chefs_recommendation", False):
                st.markdown(f"""
                <div class="golden-card">
                    <div class="golden-card-content">
                        <span style="color:#B45309; font-weight:900; letter-spacing:2px; font-size:14px;">RECOMENDACIÓN ESTRELLA</span>
                        <h1 style="font-size: 55px; margin: 5px 0;">{opt.get('hero_emoji', '🍽️')}</h1>
                        <h2 style="margin: 0; color: #1E293B;">{recipe_name}</h2>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"<h1 style='text-align:center; font-size:40px; margin:0;'>{opt.get('hero_emoji', '🍽️')}</h1><h3 style='text-align:center;'>{recipe_name}</h3>", unsafe_allow_html=True)
            
            st.caption(f"**{t['diff']}:** {opt.get('difficulty','')} | **{t['time']}:** {opt.get('time','')} | **{t['health']}:** {opt.get('health_score','')}/10")
            st.write(opt.get('description', ''))
            
            if st.button(t["cook_btn"].format(""), key=f"btn_cook_{i}", use_container_width=True):
                st.session_state.selected_option = opt
                st.session_state.step = "recipe_loading"
                st.rerun()
            st.write("---")

    if st.session_state.step == "recipe_loading":
        lottie_placeholder = st.empty()
        with lottie_placeholder.container():
            if lottie_cooking: st_lottie(lottie_cooking, height=200, key="loading_anim_2")
            st.markdown(f"<h3 style='text-align:center;'>{t['loading_recipe']}</h3>", unsafe_allow_html=True)
        
        safe_name = st.session_state.selected_option.get('name', st.session_state.selected_option.get('recipe_name', 'la receta seleccionada'))
        prompt = f"Write the complete and detailed recipe for '{safe_name}'."
        format_hint = """{ "recipe_name": "Nombre", "region": "Estilo", "hero_emoji": "🥘", "ingredients_emojis": "🍅", "nutritionist_note": "Nota", "health_badges":[{"icon": "🟢", "label": "Sano", "type": "positive"}], "macros": { "calories": "450 kcal", "total_fat": "15g", "saturated_fat": "3g", "sodium": "400mg", "total_carbs": "30g", "fiber": "6g", "sugars": "5g", "protein": "40g" }, "ingredients":[{"item": "Ingrediente", "qty": "200g"}], "instructions":["1. Paso 1"] }"""
        res = call_ai_json(prompt, format_hint, lang_code, user_profile, st.session_state.avail_ing, st.session_state.avoid_tdy)
        lottie_placeholder.empty()
        
        if res:
            st.session_state.full_recipe = res
            st.session_state.step = "recipe_view"
            st.rerun()

    if st.session_state.step == "recipe_view" and st.session_state.full_recipe:
        recipe = st.session_state.full_recipe
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(t["start_over"], use_container_width=True):
                st.session_state.step, st.session_state.options, st.session_state.full_recipe = "input", None, None
                st.rerun()
        with col_btn2:
            st.download_button(label=t["download_btn"], data=format_recipe_for_download(recipe, t), file_name=f"{recipe.get('recipe_name', 'receta')}.txt", mime="text/plain", use_container_width=True)

        st.markdown(f"<p class='hero-emoji'>{recipe.get('hero_emoji', '🍽️')}</p><h2 style='text-align:center;'>{recipe.get('recipe_name', '')}</h2><h4 style='text-align:center; color:#64748B;'>🌍 {recipe.get('region', 'Global')}</h4>", unsafe_allow_html=True)
        st.info(f"**{t['note']}** {recipe.get('nutritionist_note', '')}")
        st.divider()
        
        m = recipe.get('macros', {})
        c_label, c_chart = st.columns(2)
        with c_label:
            st.markdown(f"""
            <div class="nutrition-label">
                <h2>{t.get('nut_facts', 'Nutrition Facts')}</h2>
                <div class="nut-row thick"><span class="nut-bold">{t.get('nut_cal', 'Calories')}</span> <span class="nut-bold">{m.get('calories', '0')}</span></div>
                <div class="nut-row"><span class="nut-bold">{t.get('nut_tfat', 'Total Fat')}</span> {m.get('total_fat', '0g')}</div>
                <div class="nut-row"><span class="nut-bold">{t.get('nut_tcarb', 'Carbs')}</span> {m.get('total_carbs', '0g')}</div>
                <div class="nut-row thick"><span class="nut-bold">{t.get('nut_pro', 'Protein')}</span> <span class="nut-bold">{m.get('protein', '0g')}</span></div>
            </div>
            """, unsafe_allow_html=True)
        with c_chart:
            macro_df = pd.DataFrame({"Macro":[t.get("mac_pro", "Proteínas"), t.get("mac_fat", "Grasas"), t.get("mac_car", "Carbohidratos")], "Gramos":[extract_number(m.get('protein', '0g')), extract_number(m.get('total_fat', '0g')), extract_number(m.get('total_carbs', '0g'))]})
            if macro_df['Gramos'].sum() > 0:
                fig = px.pie(macro_df, values='Gramos', names='Macro', hole=0.55, color_discrete_sequence=['#EF4444', '#F59E0B', '#3B82F6'])
                fig.update_traces(textfont_color='#FFFFFF', textinfo='percent+label')
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
        
        # --- INTEGRACIÓN: GUARDAR RECETA DIRECTAMENTE EN EL CALENDARIO ---
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button(t["save_fav"], use_container_width=True):
                favs = user_profile.get("favorites",[])
                favs.append({"name": recipe.get("recipe_name", ""), "calories": m.get('calories', '0'), "protein": m.get('protein', '0g')})
                update_user_data(user_profile["username"], {"favorites": favs})
                st.toast(t["saved"])
        with c_act2:
            m_type, _ = get_meal_type_and_color()
            if st.button(f"📅 Añadir al Calendario ({m_type})", type="primary", use_container_width=True):
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                m_data = {
                    "calories": extract_number(m.get('calories', '0')), 
                    "protein": extract_number(m.get('protein', '0')), 
                    "fat": extract_number(m.get('total_fat', '0')), 
                    "carbs": extract_number(m.get('total_carbs', '0'))
                }
                add_to_meal_calendar(user_profile["username"], today_str, recipe.get("recipe_name", "Receta"), m_data)
                st.toast(f"¡Guardado en tu calendario como {m_type}!", icon="✅")
                
        with st.expander("🛒 " + t["ingredients"], expanded=True):
            for ing in recipe.get("ingredients",[]): st.markdown(f"- **{ing.get('qty', '')}** {ing.get('item', '')}")
        with st.expander("👨‍🍳 " + t["instructions"], expanded=True):
            for step in recipe.get("instructions",[]): st.write(f"{step}")

# ==========================================
# MÓDULO 2: MI COMPRA
# ==========================================
elif st.session_state.current_page == "mod2":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    st.markdown(f"<h2 style='text-align:center;'>{t['shop_title']}</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col1: new_item = st.text_input("", placeholder=t["type_food"], label_visibility="collapsed")
    with col2: add_pressed = st.button(t["add_to_list"], type="primary", use_container_width=True)

    if add_pressed and new_item:
        with st.spinner("Organizando..."):
            parsed = groq_generic_json(f"Clasifica el alimento y tradúcelo al {lang_code}. Categorías: cat_produce, cat_dairy, cat_white_meat, cat_red_meat, cat_seafood, cat_pantry, cat_other. Solo JSON: {{\"category\":\"cat_x\", \"translated_item\": \"Nombre\"}}", f"Food: {new_item}")
            category = parsed.get("category", "cat_other") if parsed else "cat_other"
            item_name = parsed.get("translated_item", new_item).capitalize() if parsed else new_item.capitalize()
            shop_list = user_profile.get("shopping_list",[])
            shop_list.append({"item": item_name, "category": category})
            update_user_data(user_profile["username"], {"shopping_list": shop_list})
            st.rerun()

    st.subheader(t["shop_list_title"])
    shop_list = user_profile.get("shopping_list",[])
    if not shop_list:
        st.info("🛒 Tu lista está vacía.")
    else:
        categorized = {}
        for idx,obj in enumerate(shop_list):
            cat = obj.get("category","cat_other")
            if cat not in categorized: categorized[cat] = []
            categorized[cat].append((idx,obj["item"]))

        for cat in["cat_produce", "cat_dairy", "cat_white_meat", "cat_red_meat", "cat_seafood", "cat_pantry", "cat_other"]:
            if cat in categorized:
                with st.expander(f"{t.get(cat,cat)} ({len(categorized[cat])})", expanded=True):
                    for idx,item in categorized[cat]:
                        c1,c2 = st.columns([6,1])
                        c1.markdown(f"<p style='margin-top:6px;'>• {item}</p>", unsafe_allow_html=True)
                        if c2.button("🗑️", key=f"del_{idx}"):
                            shop_list.pop(idx)
                            update_user_data(user_profile["username"], {"shopping_list":shop_list})
                            st.rerun()

        if st.button(t["clear_list"], type="secondary"):
            update_user_data(user_profile["username"], {"shopping_list":[]})
            st.rerun()

# ==========================================
# MÓDULO 3: CALENDARIO NUTRICIONAL INTERACTIVO
# ==========================================
elif st.session_state.current_page == "mod3":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    st.markdown(f"<h2 style='text-align:center;'>📅 {t.get('dash_mod3', 'Mi Calendario')}</h2>", unsafe_allow_html=True)
    
    # Manejo de estado del calendario
    if "cal_date" not in st.session_state: 
        st.session_state.cal_date = datetime.date.today()
    if "cal_view" not in st.session_state:
        st.session_state.cal_view = "Semanal"

    # Controles de navegación superior
    cc1, cc2, cc3, cc4 = st.columns([1, 2, 2, 1])
    with cc1:
        if st.button("⬅️ Ant.", use_container_width=True):
            delta = 7 if st.session_state.cal_view == "Semanal" else 30
            st.session_state.cal_date -= datetime.timedelta(days=delta)
            st.rerun()
    with cc2:
        st.markdown(f"<h4 style='text-align:center;'>{st.session_state.cal_date.strftime('%B %Y').capitalize()}</h4>", unsafe_allow_html=True)
    with cc3:
        st.session_state.cal_view = st.selectbox("Vista", ["Semanal", "Mensual"], label_visibility="collapsed", index=0 if st.session_state.cal_view == "Semanal" else 1)
    with cc4:
        if st.button("Sig. ➡️", use_container_width=True):
            delta = 7 if st.session_state.cal_view == "Semanal" else 30
            st.session_state.cal_date += datetime.timedelta(days=delta)
            st.rerun()

    calendar_db = user_profile.get("meal_calendar") or {}
    
    # Renderizado UI del Calendario
    if st.session_state.cal_view == "Semanal":
        start_of_week = st.session_state.cal_date - datetime.timedelta(days=st.session_state.cal_date.weekday())
        days =[start_of_week + datetime.timedelta(days=i) for i in range(7)]
        day_names =["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        
        cols = st.columns(7)
        for i, d in enumerate(days):
            d_str = d.strftime("%Y-%m-%d")
            with cols[i]:
                # Estilo de la cabecera del día
                bg = "#E2E8F0" if d == datetime.date.today() else "#F8F9FA"
                st.markdown(f"<div style='text-align:center; background:{bg}; padding:10px; border-radius:10px; margin-bottom:10px;'><b>{day_names[i]}</b><br>{d.day}</div>", unsafe_allow_html=True)
                
                # Renderizamos las tarjetas de las comidas para este día
                meals = calendar_db.get(d_str,[])
                for m in meals:
                    st.markdown(f"""
                    <div style='background:{m.get("color", "#CBD5E1")}15; border-left:4px solid {m.get("color", "#CBD5E1")}; padding:8px; border-radius:6px; margin-bottom:8px; font-size:12px;'>
                        <strong style='color:{m.get("color", "#334155")};'>{m.get("type", "Comida")}</strong><br>
                        <span style='color:#334155; font-weight: 500;'>{m.get("food", "")}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
    elif st.session_state.cal_view == "Mensual":
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdatescalendar(st.session_state.cal_date.year, st.session_state.cal_date.month)
        
        # Cabecera de días de la semana
        c_cols = st.columns(7)
        for i, d_name in enumerate(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]):
            c_cols[i].markdown(f"<div style='text-align:center; font-weight:bold; color:#64748B;'>{d_name}</div>", unsafe_allow_html=True)
            
        # Cuadrícula del mes
        for week in month_days:
            w_cols = st.columns(7)
            for i, d in enumerate(week):
                d_str = d.strftime("%Y-%m-%d")
                opacity = "1" if d.month == st.session_state.cal_date.month else "0.3"
                bg = "#E2E8F0" if d == datetime.date.today() else "#FFFFFF"
                
                html_cell = f"<div style='background:{bg}; border:1px solid #F1F5F9; border-radius:8px; padding:5px; min-height:80px; opacity:{opacity}; margin-bottom:10px;'>"
                html_cell += f"<div style='text-align:right; font-size:12px; color:#94A3B8; font-weight:bold;'>{d.day}</div>"
                
                # Mini-pastillas de colores para indicar comidas registradas
                meals = calendar_db.get(d_str,[])
                for m in meals:
                    html_cell += f"<div style='background:{m.get('color', '#CBD5E1')}; width:100%; height:6px; border-radius:3px; margin-top:3px;' title='{m.get('food','')}'></div>"
                
                html_cell += "</div>"
                w_cols[i].markdown(html_cell, unsafe_allow_html=True)

    st.divider()
    st.subheader("➕ Añadir Comida Manual")
    with st.form("add_meal_form", clear_on_submit=True):
        c_date, c_food = st.columns([1, 3])
        sel_date = c_date.date_input("Día", value=datetime.date.today())
        inp_food = c_food.text_input("¿Qué has comido?", placeholder="Ej: 1 Manzana y un café cortado")
        sub = st.form_submit_button("Guardar en el Calendario", type="primary")
        
        if sub and inp_food:
            with st.spinner("Registrando y calculando macros en la sombra..."):
                add_to_meal_calendar(user_profile["username"], sel_date.strftime("%Y-%m-%d"), inp_food)
                st.rerun()

# ==========================================
# MÓDULO 4: DASHBOARD CLÍNICO DE IA
# ==========================================
elif st.session_state.current_page == "mod4":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    st.markdown(f"<h2 style='text-align:center;'>🩺 Dashboard Clínico Avanzado</h2>", unsafe_allow_html=True)
    
    # Selector de periodo temporal
    periodo = st.radio("Selecciona el período a analizar:", ["Hoy", "Esta Semana", "Este Mes"], horizontal=True)
    
    calendar_db = user_profile.get("meal_calendar") or {}
    today = datetime.date.today()
    
    target_dates =[]
    if periodo == "Hoy":
        target_dates = [today.strftime("%Y-%m-%d")]
    elif periodo == "Esta Semana":
        start = today - datetime.timedelta(days=today.weekday())
        target_dates =[(start + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    elif periodo == "Este Mes":
        target_dates =[(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)] # Últimos 30 días
        
    t_cal, t_pro, t_fat, t_car = 0, 0, 0, 0
    all_foods =[]
    
    # Recolección silenciosa de datos desde el calendario
    for d_str in target_dates:
        for meal in calendar_db.get(d_str,[]):
            t_cal += meal.get("calories", 0)
            t_pro += meal.get("protein", 0)
            t_fat += meal.get("fat", 0)
            t_car += meal.get("carbs", 0)
            all_foods.append(f"{meal.get('type')}: {meal.get('food')}")
            
    # Dashboard visual de Macros Acumulados
    st.markdown("### 📊 Resumen de Macros del Período")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"🔥 {t.get('mac_cal', 'Calorías')} Totales", f"{t_cal} kcal")
    c2.metric(f"🍗 {t.get('mac_pro', 'Proteínas')}", f"{t_pro} g")
    c3.metric(f"🥑 {t.get('mac_fat', 'Grasas')}", f"{t_fat} g")
    c4.metric(f"🍞 {t.get('mac_car', 'Carbos')}", f"{t_car} g")
    
    st.divider()
    
    # IA Evaluadora Médica
    if not all_foods:
        st.info("No hay datos de comidas registrados en el Calendario para este período. ¡Ve al Módulo 3 para registrar lo que comes!")
    else:
        if st.button("🧠 Generar Informe Clínico de IA", type="primary", use_container_width=True):
            lottie_placeholder = st.empty()
            with lottie_placeholder.container():
                if lottie_cooking: st_lottie(lottie_cooking, height=150)
                st.markdown("<h4 style='text-align:center;'>Evaluando tu salud y hábitos...</h4>", unsafe_allow_html=True)
                
            sys_eval = f"""
            Eres un Médico Nutricionista Clínico y Científico de Datos. Tu paciente es {user_profile['name']} ({user_profile['age']} años, {user_profile['weight']}kg, Objetivo: {user_profile['goals']}, Restricciones: {user_profile['restrictions']}).
            Periodo evaluado: {periodo}.
            Macros Totales Registrados: Calorías: {t_cal} kcal | Proteínas: {t_pro}g | Grasas: {t_fat}g | Carbos: {t_car}g.
            Lista de alimentos consumidos en el periodo: {', '.join(all_foods)}.
            
            Realiza un informe médico exhaustivo, profesional y motivador. USA FORMATO MARKDOWN ESTRICTO y lenguaje {lang_code.upper()}.
            Estructura OBLIGATORIA:
            1. **Puntuación Nutricional (Score del 0 al 100)**: Evalúa la limpieza y equilibrio de su dieta.
            2. **Análisis de Macros**: ¿Están alineados con su objetivo físico y su edad/peso?
            3. **Calidad de Ingredientes**: Analiza qué tan limpia es la dieta según los alimentos registrados.
            4. **Puntos Fuertes**: Qué está haciendo extremadamente bien.
            5. **Advertencias Médicas**: Peligros detectados (excesos de azúcar, falta de proteína, déficits, alimentos problemáticos).
            6. **Recomendación Estrella**: El cambio dietético exacto y accionable que debe aplicar a partir de mañana.
            
            Devuelve SOLO JSON con formato: {{"markdown_report": "tu contenido aquí"}}
            """
            
            report = groq_generic_json(sys_eval, "Genera el reporte médico exhaustivo.")
            lottie_placeholder.empty()
            
            if report and "markdown_report" in report:
                st.markdown(f"""
                <div style="background: #FFFFFF; padding: 30px; border-radius: 15px; border: 2px solid #E2E8F0; box-shadow: 0 10px 30px rgba(0,0,0,0.05);">
                    {report['markdown_report']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Hubo un error al generar el análisis. Inténtalo de nuevo en unos segundos.")
