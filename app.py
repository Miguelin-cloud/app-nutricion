import streamlit as st
import json
import os
import datetime
import re
import random
import requests
import pandas as pd
import plotly.express as px
from groq import Groq
from supabase import create_client, Client
from streamlit_lottie import st_lottie
from streamlit_javascript import st_javascript
from duckduckgo_search import DDGS
from datetime import timedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y PWA
# ==========================================
st.set_page_config(page_title="NutriAI | Chef Inteligente", page_icon="🌿", layout="wide")

# Inyección PWA
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

    if ('serviceWorker' in navigator) {
        var swCode = "self.addEventListener('fetch', function(e) {});";
        var swBlob = new Blob([swCode], {type: 'application/javascript'});
        var swUrl = URL.createObjectURL(swBlob);
        navigator.serviceWorker.register(swUrl).catch(function(err){});
    }

    var meta1 = document.createElement('meta'); meta1.name = "apple-mobile-web-app-capable"; meta1.content = "yes"; document.head.appendChild(meta1);
    var meta2 = document.createElement('meta'); meta2.name = "apple-mobile-web-app-status-bar-style"; meta2.content = "default"; document.head.appendChild(meta2);
</script>
""", height=0, width=0)

# ==========================================
# CSS PREMIUM (Light Theme / Soft Neumorphism)
# ==========================================
st.markdown("""
    <style>
    /* 🔥 Fondo Claro y Acogedor */
    .stApp {
        background: #FDFBF7 !important;
        color: #1E293B !important;
    }
    
    /* 🔥 Contenedor Principal (Tarjetas Blancas) */
    .block-container {
        background: #FFFFFF !important;
        border-radius: 20px !important;
        padding-top: 3rem !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05) !important;
        border: 1px solid rgba(0, 0, 0, 0.03) !important;
    }
    
    /* 🔥 BARRA LATERAL REDISEÑADA */
    [data-testid="stSidebar"] {
        background: #F8F9FA !important;
        border-right: 1px solid rgba(0, 0, 0, 0.05) !important;
    }
    
    /* ALTO CONTRASTE CRÍTICO PARA TODOS LOS TEXTOS */
    h1, h2, h3, h4, p, label, .stMarkdown, span, div, strong, li {
        color: #1E293B !important;
    }

    /* Ajuste de inputs y textareas (Limpios y Blancos) */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important; 
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    div[data-baseweb="input"] > div:focus-within, 
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
    }
    div[data-baseweb="input"] input, 
    div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] div { 
        color: #1E293B !important; 
    }
    
    /* Expanders (Acordeones) */[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.02) !important;
    }[data-testid="stExpander"] summary {
        background-color: #F8F9FA !important;
        border-radius: 12px !important;
        color: #1E293B !important;
    }

    /* 🔥 Botones Principales (Verde/Azul Vibrante) */
    .stButton > button {
        background: linear-gradient(135deg, #10B981, #3B82F6) !important;
        color: white !important; 
        border: none !important; 
        border-radius: 12px !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.25) !important; 
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button * { color: white !important; }
    .stButton > button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.35) !important; 
    }

    /* Botones Secundarios */
    .stDownloadButton > button, button[kind="secondaryFormSubmit"], button[kind="secondary"] {
        background: #F1F5F9 !important; 
        border: 1px solid #CBD5E1 !important; 
        color: #334155 !important;
        box-shadow: none !important;
    }
    button[kind="secondary"] * { color: #334155 !important; }
    button[kind="secondary"]:hover { background: #E2E8F0 !important; border-color: #94A3B8 !important; }

    /* Botones de eliminar (Lista de compra) */
    button[key^="del_"] { background: transparent !important; box-shadow: none !important; color: #EF4444 !important; font-size: 1.2rem !important; }
    button[key^="del_"]:hover { transform: scale(1.1) !important; }

    /* Logo Principal */
    .brand-logo { 
        font-family: 'Georgia', serif; font-size: 3.5rem; font-weight: 900; 
        text-align: center; margin-bottom: 0px; 
        background: -webkit-linear-gradient(45deg, #10B981, #3B82F6); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    }

    /* Golden Card (Rediseñada para Light Theme) */
    .golden-card {
        background: linear-gradient(135deg, #FFD700 0%, #F59E0B 100%);
        padding: 4px; border-radius: 20px; margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(245, 158, 11, 0.2);
    }
    .golden-card-content {
        background: #FFFFFF; border-radius: 18px; padding: 25px; text-align: center;
    }

    .hero-emoji { text-align: center; font-size: 70px; margin-bottom: -10px; }

    /* Nutrition Label (Mantenido estético sobre blanco) */
    .nutrition-label {
        background: #FFFFFF; color: #000000; padding: 20px; border-radius: 12px;
        border: 2px solid #E2E8F0; max-width: 350px; font-family: Arial, sans-serif;
    }
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

def append_to_daily_log(username, entry_data):
    user = get_user_data(username)
    logs = user.get("daily_logs") or {}
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    if today not in logs: logs[today] = []
    logs[today].append(entry_data)
    update_user_data(username, {"daily_logs": logs})

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

    # Directriz CRÍTICA Modificada: Llaves en Inglés siempre, Valores 100% Traducidos.
    final_prompt = system_prompt + f"""
    \nEXPECTED JSON FORMAT:
    {expected_format_hint}
    
    🔴[CRITICAL LANGUAGE DIRECTIVE] 🔴
    CRITICAL LANGUAGE RULE: The JSON KEYS MUST ALWAYS BE IN ENGLISH (e.g., 'recipe_name', 'nutritionist_note', 'region', 'instructions', 'name', 'description', 'time', 'difficulty'). 
    However, the JSON VALUES MUST BE STRICTLY, COMPLETELY, AND NATURALLY TRANSLATED TO {lang_code.upper()}. 
    Do NOT leave any value in English if the requested language is different. Pay special attention to translating the 'region' (e.g., 'Mediterranean' to 'Mediterránea'), the 'nutritionist_note', the 'ingredients', and every step in 'instructions'. NEVER MIX LANGUAGES IN VALUES.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": final_prompt}, 
                {"role": "user", "content": prompt}
            ], 
            response_format={"type": "json_object"}, 
            temperature=0.4
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

def groq_generic_json(system_prompt, user_prompt):
    client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], 
            response_format={"type": "json_object"}, 
            temperature=0.3
        )
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
    # 1. Conexión DIRECTA a las revistas de cocina (Infalible, sin bloqueos de buscador)
    rss_feeds =[
        "https://www.vitonica.com/categoria/recetas-saludables/feed",
        "https://www.directoalpaladar.com/categoria/recetas-saludables/feed"
    ]
    
    raw_results =[]
    for url in rss_feeds:
        try:
            # Nos conectamos como si fuéramos un navegador para extraer el XML de las noticias
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=5)
            
            # Separamos cada noticia de la revista
            items = res.text.split('<item>')
            
            # Cogemos las 3 recetas más recientes de cada revista
            for item in items[1:4]: 
                # Extraemos el Título
                t_match = re.search(r'<title>(.*?)</title>', item, re.IGNORECASE | re.DOTALL)
                title = t_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if t_match else "Receta Saludable"
                
                # Extraemos el Enlace Real de la página
                l_match = re.search(r'<link>(.*?)</link>', item, re.IGNORECASE | re.DOTALL)
                link = l_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if l_match else "#"
                
                # Extraemos la descripción y le borramos las etiquetas de HTML o imágenes
                d_match = re.search(r'<description>(.*?)</description>', item, re.IGNORECASE | re.DOTALL)
                desc = d_match.group(1).replace('<![CDATA[', '').replace(']]>', '').strip() if d_match else "Deliciosa opción sana."
                desc_clean = re.sub(r'<[^>]+>', '', desc)[:150] # Limpia todo y corta a 150 caracteres
                
                raw_results.append({"title": title, "url": link, "summary": desc_clean})
        except Exception as e:
            continue
            
    # Mezclamos las recetas de ambas revistas y nos quedamos con las 4 mejores
    random.shuffle(raw_results)
    raw_results = raw_results[:4]
    
    if not raw_results:
        return[] # Solo se devolverá vacío si el servidor web se queda sin internet
        
    # 2. PROMPT DE LA IA (Traduce y mejora los textos obtenidos directamente de las revistas)
    sys_prompt = f"""
    You are a Michelin-star Chef and an expert culinary copywriter.
    I am providing you with a JSON list of REAL daily recipes extracted directly from famous culinary websites.
    
    Your task:
    1. Rewrite the 'title' to make it sound irresistible, premium, and highly nutritious.
    2. Rewrite the 'summary' into a mouth-watering 2-line description highlighting its health benefits.
    3. TRANSLATE both the title and the summary entirely into {lang_code.upper()}. This is mandatory.
    4. Extract and keep the EXACT original 'url' intact.
    
    You must reply STRICTLY with a JSON object in this exact format:
    {{
        "recipes":[
            {{"title": "Translated Catchy Title", "summary": "Translated 2-line description", "url": "https://original-link.com"}}
        ]
    }}
    """
    
    user_prompt = "REAL RSS RECIPES:\n" + json.dumps(raw_results)
    
    try:
        # Llamamos a Groq con los resultados reales
        parsed = groq_generic_json(sys_prompt, user_prompt)
        if parsed and "recipes" in parsed and len(parsed["recipes"]) > 0:
            return parsed["recipes"]
    except Exception:
        pass
        
    # Sistema de seguridad: Si la IA tarda o falla, muestra las recetas originales en español.
    return raw_results
# ==========================================
# SISTEMA MULTIDIOMA Y TEXTOS
# ==========================================
TRANSLATIONS = {
    "🇪🇸 Español": {
        "lang_code": "Spanish",
        "title": "¡Hola {name}! ¿Qué cocinamos hoy? 🍲", "subtitle": "Tu ecosistema inteligente de nutrición y cocina.",
        "dash_mod1": "Cocina Mágica", "dash_mod2": "Mi Compra", "dash_mod3": "Mis Menús", "dash_mod4": "Mi Salud",
        "assistant_msg": "¿Qué hay en la despensa? ¡Hagamos magia!", "avail_ing_label": "Ingredientes disponibles hoy", "avoid_today_label": "¿Algo que evitar hoy?", "find_btn": "Buscar Recetas Mágicas",
        "analyzing": "El Chef está analizando...", "here_options": "Opciones para ti:", "diff": "Dificultad", "time": "Tiempo", "health": "Salud",
        "cook_btn": "Cocinar {}", "loading_recipe": "Calculando macros exactos...", "start_over": "← Empezar de Nuevo", "note": "Nota del Nutricionista:",
        "ingredients": "🛒 Ingredientes", "save_fav": "⭐ Guardar en Favoritos", "saved": "¡Guardado!", "instructions": "👨‍🍳 Preparación", "adjust_title": "⚖️ Ajustar Macros",
        "adjust_sub": "¿Necesitas otras cantidades?", "adjust_ph": "Ej: 'Añade 20g de proteína'", "recalc_btn": "Recalcular", "recalculating": "Ajustando receta...",
        "profile": "👤 Mi Perfil", "update_prof": "Actualizar Perfil", "prof_updated": "¡Perfil actualizado!", "favs": "⭐ Favoritos", "no_favs": "Aún no hay favoritos.",
        "logout": "Cerrar Sesión", "news_title": "📰 Tendencias Nutricionales", "feed_title": "Últimas Noticias 🔥", "cook_this": "Cocinar esto 🍳", "download_btn": "⬇️ Descargar",
        "keep_logged_in": "Mantener sesión iniciada", "chef_recom": "🌟 RECOMENDACIÓN ESTRELLA 🌟",
        "auth_app_name": "NutriAI 🌿", "auth_subtitle": "Tu chef y nutricionista personal impulsado por IA.", "tab_login": "🔑 Iniciar Sesión", "tab_register": "📝 Registrarse", "tab_recover": "🆘 Recuperar PIN",
        "username_label_login": "Usuario", "pin_label_login": "PIN", "login_btn": "Entrar a la Cocina 🚀", "login_error": "Usuario o PIN incorrectos.",
        "reg_section1": "1. Datos de Acceso", "create_user_label": "Crea un Usuario único", "create_pin_label": "Crea un PIN corto", "security_question_label": "Pregunta de Seguridad",
        "security_options":["¿Nombre de tu primera mascota?", "¿Ciudad de nacimiento?", "¿Nombre de tu colegio?"], "security_answer_label": "Respuesta",
        "reg_section2": "2. Tu Perfil Clínico", "name_label": "Nombre Real", "age_label": "Edad", "weight_label": "Peso (kg)", "height_label": "Altura (cm)", "gender_label": "Género", "gender_options":["Masculino", "Femenino", "Otro"],
        "reg_section3": "3. Objetivos", "goals_label": "Objetivo principal", "rest_label": "Restricciones Crónicas", "create_account_btn": "Crear Cuenta 🚀", "username_taken": "Usuario en uso.",
        "account_created": "¡Cuenta creada!", "fill_required": "Rellena los campos.", "forgot_pin_text": "¿Olvidaste tu PIN?", "search_user_label": "Introduce tu Usuario",
        "search_user_btn": "Buscar", "user_found": "Usuario encontrado.", "user_not_found": "Usuario no encontrado.", "recover_question_prefix": "Pregunta:", "your_answer_label": "Respuesta", "new_pin_label": "Nuevo PIN",
        "change_pin_btn": "Cambiar PIN", "pin_changed_success": "¡PIN cambiado!", "wrong_answer": "Incorrecta.", "current_weight_label": "Peso Actual (kg)",
        "profile_goals_label": "Objetivos", "profile_restrictions_label": "Restricciones", 
        "back_home": "🏠 Volver al Menú", "add_to_log": "📝 Añadir al registro de hoy", "log_success": "¡Añadido al registro de hoy!",
        "shop_title": "Lista de la Compra Dinámica", "search_web_label": "¿Qué te gustaría preparar?", "search_web_btn": "🔍 Buscar y Extraer Ingredientes",
        "shop_list_title": "Tu Inventario de Compra", "add_item_btn": "Añadir Item", "clear_list": "🗑️ Vaciar Lista",
        "plan_title": "Planificador Semanal", "save_plan": "💾 Guardar Planificación", "plan_saved": "¡Planificación guardada!",
        "nutri_title": "Resumen Nutricional Diario", "manual_log_label": "¿Qué has comido fuera de la app? (Ej: 1 Manzana)", "manual_log_btn": "➕ Añadir",
        "eval_btn": "🩺 Evaluar mi día", "total_today": "Total de hoy", "analyzing_nutri": "Evaluando datos médicos...",
        "cat_produce": "🥦 Frutas y Verduras", "cat_dairy": "🥛 Lácteos y Huevos", "cat_white_meat": "🍗 Carnes Blancas", 
        "cat_red_meat": "🥩 Carnes Rojas", "cat_seafood": "🐟 Pescados y Mariscos", "cat_pantry": "🥫 Despensa y Granos", "cat_other": "🛒 Otros",
        "add_to_list": "Añadir a la lista", "delete_item": "Eliminar", "type_food": "Escribe un alimento suelto...",
        "day_1": "Lunes", "day_2": "Martes", "day_3": "Miércoles", "day_4": "Jueves", "day_5": "Viernes", "day_6": "Sábado", "day_7": "Domingo",
        "mac_cal": "Calorías", "mac_pro": "Proteínas", "mac_fat": "Grasas", "mac_car": "Carbohidratos",
        "nut_facts": "Información Nutricional", "nut_cal": "Calorías", "nut_tfat": "Grasa Total", "nut_sfat": "Grasa Saturada", "nut_sod": "Sodio", "nut_tcarb": "Carbohidratos Totales", "nut_fib": "Fibra Dietética", "nut_sug": "Azúcares Totales", "nut_pro": "Proteína"
    },
    "🇬🇧 English": {
        "lang_code": "English", "title": "Hi {name}! What are we cooking today? 🍲", "subtitle": "Your smart nutrition ecosystem.",
        "dash_mod1": "Magic Kitchen", "dash_mod2": "My Groceries", "dash_mod3": "My Menus", "dash_mod4": "My Health",
        "assistant_msg": "What's in the pantry?", "avail_ing_label": "Available ingredients", "avoid_today_label": "Anything to avoid?", "find_btn": "Find Magic Recipes",
        "analyzing": "Analyzing...", "here_options": "Options:", "diff": "Difficulty", "time": "Time", "health": "Health",
        "cook_btn": "Cook {}", "loading_recipe": "Calculating macros...", "start_over": "← Start Over", "note": "Nutritionist Note:",
        "ingredients": "🛒 Ingredients", "save_fav": "⭐ Save Fav", "saved": "Saved!", "instructions": "👨‍🍳 Instructions", "adjust_title": "⚖️ Adjust Macros",
        "adjust_sub": "Need different targets?", "adjust_ph": "e.g. 'Add 20g protein'", "recalc_btn": "Recalculate", "recalculating": "Adjusting...",
        "profile": "👤 Profile", "update_prof": "Update", "prof_updated": "Updated!", "favs": "⭐ Favs", "no_favs": "No favs yet.",
        "logout": "Logout", "news_title": "📰 Nutrition Trends", "feed_title": "Latest News 🔥", "cook_this": "Cook this 🍳", "download_btn": "⬇️ Download",
        "keep_logged_in": "Keep logged in", "chef_recom": "🌟 CHEF'S RECOMMENDATION 🌟", "auth_app_name": "NutriAI 🌿", "auth_subtitle": "AI Personal Chef", 
        "tab_login": "🔑 Log In", "tab_register": "📝 Register", "tab_recover": "🆘 Recover", "username_label_login": "Username", "pin_label_login": "PIN", 
        "login_btn": "Enter 🚀", "login_error": "Error.", "reg_section1": "1. Access", "create_user_label": "Username", "create_pin_label": "PIN", 
        "security_question_label": "Question", "security_options":["Pet?", "City?", "School?"], "security_answer_label": "Answer",
        "reg_section2": "2. Profile", "name_label": "Name", "age_label": "Age", "weight_label": "Weight", "height_label": "Height", "gender_label": "Gender", 
        "gender_options":["Male", "Female", "Other"], "reg_section3": "3. Goals", "goals_label": "Goals", "rest_label": "Restrictions", "create_account_btn": "Create 🚀", 
        "username_taken": "Taken.", "account_created": "Created!", "fill_required": "Fill all.", "forgot_pin_text": "Forgot PIN?", "search_user_label": "Username",
        "search_user_btn": "Search", "user_found": "Found.", "user_not_found": "Not found.", "recover_question_prefix": "Q:", "your_answer_label": "Answer", 
        "new_pin_label": "New PIN", "change_pin_btn": "Change", "pin_changed_success": "Changed!", "wrong_answer": "Wrong.", "current_weight_label": "Weight",
        "profile_goals_label": "Goals", "profile_restrictions_label": "Restrictions",
        "back_home": "🏠 Back to Home", "add_to_log": "📝 Add to today's log", "log_success": "Added to log!",
        "shop_title": "Dynamic Shopping List", "search_web_label": "What do you want to cook?", "search_web_btn": "🔍 Search & Extract",
        "shop_list_title": "Your Groceries", "add_item_btn": "Add Item", "clear_list": "🗑️ Clear List",
        "plan_title": "Weekly Planner", "save_plan": "💾 Save Plan", "plan_saved": "Plan saved!",
        "nutri_title": "Daily Nutritional Summary", "manual_log_label": "Ate outside the app? (e.g., 1 Apple)", "manual_log_btn": "➕ Add",
        "eval_btn": "🩺 Evaluate my day", "total_today": "Total today", "analyzing_nutri": "Evaluating medical data...",
        "cat_produce": "🥦 Fruits & Vegetables", "cat_dairy": "🥛 Dairy & Eggs", "cat_white_meat": "🍗 White Meat", 
        "cat_red_meat": "🥩 Red Meat", "cat_seafood": "🐟 Seafood", "cat_pantry": "🥫 Pantry & Grains", "cat_other": "🛒 Other",
        "add_to_list": "Add to list", "delete_item": "Delete", "type_food": "Type a food item...",
        "day_1": "Monday", "day_2": "Tuesday", "day_3": "Wednesday", "day_4": "Thursday", "day_5": "Friday", "day_6": "Saturday", "day_7": "Sunday",
        "mac_cal": "Calories", "mac_pro": "Protein", "mac_fat": "Fats", "mac_car": "Carbs",
        "nut_facts": "Nutrition Facts", "nut_cal": "Calories", "nut_tfat": "Total Fat", "nut_sfat": "Saturated Fat", "nut_sod": "Sodium", "nut_tcarb": "Total Carbohydrate", "nut_fib": "Dietary Fiber", "nut_sug": "Total Sugars", "nut_pro": "Protein"
    },
    "🇫🇷 Français": {
        "lang_code": "French", "title": "Bonjour {name} !", "subtitle": "Votre écosystème nutritionnel.",
        "dash_mod1": "Cuisine Magique", "dash_mod2": "Mes Courses", "dash_mod3": "Mes Menus", "dash_mod4": "Ma Santé",
        "assistant_msg": "Qu'y a-t-il dans le frigo ?", "avail_ing_label": "Ingrédients disponibles", "avoid_today_label": "À éviter ?", "find_btn": "Trouver",
        "analyzing": "Analyse...", "here_options": "Options :", "diff": "Difficulté", "time": "Temps", "health": "Santé",
        "cook_btn": "Cuisiner {}", "loading_recipe": "Calcul...", "start_over": "← Recommencer", "note": "Note :",
        "ingredients": "🛒 Ingrédients", "save_fav": "⭐ Sauvegarder", "saved": "Sauvegardé !", "instructions": "👨‍🍳 Préparation", "adjust_title": "⚖️ Ajuster",
        "adjust_sub": "Autres quantités ?", "adjust_ph": "Ex : '20g de protéines'", "recalc_btn": "Recalculer", "recalculating": "Ajustement...",
        "profile": "👤 Profil", "update_prof": "Mettre à jour", "prof_updated": "Mis à jour !", "favs": "⭐ Favoris", "no_favs": "Pas de favoris.",
        "logout": "Déconnexion", "news_title": "📰 Tendances Nutrition", "feed_title": "Dernières Nouvelles 🔥", "cook_this": "Cuisiner 🍳", "download_btn": "⬇️ Télécharger",
        "keep_logged_in": "Rester connecté", "chef_recom": "🌟 RECOMMANDATION 🌟", "auth_app_name": "NutriAI 🌿", "auth_subtitle": "Chef personnel IA.",
        "tab_login": "🔑 Login", "tab_register": "📝 Inscription", "tab_recover": "🆘 Récupérer", "username_label_login": "Utilisateur", "pin_label_login": "PIN",
        "login_btn": "Entrer 🚀", "login_error": "Erreur.", "reg_section1": "1. Accès", "create_user_label": "Utilisateur", "create_pin_label": "PIN",
        "security_question_label": "Question", "security_options":["Animal ?", "Ville ?", "École ?"], "security_answer_label": "Réponse",
        "reg_section2": "2. Profil", "name_label": "Nom", "age_label": "Âge", "weight_label": "Poids", "height_label": "Taille", "gender_label": "Genre",
        "gender_options":["Homme", "Femme", "Autre"], "reg_section3": "3. Objectifs", "goals_label": "Objectifs", "rest_label": "Restrictions", "create_account_btn": "Créer 🚀",
        "username_taken": "Pris.", "account_created": "Créé !", "fill_required": "Remplir.", "forgot_pin_text": "PIN oublié ?", "search_user_label": "Utilisateur",
        "search_user_btn": "Chercher", "user_found": "Trouvé.", "user_not_found": "Non trouvé.", "recover_question_prefix": "Q :", "your_answer_label": "Réponse",
        "new_pin_label": "Nouveau PIN", "change_pin_btn": "Changer", "pin_changed_success": "Changé !", "wrong_answer": "Faux.", "current_weight_label": "Poids",
        "profile_goals_label": "Objectifs", "profile_restrictions_label": "Restrictions", 
        "back_home": "🏠 Retour", "add_to_log": "📝 Ajouter au journal", "log_success": "Ajouté !", "shop_title": "Liste de Courses", "search_web_label": "Que voulez-vous cuisiner ?", "search_web_btn": "🔍 Extraire",
        "shop_list_title": "Inventaire", "add_item_btn": "Ajouter", "clear_list": "🗑️ Vider", "plan_title": "Planificateur", "save_plan": "💾 Sauvegarder", "plan_saved": "Sauvegardé !",
        "nutri_title": "Résumé Nutritionnel", "manual_log_label": "Mangé dehors ?", "manual_log_btn": "➕ Ajouter", "eval_btn": "🩺 Évaluer", "total_today": "Total", "analyzing_nutri": "Évaluation...",
        "cat_produce": "🥦 Fruits et Légumes", "cat_dairy": "🥛 Produits Laitiers", "cat_white_meat": "🍗 Viande Blanche", 
        "cat_red_meat": "🥩 Viande Rouge", "cat_seafood": "🐟 Poissons et Fruits de Mer", "cat_pantry": "🥫 Garde-manger", "cat_other": "🛒 Autre",
        "add_to_list": "Ajouter", "delete_item": "Supprimer", "type_food": "Écrivez un aliment...",
        "day_1": "Lundi", "day_2": "Mardi", "day_3": "Mercredi", "day_4": "Jeudi", "day_5": "Vendredi", "day_6": "Samedi", "day_7": "Dimanche",
        "mac_cal": "Calories", "mac_pro": "Protéines", "mac_fat": "Graisses", "mac_car": "Glucides",
        "nut_facts": "Valeurs Nutritionnelles", "nut_cal": "Calories", "nut_tfat": "Graisses Totales", "nut_sfat": "Graisses Saturées", "nut_sod": "Sodium", "nut_tcarb": "Glucides Totaux", "nut_fib": "Fibres Alimentaires", "nut_sug": "Sucres Totaux", "nut_pro": "Protéines"
    },
    "🇮🇹 Italiano": {
        "lang_code": "Italian", "title": "Ciao {name}!", "subtitle": "Il tuo ecosistema nutrizionale.",
        "dash_mod1": "Cucina Magica", "dash_mod2": "La Mia Spesa", "dash_mod3": "I Miei Menù", "dash_mod4": "La Mia Salute",
        "assistant_msg": "Cosa c'è in dispensa?", "avail_ing_label": "Ingredienti", "avoid_today_label": "Da evitare?", "find_btn": "Trova Ricette",
        "analyzing": "Analizzando...", "here_options": "Opzioni:", "diff": "Difficoltà", "time": "Tempo", "health": "Salute",
        "cook_btn": "Cucina {}", "loading_recipe": "Calcolando...", "start_over": "← Ricomincia", "note": "Nota:",
        "ingredients": "🛒 Ingredienti", "save_fav": "⭐ Salva", "saved": "Salvato!", "instructions": "👨‍🍳 Preparazione", "adjust_title": "⚖️ Regola",
        "adjust_sub": "Altre quantità?", "adjust_ph": "Es: '20g proteine'", "recalc_btn": "Ricalcola", "recalculating": "Regolazione...",
        "profile": "👤 Profilo", "update_prof": "Aggiorna", "prof_updated": "Aggiornato!", "favs": "⭐ Preferiti", "no_favs": "Nessun preferito.",
        "logout": "Esci", "news_title": "📰 Tendenze Nutrizionali", "feed_title": "Ultime Notizie 🔥", "cook_this": "Cucina 🍳", "download_btn": "⬇️ Scarica",
        "keep_logged_in": "Mantieni accesso", "chef_recom": "🌟 RACCOMANDAZIONE 🌟", "auth_app_name": "NutriAI 🌿", "auth_subtitle": "Chef IA.",
        "tab_login": "🔑 Accedi", "tab_register": "📝 Registrati", "tab_recover": "🆘 Recupera", "username_label_login": "Utente", "pin_label_login": "PIN",
        "login_btn": "Entra 🚀", "login_error": "Errore.", "reg_section1": "1. Accesso", "create_user_label": "Utente", "create_pin_label": "PIN",
        "security_question_label": "Domanda", "security_options":["Animale?", "Città?", "Scuola?"], "security_answer_label": "Risposta",
        "reg_section2": "2. Profilo", "name_label": "Nome", "age_label": "Età", "weight_label": "Peso", "height_label": "Altezza", "gender_label": "Genere",
        "gender_options":["Maschio", "Femmina", "Altro"], "reg_section3": "3. Obiettivi", "goals_label": "Obiettivi", "rest_label": "Restrizioni", "create_account_btn": "Crea 🚀",
        "username_taken": "In uso.", "account_created": "Creato!", "fill_required": "Compila tutto.", "forgot_pin_text": "Dimenticato PIN?", "search_user_label": "Utente",
        "search_user_btn": "Cerca", "user_found": "Trovato.", "user_not_found": "Non trovato.", "recover_question_prefix": "D:", "your_answer_label": "Risposta",
        "new_pin_label": "Nuovo PIN", "change_pin_btn": "Cambia", "pin_changed_success": "Cambiato!", "wrong_answer": "Errato.", "current_weight_label": "Peso",
        "profile_goals_label": "Obiettivi", "profile_restrictions_label": "Restrizioni", 
        "back_home": "🏠 Torna alla Home", "add_to_log": "📝 Aggiungi al diario", "log_success": "Aggiunto!", "shop_title": "Lista della Spesa", "search_web_label": "Cosa vuoi cucinare?", "search_web_btn": "🔍 Estrai",
        "shop_list_title": "La tua spesa", "add_item_btn": "Aggiungi", "clear_list": "🗑️ Svuota lista", "plan_title": "Pianificatore", "save_plan": "💾 Salva", "plan_saved": "Salvato!",
        "nutri_title": "Riassunto Nutrizionale", "manual_log_label": "Mangiato fuori?", "manual_log_btn": "➕ Aggiungi", "eval_btn": "🩺 Valuta la mia giornata", "total_today": "Totale di oggi", "analyzing_nutri": "Valutazione...",
        "cat_produce": "🥦 Frutta e Verdura", "cat_dairy": "🥛 Latticini e Uova", "cat_white_meat": "🍗 Carne Bianca", 
        "cat_red_meat": "🥩 Carne Rossa", "cat_seafood": "🐟 Pesce e Frutti di Mare", "cat_pantry": "🥫 Dispensa e Cereali", "cat_other": "🛒 Altro",
        "add_to_list": "Aggiungi alla lista", "delete_item": "Elimina", "type_food": "Scrivi un alimento...",
        "day_1": "Lunedì", "day_2": "Martedì", "day_3": "Mercoledì", "day_4": "Giovedì", "day_5": "Venerdì", "day_6": "Sabato", "day_7": "Domenica",
        "mac_cal": "Calorie", "mac_pro": "Proteine", "mac_fat": "Grassi", "mac_car": "Carboidrati",
        "nut_facts": "Valori Nutrizionali", "nut_cal": "Calorie", "nut_tfat": "Grassi Totali", "nut_sfat": "Grassi Saturi", "nut_sod": "Sodio", "nut_tcarb": "Carboidrati Totali", "nut_fib": "Fibra Alimentare", "nut_sug": "Zuccheri Totali", "nut_pro": "Proteine"
    }
}

if "selected_lang" not in st.session_state: st.session_state.selected_lang = "🇪🇸 Español"

# CALLBACK DE AUTO-TRADUCCIÓN (State Translation)
def handle_language_change():
    new_lang = st.session_state.selected_lang
    new_lang_code = TRANSLATIONS[new_lang]["lang_code"]
    
    with st.spinner(f"Traduciendo al {new_lang_code}... / Translating..."):
        # Traducir opciones listadas si existen
        if st.session_state.get("options"):
            sys_p = f"Translate all the VALUES of this JSON array into {new_lang_code.upper()}, keeping the exact same English KEYS. Return ONLY the JSON object with an 'options' key containing the translated array."
            user_p = json.dumps({"options": st.session_state.options})
            res = groq_generic_json(sys_p, user_p)
            if res and "options" in res:
                st.session_state.options = res["options"]
                
        # Traducir receta detallada si existe
        if st.session_state.get("full_recipe"):
            sys_p = f"Translate all the VALUES of this JSON object into {new_lang_code.upper()}, keeping the exact same English KEYS. Return ONLY the translated JSON object."
            user_p = json.dumps(st.session_state.full_recipe)
            res = groq_generic_json(sys_p, user_p)
            if res:
                st.session_state.full_recipe = res

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
            keep_in = st.checkbox(t["keep_logged_in"], value=True)
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
                        new_user = {"username": reg_user, "pin": reg_pin, "security_question": reg_sq, "security_answer": reg_sa.lower(), "name": reg_name, "age": reg_age, "weight": reg_weight, "height": reg_height, "gender": reg_gender, "goals": reg_goals, "restrictions": reg_rest, "favorites":[], "daily_logs":{}, "weekly_planner":{}, "shopping_list":[]}
                        supabase.table("app_users_2").insert(new_user).execute()
                        st.session_state.current_username = reg_user
                        st.session_state.keep_in = True
                        st.session_state.do_login_js = True
                        st.success(t["account_created"])
                        st.rerun()
                else: st.warning(t["fill_required"])
        
        with tab3:
            st.markdown(t["forgot_pin_text"])
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
    st.subheader(t["favs"])
    favs = user_profile.get("favorites",[])
    if favs:
        for f in favs:
            with st.expander(f.get("name", "Favorito")): 
                st.write(f"🔥 {f.get('calories', 0)} | 💪 {f.get('protein', '0g')}")
    else: st.info(t["no_favs"])

    st.divider()
    with st.expander(t.get("news_title", "📰 Tendencias Nutricionales"), expanded=True):
        
        # Llamamos a nuestra nueva función infalible
        news_items = fetch_daily_healthy_recipes(lang_code)
        
        if news_items:
            for news in news_items:
                r_title = news.get('title', 'Receta Saludable')
                r_summary = news.get('summary', '')[:120] + "..."
                r_url = news.get('url', '#')
                
                st.markdown(f"""
                <div style="background: #FFFFFF; padding:12px; border-radius:10px; margin-bottom:12px; border:1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); transition: transform 0.2s;">
                    <h4 style="margin:0;font-size:14px;font-weight:700;color:#1E293B;line-height:1.2;">{r_title}</h4>
                    <p style="font-size:12px;margin-top:6px;margin-bottom:8px;line-height:1.4;color:#475569;">{r_summary}</p>
                    <a href="{r_url}" target="_blank" style="display:inline-block; padding:4px 0px; font-size:12px;color:#10B981;font-weight:800;text-decoration:none;">{t.get("cook_this", "Ver receta 🍳")} →</a>
                </div>
                """, unsafe_allow_html=True)
        else: 
            st.warning("No se pudieron cargar las noticias hoy.")
            
        # Un botón para forzar la actualización si fuera necesario
        if st.button("🔄 Actualizar Recetas", use_container_width=True):
            fetch_daily_healthy_recipes.clear()
            st.rerun()

# ==========================================
# HEADER PRINCIPAL
# ==========================================
st.markdown(f"<h1 class='brand-logo'>NutriAI</h1>", unsafe_allow_html=True)

# ==========================================
# RUTEO DE PÁGINAS (DASHBOARD REDISEÑADO)
# ==========================================
if st.session_state.current_page == "home":
    st.markdown("""
    <style>
    /* Diseño Masivo y SVGs para los 4 Módulos */
    [data-testid="column"] div.stButton > button {
        min-height: 220px !important;
        border-radius: 24px !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #1E293B !important;
        background-color: #FFFFFF !important;
        background-image: none !important; 
        box-shadow: 0 10px 40px rgba(0,0,0,0.06) !important;
        border: 2px solid #E2E8F0 !important;
        transition: all 0.3s ease !important;
        background-repeat: no-repeat !important;
        background-position: center top 35px !important;
        background-size: 70px !important;
        padding-top: 100px !important; 
    }
    [data-testid="column"] div.stButton > button:hover {
        transform: translateY(-8px) !important;
        box-shadow: 0 20px 50px rgba(16,185,129,0.15) !important;
        border: 2px solid #10B981 !important;
    }
    
    /* 1: Cocina Mágica (Wand/Chef Hat) */
    [data-testid="column"]:nth-of-type(1) div.stButton:nth-of-type(1) button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2310b981' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2l3 6 6 1-4 4 1 6-6-3-6 3 1-6-4-4 6-1z'/%3E%3C/svg%3E") !important;
    }
    
    /* 3: Mis Menús (Calendar) */
    [data-testid="column"]:nth-of-type(1) div.stButton:nth-of-type(2) button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23f59e0b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='4' width='18' height='18' rx='2' ry='2'/%3E%3Cline x1='16' y1='2' x2='16' y2='6'/%3E%3Cline x1='8' y1='2' x2='8' y2='6'/%3E%3Cline x1='3' y1='10' x2='21' y2='10'/%3E%3C/svg%3E") !important;
    }

    /* 2: Mi Compra (Cart) */
    [data-testid="column"]:nth-of-type(2) div.stButton:nth-of-type(1) button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%233b82f6' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='9' cy='21' r='1'/%3E%3Ccircle cx='20' cy='21' r='1'/%3E%3Cpath d='M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6'/%3E%3C/svg%3E") !important;
    }

    /* 4: Mi Salud (Heart) */[data-testid="column"]:nth-of-type(2) div.stButton:nth-of-type(2) button {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ef4444' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z'/%3E%3C/svg%3E") !important;
    }
    
    /* Layout Móvil */
    @media (max-width: 768px) {
        [data-testid="column"] div.stButton > button { min-height: 180px !important; font-size: 22px !important; margin-bottom: 10px; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<h2 style='text-align:center;'>{t['title'].format(name=user_profile['name'])}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:1.2rem; color:#64748B;'>{t['subtitle']}</p><br>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t["dash_mod1"], use_container_width=True):
            st.session_state.current_page = "mod1"
            st.session_state.step = "input"
            st.rerun()
        if st.button(t["dash_mod3"], use_container_width=True):
            st.session_state.current_page = "mod3"
            st.rerun()
    with c2:
        if st.button(t["dash_mod2"], use_container_width=True):
            st.session_state.current_page = "mod2"
            st.rerun()
        if st.button(t["dash_mod4"], use_container_width=True):
            st.session_state.current_page = "mod4"
            st.rerun()

# ==========================================
# MÓDULO 1: COCINA INTELIGENTE
# ==========================================
elif st.session_state.current_page == "mod1":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()

    if st.session_state.step in ["input", "options"]:
        st.markdown(f"#### 👨‍🍳 {t['assistant_msg']}")
        available_ingredients = st.text_area(t["avail_ing_label"], placeholder="Ej: Pechuga de pollo, espinacas, 3 huevos...", height=100)
        avoid_today = st.text_input("🚫 " + t["avoid_today_label"], placeholder="Ej: fritos, picante...")
        
        if st.button(t["find_btn"], type="primary", use_container_width=True):
            if available_ingredients:
                st.session_state.avail_ing = available_ingredients
                st.session_state.avoid_tdy = avoid_today
                
                ing_count = len([x for x in re.split(r',|\sy\s|\sand\s|\set\s|\n', available_ingredients) if x.strip()])
                if ing_count <= 4: n_recipes = 2
                elif ing_count <= 8: n_recipes = 3
                else: n_recipes = 4
                
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
            else: st.warning(t["fill_required"])

    if st.session_state.step == "options" and st.session_state.options:
        st.divider()
        st.subheader(t["here_options"])
        
        for i, opt in enumerate(st.session_state.options):
            recipe_name = opt.get('name', opt.get('recipe_name', 'Receta Mágica'))
            difficulty = opt.get('difficulty', 'Media')
            time_prep = opt.get('time', '20 mins')
            health_score = opt.get('health_score', 8)
            description = opt.get('description', '')

            with st.container():
                if opt.get("is_chefs_recommendation", False):
                    st.markdown(f"""
                    <div class="golden-card">
                        <div class="golden-card-content">
                            <span style="color:#B45309; font-weight:900; letter-spacing:2px; font-size:14px;">{t['chef_recom']}</span>
                            <h1 style="font-size: 55px; margin: 5px 0;">{opt.get('hero_emoji', '🍽️')}</h1>
                            <h2 style="margin: 0; color: #1E293B;">{recipe_name}</h2>
                            <p style="color:#64748B; font-style:italic; margin-top:5px;">Alineado 100% con tu perfil de salud</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<h1 style='text-align:center; font-size:40px; margin:0;'>{opt.get('hero_emoji', '🍽️')}</h1><h3 style='text-align:center;'>{recipe_name}</h3>", unsafe_allow_html=True)
                
                st.caption(f"**{t['diff']}:** {difficulty} | **{t['time']}:** {time_prep} | **{t['health']}:** {health_score}/10")
                st.write(description)
                
                if st.button(t["cook_btn"].format(""), key=f"btn_cook_{i}", use_container_width=True):
                    st.session_state.selected_option = opt
                    st.session_state.step = "recipe_loading"
                    st.rerun()
            st.write("---")

    if st.session_state.step == "recipe_loading":
        lottie_placeholder = st.empty()
        with lottie_placeholder.container():
            st.markdown("<br>", unsafe_allow_html=True)
            if lottie_cooking: st_lottie(lottie_cooking, height=200, key="loading_anim_2")
            st.markdown(f"<h3 style='text-align:center;'>{t['loading_recipe']}</h3>", unsafe_allow_html=True)
        
        safe_name = st.session_state.selected_option.get('name', st.session_state.selected_option.get('recipe_name', 'la receta seleccionada'))
        prompt = f"Write the complete and detailed recipe for '{safe_name}'. Explain each step carefully."
        
        format_hint = """{ 
            "recipe_name": "Nombre de la receta", 
            "region": "Estilo", 
            "hero_emoji": "🥘", 
            "ingredients_emojis": "🍅🧅", 
            "nutritionist_note": "Nota del nutricionista", 
            "health_badges":[
                {"icon": "🟢", "label": "Sin Colesterol", "type": "positive"},
                {"icon": "🔴", "label": "Alto en Sodio", "type": "warning"}
            ],
            "macros": { 
                "calories": "450 kcal", 
                "total_fat": "15g", 
                "saturated_fat": "3g", 
                "sodium": "400mg", 
                "total_carbs": "30g", 
                "fiber": "6g", 
                "sugars": "5g", 
                "protein": "40g" 
            }, 
            "ingredients":[{"item": "Nombre del ingrediente", "qty": "200g"}], 
            "instructions":["1. 🍳 Primer paso...", "2. 🔪 Segundo paso..."] 
        }"""
        res = call_ai_json(prompt, format_hint, lang_code, user_profile, st.session_state.avail_ing, st.session_state.avoid_tdy)
        lottie_placeholder.empty()
        
        if res:
            st.session_state.full_recipe = res
            st.session_state.step = "recipe_view"
            st.rerun()

    if st.session_state.step == "recipe_view" and st.session_state.full_recipe:
        recipe = st.session_state.full_recipe
        recipe['recipe_name'] = recipe.get('recipe_name', recipe.get('name', 'Receta Mágica'))
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button(t["start_over"], use_container_width=True):
                st.session_state.step, st.session_state.options, st.session_state.full_recipe, st.session_state.avail_ing, st.session_state.avoid_tdy = "input", None, None, "", ""
                st.rerun()
        with col_btn2:
            txt_data = format_recipe_for_download(recipe, t)
            st.download_button(label=t["download_btn"], data=txt_data, file_name=f"{recipe.get('recipe_name', 'receta').replace(' ', '_')}.txt", mime="text/plain", use_container_width=True)

        st.markdown(f"<p class='hero-emoji'>{recipe.get('hero_emoji', '🍽️')}</p><h2 style='text-align:center;'>{recipe.get('recipe_name', '')}</h2><h4 style='text-align:center; color:#64748B;'>🌍 {recipe.get('region', 'Global')}</h4><h3 style='text-align:center; letter-spacing: 5px;'>{recipe.get('ingredients_emojis', '')}</h3>", unsafe_allow_html=True)
        st.info(f"**{t['note']}** {recipe.get('nutritionist_note', '')}")
        st.divider()
        
        badges = recipe.get('health_badges',[])
        if badges:
            html_b = "<div style='display:flex; justify-content:center; gap:12px; flex-wrap:wrap; margin-bottom:20px;'>"
            for b in badges:
                c = "#10b981" if b.get("type")=="positive" else "#f59e0b" if b.get("type")=="warning" else "#ef4444"
                html_b += f"<span style='background:{c}15; color:{c}; padding:8px 18px; border-radius:20px; font-weight:700; font-size:14px; border:1px solid {c}50; box-shadow:0 2px 5px rgba(0,0,0,0.05);'>{b.get('icon','')} {b.get('label','')}</span>"
            html_b += "</div>"
            st.markdown(html_b, unsafe_allow_html=True)
        
        col_label, col_chart = st.columns(2)
        m = recipe.get('macros', {})
        
        with col_label:
            st.markdown(f"""
            <div class="nutrition-label">
                <h2>{t.get('nut_facts', 'Nutrition Facts')}</h2>
                <div class="nut-row thick"><span class="nut-bold">{t.get('nut_cal', 'Calories')}</span> <span class="nut-bold">{m.get('calories', '0')}</span></div>
                <div class="nut-row"><span class="nut-bold">{t.get('nut_tfat', 'Total Fat')}</span> {m.get('total_fat', '0g')}</div>
                <div class="nut-row" style="padding-left: 1.5rem;">{t.get('nut_sfat', 'Saturated Fat')} {m.get('saturated_fat', '0g')}</div>
                <div class="nut-row"><span class="nut-bold">{t.get('nut_sod', 'Sodium')}</span> {m.get('sodium', '0mg')}</div>
                <div class="nut-row"><span class="nut-bold">{t.get('nut_tcarb', 'Total Carbohydrate')}</span> {m.get('total_carbs', '0g')}</div>
                <div class="nut-row" style="padding-left: 1.5rem;">{t.get('nut_fib', 'Dietary Fiber')} {m.get('fiber', '0g')}</div>
                <div class="nut-row" style="padding-left: 1.5rem;">{t.get('nut_sug', 'Total Sugars')} {m.get('sugars', '0g')}</div>
                <div class="nut-row thick"><span class="nut-bold">{t.get('nut_pro', 'Protein')}</span> <span class="nut-bold">{m.get('protein', '0g')}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_chart:
            macro_df = pd.DataFrame({
                "Macro":[t.get("mac_pro", "Proteínas"), t.get("mac_fat", "Grasas"), t.get("mac_car", "Carbohidratos")], 
                "Gramos":[extract_number(m.get('protein', '0g')), extract_number(m.get('total_fat', '0g')), extract_number(m.get('total_carbs', '0g'))]
            })
            if macro_df['Gramos'].sum() > 0:
                fig = px.pie(macro_df, values='Gramos', names='Macro', hole=0.55, color_discrete_sequence=['#EF4444', '#F59E0B', '#3B82F6'])
                fig.update_traces(textfont_color='#FFFFFF', textinfo='percent+label', textposition='inside')
                fig.update_layout(
                    margin=dict(t=20, b=20, l=20, r=20), showlegend=True, 
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color='#1E293B')), 
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1E293B')
                )
                st.plotly_chart(fig, use_container_width=True)
        
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button(t["save_fav"], use_container_width=True):
                favs = user_profile.get("favorites",[])
                favs.append({"name": recipe.get("recipe_name", ""), "calories": m.get('calories', '0'), "protein": m.get('protein', '0g')})
                update_user_data(user_profile["username"], {"favorites": favs})
                st.toast(t["saved"])
        with c_act2:
            if st.button(t["add_to_log"], type="primary", use_container_width=True):
                entry = {"name": recipe.get("recipe_name", ""), "calories": extract_number(m.get('calories', '0')), "protein": extract_number(m.get('protein', '0')), "fat": extract_number(m.get('total_fat', '0')), "carbs": extract_number(m.get('total_carbs', '0'))}
                append_to_daily_log(user_profile["username"], entry)
                st.toast(t["log_success"], icon="✅")
                
        with st.expander("🛒 " + t["ingredients"], expanded=True):
            for ing in recipe.get("ingredients",[]): st.markdown(f"- **{ing.get('qty', '')}** {ing.get('item', '')}")
                
        with st.expander("👨‍🍳 " + t["instructions"], expanded=True):
            for step in recipe.get("instructions",[]): st.write(f"{step}")

        st.divider()
        st.subheader(t["adjust_title"])
        macro_adjustment = st.text_input("", placeholder=t["adjust_ph"])
        if st.button(t["recalc_btn"], use_container_width=True):
            if macro_adjustment:
                lottie_placeholder = st.empty()
                with lottie_placeholder.container():
                    if lottie_cooking: st_lottie(lottie_cooking, height=150, key="loading_anim_3")
                    st.markdown(f"<h3 style='text-align:center;'>{t['recalculating']}</h3>", unsafe_allow_html=True)
                prompt = f"Current recipe: {json.dumps(recipe)}. Adjustment: '{macro_adjustment}'. Recalculate."
                format_hint = "Return strictly in the exact same JSON format as the original recipe."
                new_recipe = call_ai_json(prompt, format_hint, lang_code, user_profile, st.session_state.avail_ing, st.session_state.avoid_tdy)
                lottie_placeholder.empty()
                if new_recipe:
                    st.session_state.full_recipe = new_recipe
                    st.rerun()

# ==========================================
# MÓDULO 2: LISTA DE LA COMPRA E INVENTARIO
# ==========================================
elif st.session_state.current_page == "mod2":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    st.markdown(f"<h2 style='text-align:center;'>{t['shop_title']}</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col1: new_item = st.text_input("", placeholder=t["type_food"], label_visibility="collapsed")
    with col2: add_pressed = st.button(t["add_to_list"], type="primary", use_container_width=True)

    if add_pressed and new_item:
        with st.spinner("Organizando alimento..."):
            sys_prompt = f"""
            Clasifica el alimento del usuario en UNA sola categoría y TRADÚCELO al {lang_code}.
            Categorías válidas: cat_produce, cat_dairy, cat_white_meat, cat_red_meat, cat_seafood, cat_pantry, cat_other.
            Devuelve SOLO JSON: {{"category":"cat_x", "translated_item": "Nombre traducido"}}
            """
            parsed = groq_generic_json(sys_prompt, f"Food: {new_item}")
            category = "cat_other"
            item_name = new_item.capitalize()
            
            if parsed:
                category = parsed.get("category", "cat_other")
                item_name = parsed.get("translated_item", new_item).capitalize()

            shop_list = user_profile.get("shopping_list",[])
            if not isinstance(shop_list,list): shop_list =[]
            shop_list.append({"item": item_name, "category": category})
            update_user_data(user_profile["username"], {"shopping_list":shop_list})
            st.rerun()

    st.divider()
    st.subheader(t["shop_list_title"])
    shop_list = user_profile.get("shopping_list",[])

    if not shop_list:
        st.info("🛒 Tu lista está vacía.")
    else:
        categorized = {}
        for idx,obj in enumerate(shop_list):
            cat = obj.get("category","cat_other")
            if cat not in categorized: categorized[cat] =[]
            categorized[cat].append((idx,obj["item"]))

        category_order =["cat_produce", "cat_dairy", "cat_white_meat", "cat_red_meat", "cat_seafood", "cat_pantry", "cat_other"]
        for cat in category_order:
            if cat in categorized:
                items = categorized[cat]
                if items:
                    with st.expander(f"{t.get(cat,cat)} ({len(items)})", expanded=True):
                        for idx,item in items:
                            c1,c2 = st.columns([6,1])
                            with c1: st.markdown(f"<p style='font-size:1.05rem;font-weight:500;margin-top:6px;'>• {item}</p>", unsafe_allow_html=True)
                            with c2:
                                if st.button("🗑️", key=f"del_{idx}", use_container_width=True):
                                    shop_list.pop(idx)
                                    update_user_data(user_profile["username"], {"shopping_list":shop_list})
                                    st.rerun()

    if shop_list:
        st.markdown("<br>", unsafe_allow_html=True)
        col1,col2 = st.columns([3,1])
        with col2:
            if st.button(t["clear_list"], type="secondary", use_container_width=True):
                update_user_data(user_profile["username"], {"shopping_list":[]})
                st.rerun()

# ==========================================
# MÓDULO 3: PLANIFICADOR SEMANAL
# ==========================================
elif st.session_state.current_page == "mod3":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    st.markdown(f"<h2>{t['plan_title']}</h2>", unsafe_allow_html=True)
    
    planner = user_profile.get("weekly_planner") or {}
    db_days =["day_1", "day_2", "day_3", "day_4", "day_5", "day_6", "day_7"]
    ui_days = [t["day_1"], t["day_2"], t["day_3"], t["day_4"], t["day_5"], t["day_6"], t["day_7"]]
    
    new_plan = {}
    for db_d, ui_d in zip(db_days, ui_days):
        # Permite retrocompatibilidad con bases de datos que guardaron 'Lunes' textualmente
        old_val = planner.get(ui_d, "")
        current_val = planner.get(db_d, old_val)
        new_plan[db_d] = st.text_input(f"📅 {ui_d}", value=current_val, placeholder="Ej: Pollo a la plancha / Descanso")
        
    if st.button(t["save_plan"], type="primary", use_container_width=True):
        update_user_data(user_profile["username"], {"weekly_planner": new_plan})
        st.success(t["plan_saved"])

# ==========================================
# MÓDULO 4: RESUMEN NUTRICIONAL DIARIO
# ==========================================
elif st.session_state.current_page == "mod4":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    st.markdown(f"<h2>{t['nutri_title']}</h2>", unsafe_allow_html=True)
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    daily_logs = user_profile.get("daily_logs") or {}
    today_data = daily_logs.get(today_str,[])
    
    t_cal = sum(item.get("calories", 0) for item in today_data)
    t_pro = sum(item.get("protein", 0) for item in today_data)
    t_fat = sum(item.get("fat", 0) for item in today_data)
    t_car = sum(item.get("carbs", 0) for item in today_data)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"🔥 {t.get('mac_cal', 'Calorías')}", f"{t_cal} kcal")
    c2.metric(f"🍗 {t.get('mac_pro', 'Proteínas')}", f"{t_pro} g")
    c3.metric(f"🥑 {t.get('mac_fat', 'Grasas')}", f"{t_fat} g")
    c4.metric(f"🍞 {t.get('mac_car', 'Carbos')}", f"{t_car} g")
    
    with st.expander("Ver detalle de hoy", expanded=True):
        if not today_data: st.write("No has registrado nada hoy.")
        for d in today_data: st.write(f"- **{d['name']}**: {d['calories']} kcal (P:{d['protein']}g | G:{d['fat']}g | C:{d['carbs']}g)")

    st.divider()
    manual_input = st.text_input(t["manual_log_label"])
    if st.button(t["manual_log_btn"]):
        if manual_input:
            with st.spinner("Calculando macros..."):
                sys = "Estima los macros de este alimento. Devuelve un JSON: {'calories': 100, 'protein': 2, 'fat': 0, 'carbs': 20}"
                parsed = groq_generic_json(sys, f"Alimento: {manual_input}")
                if parsed:
                    entry = {"name": manual_input.title(), "calories": parsed.get('calories',0), "protein": parsed.get('protein',0), "fat": parsed.get('fat',0), "carbs": parsed.get('carbs',0)}
                    append_to_daily_log(user_profile["username"], entry)
                    st.rerun()
    
    st.divider()
    if st.button(t["eval_btn"], type="primary", use_container_width=True):
        with st.spinner(t["analyzing_nutri"]):
            sys_eval = f"Eres un médico nutricionista evaluando a {user_profile['name']} ({user_profile['weight']}kg, Objetivo: {user_profile['goals']}). Hoy ha consumido {t_cal} kcal, {t_pro}g proteína, {t_fat}g grasa, {t_car}g carbos. Genera un breve feedback médico constructivo, realista, de 3 líneas. Devuelve JSON: {{'feedback': 'tu texto aquí'}} en {lang_code}."
            eval_res = groq_generic_json(sys_eval, "Evalúa mi día.")
            if eval_res and "feedback" in eval_res:
                st.info(f"🩺 **Evaluación Médica:**\n\n{eval_res['feedback']}")
