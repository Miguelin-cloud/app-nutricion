import streamlit as st
import json
import os
import datetime
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

def get_current_meal_info():
    """Detecta automáticamente el tipo de comida y color basado en la hora actual (Solo para Módulo 1)."""
    now = datetime.datetime.now()
    hour = now.hour + now.minute / 60.0
    if 6 <= hour < 11.5: return "Desayuno", "#F97316"
    elif 11.5 <= hour < 16: return "Almuerzo", "#10B981"
    elif 16 <= hour < 19.5: return "Merienda", "#8B5CF6"
    else: return "Cena", "#3B82F6"

def add_to_meal_calendar(username, date_str, meal_data):
    user = get_user_data(username)
    cal = user.get("meal_calendar") or {}
    if not isinstance(cal, dict): cal = {}
    if date_str not in cal: cal[date_str] = []
    cal[date_str].append(meal_data)
    update_user_data(username, {"meal_calendar": cal})

# ==========================================
# FUNCIONES IA (GROQ) Y EXTRACCIÓN (CON FALLBACK 3 NIVELES)
# ==========================================

def execute_groq_with_fallback(system_prompt, user_prompt, temperature=0.3, show_ui=True):
    """Motor central de peticiones IA con cascada de 3 niveles ante error 429."""
    client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))
    
    models_hierarchy =[
        {"name": "llama-3.3-70b-versatile", "alias": "Chef Ejecutivo (Plan A)"},
        {"name": "llama-3.1-8b-instant", "alias": "Chef Ayudante Rápido (Plan B)"},
        {"name": "mixtral-8x7b-32768", "alias": "Chef de Emergencia (Plan C)"}
    ]
    
    for idx, model_info in enumerate(models_hierarchy):
        try:
            response = client.chat.completions.create(
                model=model_info["name"], 
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], 
                response_format={"type": "json_object"}, 
                temperature=temperature
            )
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            err_msg = str(e).lower()
            
            if "429" in err_msg or "rate limit" in err_msg or "tokens" in err_msg:
                if idx < len(models_hierarchy) - 1:
                    next_model = models_hierarchy[idx+1]
                    time_str = datetime.datetime.now().strftime("%H:%M:%S")
                    alert_msg = f"⚠️ Tokens agotados en {model_info['alias']}. Usando {next_model['alias']}..."
                    
                    if show_ui:  # Solo muestra Toast si está permitido
                        st.toast(alert_msg, icon="👨‍🍳")
                    
                    log_entry = f"<b>{time_str}</b>: {alert_msg}"
                    if "app_alerts" not in st.session_state: st.session_state.app_alerts =[]
                    st.session_state.app_alerts.insert(0, log_entry) 
                    continue 
                else:
                    if show_ui: st.error("❌ Todos los Chefs de la IA están ocupados.")
                    return None
            else:
                if show_ui: st.error(f"Error técnico de IA ({model_info['name']}): {e}")
                return None

def call_ai_json(prompt, expected_format_hint, lang_code, u_prof, avail_ing="", avoid_tdy="", num_recipes=3):
    # (El interior de esta función déjalo exactamente como lo tienes, hasta llegar al return)
    # ... tu system_prompt ...
    # Usa nuestro nuevo motor blindado, por defecto show_ui es True
    return execute_groq_with_fallback(final_system_prompt, prompt, temperature=0.4, show_ui=True)

def groq_generic_json(system_prompt, user_prompt, show_ui=True):
    # Hemos añadido el parámetro show_ui
    return execute_groq_with_fallback(system_prompt, user_prompt, temperature=0.3, show_ui=show_ui)
    

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
def fetch_daily_healthy_recipes(lang_code, category_key="trend_sweets"):
    query_map = {
        "trend_sweets": "recetas+postres+dulces+saludables",
        "trend_salty": "recetas+saladas+cenas+saludables",
        "trend_snacks": "recetas+snacks+aperitivos+saludables",
        "trend_breakfast": "recetas+desayunos+saludables",
        "trend_drinks": "recetas+smoothies+batidos+saludables"
    }
    search_query = query_map.get(category_key, "recetas+saludables")
    url = f"https://news.google.com/rss/search?q={search_query}&hl=es&gl=ES&ceid=ES:es"
    
    raw_results =[]
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.text)
        for item in root.findall('./channel/item'):
            title = item.find('title').text
            link = item.find('link').text
            clean_title = title.split(" - ")[0] 
            raw_results.append({"title": clean_title, "url": link, "summary": clean_title})
            if len(raw_results) >= 10: break
        random.shuffle(raw_results)
        raw_results = raw_results[:3]
    except Exception:
        return[]

    if not raw_results: return[]
        
    sys_prompt = f"""
    You are a Michelin-star Chef and an expert culinary copywriter.
    I am providing you with a JSON list of REAL daily recipes extracted from Google News.
    Rewrite the 'title' to sound premium, write a 2-line 'summary'. TRANSLATE EVERYTHING TO {lang_code.upper()}.
    Keep 'url' intact. Return JSON format: {{"recipes":[{{"title": "...", "summary": "...", "url": "..."}}]}}
    """
    user_prompt = "REAL GOOGLE NEWS RECIPES:\n" + json.dumps(raw_results)
    
    try:
        # AQUÍ ESTÁ LA MAGIA: show_ui=False evita el error rojo de Caché
        parsed = groq_generic_json(sys_prompt, user_prompt, show_ui=False)
        if parsed and "recipes" in parsed and len(parsed["recipes"]) > 0: return parsed["recipes"]
    except Exception:
        pass
    return raw_results
# ==========================================
# SISTEMA MULTIDIOMA Y TEXTOS (Actualizado Mod 3 y 4)
# ==========================================
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
        "nut_facts": "Información Nutricional", "nut_cal": "Calorías", "nut_tfat": "Grasa Total", "nut_sfat": "Grasa Saturada", "nut_sod": "Sodio", "nut_tcarb": "Carbohidratos Totales", "nut_fib": "Fibra Dietética", "nut_sug": "Azúcares Totales", "nut_pro": "Proteína",
        "cal_prev": "◀ Anterior", "cal_next": "Siguiente ▶", "cal_weekly": "Semanal", "cal_monthly": "Mensual",
        "cal_add_meal_title": "➕ Añadir Comida al Calendario", "cal_ph_food": "Ej: 1 Manzana, café y tostada",
        "cal_add_btn": "Añadir", "cal_analyzing": "Analizando macros silenciosamente...",
        "meal_breakfast": "Desayuno", "meal_lunch": "Almuerzo", "meal_snack": "Merienda", "meal_dinner": "Cena",
        "mod4_title": "🩺 Dashboard de Salud y Análisis Médico", "mod4_period_label": "Selecciona el Período a Analizar",
        "mod4_period_today": "Hoy", "mod4_period_week": "Esta Semana", "mod4_period_month": "Este Mes",
        "mod4_total_cal": "Calorías Totales", "mod4_gen_btn": "🩺 Generar Análisis Clínico Profundo por IA",
        "mod4_analyzing": "La IA médica está analizando tu nutrición...",
        "ptr_default": "🖱️ Predeterminado", "ptr_drumstick": "🍗 Muslito", "ptr_avocado": "🥑 Aguacate", "ptr_pan": "🥘 Sartén", "ptr_pizza": "🍕 Pizza", "ptr_wand": "🪄 Varita", "ptr_apple": "🍎 Manzana",
        "magic_pointer": "🪄 Puntero Mágico", "choose_pointer": "Elige tu puntero:",
        "trend_sweets": "🍰 Dulces", "trend_salty": "🥨 Salados", "trend_snacks": "🥪 Snacks Rápidos", "trend_breakfast": "🥣 Desayunos", "trend_drinks": "🥤 Bebidas/Smoothies",
        "btn_delete": "🗑️ Eliminar", "btn_edit": "✏️ Editar", "btn_save": "💾 Guardar",
        "manage_meals": "⚙️ Gestionar Comidas del Día", "no_meals": "No hay comidas registradas para este día.", "manage_date": "Selecciona la fecha a editar"
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
        "nut_facts": "Nutrition Facts", "nut_cal": "Calories", "nut_tfat": "Total Fat", "nut_sfat": "Saturated Fat", "nut_sod": "Sodium", "nut_tcarb": "Total Carbohydrate", "nut_fib": "Dietary Fiber", "nut_sug": "Total Sugars", "nut_pro": "Protein",
        "cal_prev": "◀ Prev", "cal_next": "Next ▶", "cal_weekly": "Weekly", "cal_monthly": "Monthly",
        "cal_add_meal_title": "➕ Add Meal to Calendar", "cal_ph_food": "e.g., 1 Apple, coffee, and toast",
        "cal_add_btn": "Add", "cal_analyzing": "Analyzing macros silently...",
        "meal_breakfast": "Breakfast", "meal_lunch": "Lunch", "meal_snack": "Snack", "meal_dinner": "Dinner",
        "mod4_title": "🩺 Health Dashboard & Medical Analysis", "mod4_period_label": "Select Period to Analyze",
        "mod4_period_today": "Today", "mod4_period_week": "This Week", "mod4_period_month": "This Month",
        "mod4_total_cal": "Total Calories", "mod4_gen_btn": "🩺 Generate Deep Clinical AI Analysis",
        "mod4_analyzing": "Medical AI is analyzing your nutrition...",
        "ptr_default": "🖱️ Default", "ptr_drumstick": "🍗 Drumstick", "ptr_avocado": "🥑 Avocado", "ptr_pan": "🥘 Pan", "ptr_pizza": "🍕 Pizza", "ptr_wand": "🪄 Wand", "ptr_apple": "🍎 Apple",
        "magic_pointer": "🪄 Magic Pointer", "choose_pointer": "Choose your pointer:",
        "trend_sweets": "🍰 Sweets", "trend_salty": "🥨 Salty", "trend_snacks": "🥪 Quick Snacks", "trend_breakfast": "🥣 Breakfasts", "trend_drinks": "🥤 Drinks/Smoothies",
        "btn_delete": "🗑️ Delete", "btn_edit": "✏️ Edit", "btn_save": "💾 Save",
        "manage_meals": "⚙️ Manage Daily Meals", "no_meals": "No meals logged for this day.", "manage_date": "Select date to edit"
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
        "nut_facts": "Valeurs Nutritionnelles", "nut_cal": "Calories", "nut_tfat": "Graisses Totales", "nut_sfat": "Graisses Saturées", "nut_sod": "Sodium", "nut_tcarb": "Glucides Totaux", "nut_fib": "Fibres Alimentaires", "nut_sug": "Sucres Totaux", "nut_pro": "Protéines",
        "cal_prev": "◀ Précédent", "cal_next": "Suivant ▶", "cal_weekly": "Hebdomadaire", "cal_monthly": "Mensuel",
        "cal_add_meal_title": "➕ Ajouter un repas au calendrier", "cal_ph_food": "Ex : 1 Pomme, café et toast",
        "cal_add_btn": "Ajouter", "cal_analyzing": "Analyse silencieuse des macros...",
        "meal_breakfast": "Petit-déjeuner", "meal_lunch": "Déjeuner", "meal_snack": "Goûter", "meal_dinner": "Dîner",
        "mod4_title": "🩺 Tableau de bord Santé et Analyse", "mod4_period_label": "Sélectionner la période à analyser",
        "mod4_period_today": "Aujourd'hui", "mod4_period_week": "Cette Semaine", "mod4_period_month": "Ce Mois",
        "mod4_total_cal": "Calories Totales", "mod4_gen_btn": "🩺 Générer une analyse clinique IA",
        "mod4_analyzing": "L'IA médicale analyse votre nutrition...",
        "ptr_default": "🖱️ Par défaut", "ptr_drumstick": "🍗 Pilon", "ptr_avocado": "🥑 Avocat", "ptr_pan": "🥘 Poêle", "ptr_pizza": "🍕 Pizza", "ptr_wand": "🪄 Baguette", "ptr_apple": "🍎 Pomme",
        "magic_pointer": "🪄 Pointeur Magique", "choose_pointer": "Choisissez votre pointeur :",
        "trend_sweets": "🍰 Sucreries", "trend_salty": "🥨 Salé", "trend_snacks": "🥪 En-cas", "trend_breakfast": "🥣 Petit-déj", "trend_drinks": "🥤 Boissons",
        "btn_delete": "🗑️ Supprimer", "btn_edit": "✏️ Modifier", "btn_save": "💾 Enregistrer",
        "manage_meals": "⚙️ Gérer les repas du jour", "no_meals": "Aucun repas enregistré ce jour.", "manage_date": "Sélectionner la date"
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
        "nut_facts": "Valori Nutrizionali", "nut_cal": "Calorie", "nut_tfat": "Grassi Totali", "nut_sfat": "Grassi Saturi", "nut_sod": "Sodio", "nut_tcarb": "Carboidrati Totali", "nut_fib": "Fibra Alimentare", "nut_sug": "Zuccheri Totali", "nut_pro": "Proteine",
        "cal_prev": "◀ Precedente", "cal_next": "Successivo ▶", "cal_weekly": "Settimanale", "cal_monthly": "Mensile",
        "cal_add_meal_title": "➕ Aggiungi Pasto al Calendario", "cal_ph_food": "Es: 1 Mela, caffè e toast",
        "cal_add_btn": "Aggiungi", "cal_analyzing": "Analizzando i macro...",
        "meal_breakfast": "Colazione", "meal_lunch": "Pranzo", "meal_snack": "Spuntino", "meal_dinner": "Cena",
        "mod4_title": "🩺 Dashboard Salute e Analisi Medica", "mod4_period_label": "Seleziona Periodo da Analizzare",
        "mod4_period_today": "Oggi", "mod4_period_week": "Questa Settimana", "mod4_period_month": "Questo Mese",
        "mod4_total_cal": "Calorie Totali", "mod4_gen_btn": "🩺 Genera Analisi Clinica Profonda IA",
        "mod4_analyzing": "L'IA medica sta analizzando la tua nutrizione...",
        "ptr_default": "🖱️ Predefinito", "ptr_drumstick": "🍗 Cosciotto", "ptr_avocado": "🥑 Avocado", "ptr_pan": "🥘 Padella", "ptr_pizza": "🍕 Pizza", "ptr_wand": "🪄 Bacchetta", "ptr_apple": "🍎 Mela",
        "magic_pointer": "🪄 Puntatore Magico", "choose_pointer": "Scegli il puntatore:",
        "trend_sweets": "🍰 Dolci", "trend_salty": "🥨 Salati", "trend_snacks": "🥪 Spuntini", "trend_breakfast": "🥣 Colazioni", "trend_drinks": "🥤 Bevande",
        "btn_delete": "🗑️ Elimina", "btn_edit": "✏️ Modifica", "btn_save": "💾 Salva",
        "manage_meals": "⚙️ Gestisci i Pasti del Giorno", "no_meals": "Nessun pasto registrato.", "manage_date": "Seleziona la data"
    }
}

if "selected_lang" not in st.session_state: st.session_state.selected_lang = "🇪🇸 Español"

def handle_language_change():
    new_lang = st.session_state.selected_lang
    new_lang_code = TRANSLATIONS[new_lang]["lang_code"]
    
    with st.spinner(f"Traduciendo al {new_lang_code}... / Translating..."):
        if st.session_state.get("options"):
            sys_p = f"Translate all the VALUES of this JSON array into {new_lang_code.upper()}, keeping the exact same English KEYS. Return ONLY the JSON object with an 'options' key containing the translated array."
            user_p = json.dumps({"options": st.session_state.options})
            res = groq_generic_json(sys_p, user_p)
            if res and "options" in res:
                st.session_state.options = res["options"]
                
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
                        new_user = {"username": reg_user, "pin": reg_pin, "security_question": reg_sq, "security_answer": reg_sa.lower(), "name": reg_name, "age": reg_age, "weight": reg_weight, "height": reg_height, "gender": reg_gender, "goals": reg_goals, "restrictions": reg_rest, "favorites":[], "daily_logs":{}, "weekly_planner":{}, "shopping_list":[], "meal_calendar":{}}
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
if "app_alerts" not in st.session_state: st.session_state.app_alerts =[]
# ==========================================
# SIDEBAR REDISEÑADA & PUNTERO MÁGICO
# ==========================================
with st.sidebar:
    # 1. ESCUDO CSS ABSOLUTO: Bloquea cualquier CSS de la pantalla principal
    st.markdown("""
    <style>
    /* Resetear botones en la barra lateral */
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button,
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button:hover,
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button:active,
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button:focus {
        background-image: none !important; /* Mata la imagen del stickman/varita */
        padding-top: 0 !important;
        box-shadow: none !important;
    }
    
    /* ELIMINAR las etiquetas filtradas del Home en la barra lateral (incluso en hover) */
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button::after,
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button::before,
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button:hover::after,
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button:hover::before {
        content: none !important;
        display: none !important;
    }
    
    /* Quitar animaciones base que estiran botones */
    section[data-testid="stSidebar"] div[data-testid="stColumn"] div.stButton > button p {
        transform: none !important; margin: 0 !important; font-weight: normal !important;
    }

    /* 2. ESCUDO PLANO PARA RECETAS FAVORITAS (Sin zoom, sin deformar, sin fondos filtrados) */
    section[data-testid="stSidebar"] div[data-testid="stExpanderDetails"]:has(.fav-container-marker) div.stButton > button,
    section[data-testid="stSidebar"] div[data-testid="stExpanderDetails"]:has(.fav-container-marker) div.stButton > button:hover,
    section[data-testid="stSidebar"] div[data-testid="stExpanderDetails"]:has(.fav-container-marker) div.stButton > button:active,
    section[data-testid="stSidebar"] div[data-testid="stExpanderDetails"]:has(.fav-container-marker) div.stButton > button:focus {
        transform: none !important;       /* Cero zoom */
        box-shadow: none !important;      /* Cero sombras raras */
        background-image: none !important;/* Cero imágenes del home */
        background-color: #F8FAFC !important; /* Fondo gris claro clásico */
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        min-height: 0 !important;
        padding: 5px 10px !important;
        color: #1E293B !important;
        transition: background-color 0.2s ease, border-color 0.2s ease !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpanderDetails"]:has(.fav-container-marker) div.stButton > button:hover {
        background-color: #E2E8F0 !important; /* Un poco más oscuro al pasar el ratón */
        border-color: #94A3B8 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<h2 style='text-align:center;'>👨‍🍳 Chef {user_profile['name']}</h2>", unsafe_allow_html=True)

    # FUNCIÓN AUXILIAR: Botones Circulares Perfectos con Animación de Escala y Bocadillo CSS
    def render_circle_btn(emoji, key, tooltip_text, is_selected=False):
        bg = "rgba(16, 185, 129, 0.15)" if is_selected else "transparent"
        border = "#FFD700" if is_selected else "#CBD5E1"
        
        st.markdown(f"""
        <style>
        /* Forzar visibilidad para evitar que se corten los tooltips */
        div:has(>.btn-marker-{key}),
        div:has(>.btn-marker-{key}) + div.element-container,
        div:has(>.btn-marker-{key}) + div.element-container > div.stButton {{
            overflow: visible !important;
            display: flex !important; justify-content: center !important;
        }}
        
        /* Círculos matemáticamente perfectos */
        section[data-testid="stSidebar"] div.element-container:has(.btn-marker-{key}) + div.element-container div.stButton > button {{
            width: 42px !important; min-width: 42px !important; max-width: 42px !important;
            height: 42px !important; min-height: 42px !important; max-height: 42px !important;
            border-radius: 50% !important; padding: 0 !important; margin: 0 auto !important;
            flex: 0 0 auto !important; /* Previene el estiramiento ovalado */
            background-color: {bg} !important; border: 2px solid {border} !important;
            font-size: 20px !important; color: #1E293B !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
            position: relative !important; overflow: visible !important; 
            /* Transición dinámica y suave para el hover */
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), border-color 0.2s ease, background-color 0.2s ease !important;
            transform: scale(1) !important;
        }}
        
        /* Hover Dinámico: Agrandar círculo, borde dorado, sin imágenes fantasma */
        section[data-testid="stSidebar"] div.element-container:has(.btn-marker-{key}) + div.element-container div.stButton > button:hover {{
            border-color: #FFD700 !important; 
            transform: scale(1.15) !important; /* Efecto de crecimiento estético */
            z-index: 9999 !important;
            background-image: none !important;
        }}

        /* BOCADILLO DE TEXTO (Etiqueta Centrada Arriba - Revivimos el ::after) */
        section[data-testid="stSidebar"] div.element-container:has(.btn-marker-{key}) + div.element-container div.stButton > button:hover::after {{
            content: "{tooltip_text}" !important;
            display: block !important; position: absolute !important;
            bottom: calc(100% + 10px) !important; left: 50% !important;
            transform: translateX(-50%) !important;
            background: #1E293B !important; color: #FFFFFF !important;
            padding: 6px 12px !important; border-radius: 6px !important;
            font-size: 11px !important; font-weight: 700 !important;
            white-space: nowrap !important; width: max-content !important; 
            opacity: 1 !important; visibility: visible !important; pointer-events: none !important;
            z-index: 99999 !important; box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
        }}
        /* Triángulo del Bocadillo */
        section[data-testid="stSidebar"] div.element-container:has(.btn-marker-{key}) + div.element-container div.stButton > button:hover::before {{
            content: "" !important; display: block !important; position: absolute !important;
            bottom: calc(100% + 5px) !important; left: 50% !important;
            transform: translateX(-50%) !important;
            border-width: 5px !important; border-style: solid !important;
            border-color: #1E293B transparent transparent transparent !important;
            opacity: 1 !important; visibility: visible !important; pointer-events: none !important;
            z-index: 99999 !important;
        }}
        </style>
        <div class="btn-marker-{key}" data-emoji="{emoji}"></div>
        """, unsafe_allow_html=True)
        return st.button(emoji, key=key, use_container_width=False)


    # 1. EXPANDER: PUNTERO MÁGICO (Cuadrícula 2x5)
    with st.expander("🪄 " + t.get("magic_pointer", "Puntero Mágico"), expanded=False):
        if "cursor_val" not in st.session_state: st.session_state.cursor_val = "default"
        
        # 10 cursores en total
        cursors =[
            ("default", "🖱️", t.get("ptr_default", "Predeterminado")),
            ("🍗", "🍗", t.get("ptr_drumstick", "Muslito")),
            ("🥑", "🥑", t.get("ptr_avocado", "Aguacate")),
            ("🥘", "🥘", t.get("ptr_pan", "Sartén")),
            ("🍕", "🍕", t.get("ptr_pizza", "Pizza")),
            ("🪄", "🪄", t.get("ptr_wand", "Varita")),
            ("🍎", "🍎", t.get("ptr_apple", "Manzana")),
            ("🌮", "🌮", t.get("ptr_taco", "Taco")),    
            ("🍣", "🍣", t.get("ptr_sushi", "Sushi")),  
            ("☕", "☕", t.get("ptr_coffee", "Café"))   
        ]
        
        # FILA 1 (Iconos del 0 al 4)
        cols_ptr_1 = st.columns(5)
        for i in range(5):
            with cols_ptr_1[i]:
                p_val, p_emoji, p_label = cursors[i]
                if render_circle_btn(p_emoji, f"ptr_btn_{p_val}", p_label, st.session_state.cursor_val == p_val):
                    st.session_state.cursor_val = p_val
                    st.rerun()

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True) # Espacio entre filas

        # FILA 2 (Iconos del 5 al 9)
        cols_ptr_2 = st.columns(5)
        for i in range(5, 10):
            with cols_ptr_2[i-5]:
                p_val, p_emoji, p_label = cursors[i]
                if render_circle_btn(p_emoji, f"ptr_btn_{p_val}", p_label, st.session_state.cursor_val == p_val):
                    st.session_state.cursor_val = p_val
                    st.rerun()

        # JS PARA CAMBIO INSTANTÁNEO DE PUNTERO (Evita el lag del servidor)
        st.components.v1.html("""
        <script>
        const doc = window.parent.document;
        doc.addEventListener('mousedown', function(e) {
            let btn = e.target.closest('button');
            if(!btn) return;
            let container = btn.closest('div[data-testid="element-container"]');
            if(container && container.previousElementSibling) {
                let marker = container.previousElementSibling.querySelector('[class^="btn-marker-ptr_btn_"]');
                if(marker) {
                    let emoji = marker.getAttribute('data-emoji');
                    let styleId = 'dynamic-cursor-style';
                    let oldStyle = doc.getElementById(styleId);
                    if(oldStyle) oldStyle.remove();
                    
                    if(emoji && emoji !== 'default' && emoji !== '🖱️') {
                        let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" style="font-size: 24px"><text y="24">${emoji}</text></svg>`;
                        let css = `* { cursor: url('data:image/svg+xml;utf8,${encodeURIComponent(svg)}'), auto !important; }`;
                        let style = doc.createElement('style');
                        style.id = styleId;
                        style.innerHTML = css;
                        doc.head.appendChild(style);
                    }
                }
            }
        });
        </script>
        """, height=0, width=0)

        # Respaldo Python para el Puntero (Tras el recargo de la web)
        if st.session_state.cursor_val != "default":
            st.markdown(f"""
            <style>
            * {{ cursor: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' style='font-size: 24px'><text y='24'>{st.session_state.cursor_val}</text></svg>"), auto !important; }}
            </style>
            """, unsafe_allow_html=True)

    # 2. EXPANDER: PERFIL
    with st.expander("👤 " + t["profile"], expanded=False):
        upd_weight = st.number_input(t["current_weight_label"], value=float(user_profile.get("weight",70)))
        upd_goals = st.text_area(t["profile_goals_label"], value=user_profile.get("goals",""))
        upd_rest = st.text_input(t["profile_restrictions_label"], value=user_profile.get("restrictions",""))
        if st.button(t["update_prof"], use_container_width=True):
            update_user_data(user_profile["username"], {"weight":upd_weight,"goals":upd_goals,"restrictions":upd_rest})
            st.success(t["prof_updated"])
            st.rerun()

    # 3. EXPANDER: RECETAS FAVORITAS
    with st.expander(t["favs"], expanded=False):
        # El marcador que protege esta sección específica (estático y blindado)
        st.markdown('<div class="fav-container-marker" style="display:none;"></div>', unsafe_allow_html=True)
        
        favs = user_profile.get("favorites",[])
        if favs:
            for idx, f in enumerate(favs):
                r_name = f.get('recipe_name', f.get('name', 'Receta'))
                st.markdown(f"<p style='font-size:14px; font-weight:bold; margin-bottom:5px;'>{r_name}</p>", unsafe_allow_html=True)
                
                col_c, col_d = st.columns([3, 1])
                with col_c:
                    if st.button("🍳", key=f"load_fav_{idx}", use_container_width=True, help="Cocinar esta receta"):
                        if "ingredients" in f:
                            st.session_state.full_recipe = f
                            st.session_state.current_page = "mod1"
                            st.session_state.step = "recipe_view"
                            st.rerun()
                        else:
                            st.warning("Receta antigua. Faltan pasos.")
                with col_d:
                    if st.button("🗑️", key=f"del_fav_{idx}", use_container_width=True, help=t["btn_delete"]):
                        favs.pop(idx)
                        update_user_data(user_profile["username"], {"favorites": favs})
                        st.rerun()
                st.divider()
        else: 
            st.info(t["no_favs"])

    # 4. EXPANDER: TENDENCIAS NUTRICIONALES
    with st.expander(t.get("news_title", "Tendencias"), expanded=True):
        trend_keys =["trend_sweets", "trend_salty", "trend_snacks", "trend_breakfast", "trend_drinks"]
        trend_emojis =["🍰", "🥨", "🥪", "🥣", "🥤"]
        if "trend_idx" not in st.session_state: st.session_state.trend_idx = 0
        
        cols_trend = st.columns(5)
        for i, (key, emoji) in enumerate(zip(trend_keys, trend_emojis)):
            with cols_trend[i]:
                is_selected = (st.session_state.trend_idx == i)
                tooltip_text = t.get(key, key)
                if render_circle_btn(emoji, f"trend_btn_{i}", tooltip_text, is_selected):
                    st.session_state.trend_idx = i
                    st.rerun()
                    
        current_key = trend_keys[st.session_state.trend_idx]
        st.markdown(f"<div style='text-align:center; font-weight:800; color:#10B981; font-size:14px; margin:10px 0;'>{t.get(current_key, current_key)}</div>", unsafe_allow_html=True)
                
        news_items = fetch_daily_healthy_recipes(lang_code, current_key)
        if news_items:
            for news in news_items:
                r_title = news.get('title', 'Receta')
                r_summary = news.get('summary', '')[:90] + "..."
                r_url = news.get('url', '#')
                st.markdown(f"""
                <div style="background: #F8FAFC; padding:10px; border-radius:8px; margin-bottom:10px; border:1px solid #E2E8F0;">
                    <h4 style="margin:0;font-size:13px;font-weight:700;color:#1E293B;line-height:1.2;">{r_title}</h4>
                    <p style="font-size:11px;margin-top:4px;margin-bottom:6px;line-height:1.3;color:#475569;">{r_summary}</p>
                    <a href="{r_url}" target="_blank" style="font-size:11px;color:#10B981;font-weight:800;text-decoration:none;">Ver receta →</a>
                </div>
                """, unsafe_allow_html=True)
        else: 
            st.warning("No hay tendencias hoy.")
            
        if st.button("🔄 Actualizar Noticias", key="btn_refresh_news", use_container_width=True):
            fetch_daily_healthy_recipes.clear()
            st.rerun()

    # 5. EXPANDER: ALERTAS Y NOTIFICACIONES
    with st.expander("🔔 Alertas del Sistema", expanded=False):
        if not st.session_state.app_alerts:
            st.info("No hay alertas recientes. ¡Todos los sistemas funcionan perfectamente!")
        else:
            if st.button("🧹 Limpiar historial", use_container_width=True):
                st.session_state.app_alerts =[]
                st.rerun()
            for alerta in st.session_state.app_alerts:
                st.markdown(f"""
                <div style="background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 8px; margin-bottom: 8px; border-radius: 4px; font-size: 12px; color: #475569;">
                    {alerta}
                </div>
                """, unsafe_allow_html=True)

    st.divider()
    if st.button("🚪 " + t["logout"], type="secondary", use_container_width=True): 
        logout()
# ==========================================
# HEADER PRINCIPAL
# ==========================================
st.markdown(f"<h1 class='brand-logo'>NutriAI</h1>", unsafe_allow_html=True)

# ==========================================
# RUTEO DE PÁGINAS (DASHBOARD REDISEÑADO)
# ==========================================
if st.session_state.current_page == "home":
    
    if lang_code == "Spanish":
        d_m1, d_m2 = "Descubre recetas con lo que tienes en casa.", "El stickman lleva tu inventario e IA."
        d_m3, d_m4 = "Planifica tu semana y controla tus macros.", "Reportes clínicos médicos generados por IA."
    elif lang_code == "French":
        d_m1, d_m2 = "Recettes magiques avec vos ingrédients.", "Gérez votre inventaire avec l'IA."
        d_m3, d_m4 = "Planifiez la semaine et suivez vos macros.", "Rapports de santé générés par l'IA."
    elif lang_code == "Italian":
        d_m1, d_m2 = "Ricette magiche con i tuoi ingredienti.", "Gestisci l'inventario con l'IA."
        d_m3, d_m4 = "Pianifica la settimana e traccia i macro.", "Report medici generati dall'IA."
    else: 
        d_m1, d_m2 = "Discover recipes with your ingredients.", "Manage your inventory using AI."
        d_m3, d_m4 = "Plan your week and track your macros.", "Clinical health reports generated by AI."

    st.markdown(f"""
    <style>
    div[data-testid="stColumn"] button, div[data-testid="column"] button {{
        background: #FFFFFF !important;
        background-image: none !important; 
        border-radius: 20px !important;
        border: 2px solid #F8FAFC !important;
        box-shadow: 8px 8px 16px rgba(0,0,0,0.06), -8px -8px 16px rgba(255,255,255,0.8) !important;
        color: #1E293B !important;
        min-height: 240px !important;
        width: 100% !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        position: relative !important;
        overflow: hidden !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        background-repeat: no-repeat !important;
        background-position: center top 35px !important;
        padding-top: 110px !important;
    }}

    div[data-testid="stColumn"] button p, div[data-testid="column"] button p {{
        margin: 0 !important;
        transition: transform 0.4s ease, color 0.4s ease !important;
        z-index: 2;
    }}

    div[data-testid="stColumn"] button:hover, div[data-testid="column"] button:hover {{
        transform: translateY(-8px) scale(1.02) !important;
        box-shadow: 16px 16px 32px rgba(16,185,129,0.15), -16px -16px 32px #ffffff !important;
        border-color: #10B981 !important;
        background-position: center top 20px !important;
    }}

    /* CAMBIO: El título se vuelve NEGRO/GRIS MUY OSCURO para contraste total */
    div[data-testid="stColumn"] button:hover p, div[data-testid="column"] button:hover p {{
        transform: translateY(-15px) !important;
        color: #0F172A !important; 
        font-weight: 900 !important;
    }}

    /* CAMBIO: Descripción con gris muy oscuro y fondo de soporte semitransparente por si se cruza con el icono */
    div[data-testid="stColumn"] button::after, div[data-testid="column"] button::after {{
        position: absolute !important;
        bottom: 20px !important;
        left: 10px !important;
        right: 10px !important;
        text-align: center !important;
        font-size: 14.5px !important;
        color: #1E293B !important; /* Gris super oscuro */
        font-weight: 700 !important; /* Letra más gruesa */
        opacity: 0 !important;
        transform: translateY(20px) !important;
        transition: all 0.4s ease 0.1s !important;
        white-space: normal !important;
        line-height: 1.4 !important;
        padding: 5px !important;
        border-radius: 8px !important;
        background: rgba(255, 255, 255, 0.6) !important; /* Ligero halo para que siempre sea legible */
    }}

    div[data-testid="stColumn"] button:hover::after, div[data-testid="column"] button:hover::after {{
        opacity: 1 !important;
        transform: translateY(0) !important;
    }}

    /* COLUMNA 1, BOTÓN 1 (Cocina Mágica) */
    div[data-testid="stColumn"]:nth-child(1) div.element-container:nth-child(1) button,
    div[data-testid="column"]:nth-child(1) div.element-container:nth-child(1) button {{
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2310b981' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M6 13.87A4 4 0 0 1 7.41 6a5.11 5.11 0 0 1 1.05-1.54 5 5 0 0 1 7.08 0A5.11 5.11 0 0 1 16.59 6 4 4 0 0 1 18 13.87V21H6Z'/><line x1='6' y1='17' x2='18' y2='17'/><g><animateTransform attributeName='transform' type='rotate' values='-10 12 12; 10 12 12; -10 12 12' dur='2s' repeatCount='indefinite'/><circle cx='12' cy='3' r='1' fill='%2310b981'><animate attributeName='opacity' values='0;1;0' dur='1.5s' repeatCount='indefinite'/></circle></g></svg>") !important;
        background-size: 80px !important;
    }}
    div[data-testid="stColumn"]:nth-child(1) div.element-container:nth-child(1) button::after,
    div[data-testid="column"]:nth-child(1) div.element-container:nth-child(1) button::after {{ content: "{d_m1}" !important; }}

    /* COLUMNA 1, BOTÓN 2 (Mis Menús) */
    div[data-testid="stColumn"]:nth-child(1) div.element-container:nth-child(2) button,
    div[data-testid="column"]:nth-child(1) div.element-container:nth-child(2) button {{
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23f59e0b' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='4' width='18' height='18' rx='2' ry='2'/><line x1='16' y1='2' x2='16' y2='6'/><line x1='8' y1='2' x2='8' y2='6'/><line x1='3' y1='10' x2='21' y2='10'/><path d='M8 15 l2 2 l4 -4'><animate attributeName='stroke-dasharray' values='0,20; 20,0; 20,0' dur='2s' repeatCount='indefinite'/></path></svg>") !important;
        background-size: 80px !important;
    }}
    div[data-testid="stColumn"]:nth-child(1) div.element-container:nth-child(2) button::after,
    div[data-testid="column"]:nth-child(1) div.element-container:nth-child(2) button::after {{ content: "{d_m3}" !important; }}

    /* COLUMNA 2, BOTÓN 1 (Mi Compra - Stickman) */
    div[data-testid="stColumn"]:nth-child(2) div.element-container:nth-child(1) button,
    div[data-testid="column"]:nth-child(2) div.element-container:nth-child(1) button {{
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 40' stroke='%233b82f6' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'><g><animateTransform attributeName='transform' type='translate' values='-3,0; 3,0; -3,0' dur='1.2s' repeatCount='indefinite'/><path d='M28 15 h6 l4 10 h12'/><line x1='32' y1='25' x2='48' y2='25'/><circle cx='36' cy='30' r='2' fill='%233b82f6'/><circle cx='46' cy='30' r='2' fill='%233b82f6'/><circle cx='18' cy='8' r='3'/><path d='M18 11 v10'/><path d='M18 21 l-4 8'><animate attributeName='d' values='M18 21 l-4 8; M18 21 l4 8; M18 21 l-4 8' dur='0.4s' repeatCount='indefinite'/></path><path d='M18 21 l6 7'><animate attributeName='d' values='M18 21 l6 7; M18 21 l-2 8; M18 21 l6 7' dur='0.4s' repeatCount='indefinite'/></path><path d='M18 14 l10 3'/></g></svg>") !important;
        background-size: 110px !important;
    }}
    div[data-testid="stColumn"]:nth-child(2) div.element-container:nth-child(1) button::after,
    div[data-testid="column"]:nth-child(2) div.element-container:nth-child(1) button::after {{ content: "{d_m2}" !important; }}

    /* COLUMNA 2, BOTÓN 2 (Mi Salud) */
    div[data-testid="stColumn"]:nth-child(2) div.element-container:nth-child(2) button,
    div[data-testid="column"]:nth-child(2) div.element-container:nth-child(2) button {{
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ef4444' stroke='%23ef4444' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z'><animate attributeName='transform' type='scale' values='1;1.15;1;1;1' dur='1.2s' repeatCount='indefinite' transform-origin='12 12'/></path><polyline points='9 12 11 12 12 9 13 15 14 12 16 12' stroke='white' stroke-width='1' fill='none'><animate attributeName='stroke-dasharray' values='0,20; 20,0; 20,0' dur='2s' repeatCount='indefinite'/></polyline></svg>") !important;
        background-size: 80px !important;
    }}
    div[data-testid="stColumn"]:nth-child(2) div.element-container:nth-child(2) button::after,
    div[data-testid="column"]:nth-child(2) div.element-container:nth-child(2) button::after {{ content: "{d_m4}" !important; }}
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
                # ¡Ahora guardamos todo el diccionario 'recipe' entero!
                favs.append(recipe) 
                update_user_data(user_profile["username"], {"favorites": favs})
                st.toast("¡Receta completa guardada en Favoritos! ⭐")
        with c_act2:
            if st.button(t.get("cal_add_meal_title", "📅 Añadir al Calendario de Hoy"), type="primary", use_container_width=True):
                m_type, m_col = get_current_meal_info()
                entry = {
                    "type": m_type,
                    "food": recipe.get("recipe_name", ""),
                    "calories": extract_number(m.get('calories', '0')),
                    "protein": extract_number(m.get('protein', '0')),
                    "fat": extract_number(m.get('total_fat', '0')),
                    "carbs": extract_number(m.get('total_carbs', '0')),
                    "color": m_col
                }
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                add_to_meal_calendar(user_profile["username"], today_str, entry)
                st.toast("¡Añadido al calendario de hoy!", icon="✅")
                
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
# MÓDULO 3: CALENDARIO NUTRICIONAL INTERACTIVO
# ==========================================
elif st.session_state.current_page == "mod3":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    
    if "cal_ref_date" not in st.session_state: st.session_state.cal_ref_date = datetime.date.today()
    if "cal_view" not in st.session_state: st.session_state.cal_view = "weekly"

    # Diccionarios de Traducción Manual Inmunes al Servidor
    meses_dict = {
        "Spanish":["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "English":["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        "French":["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
        "Italian":["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    }
    
    dias_cortos_dict = {
        "Spanish":["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"],
        "English":["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "French":["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
        "Italian":["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    }

    mes_actual = meses_dict.get(lang_code, meses_dict["English"])[st.session_state.cal_ref_date.month]
    año_actual = st.session_state.cal_ref_date.year

    # Controles Superiores
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 2, 2, 1])
    with col_nav1:
        if st.button(t["cal_prev"], use_container_width=True):
            if st.session_state.cal_view == "weekly": st.session_state.cal_ref_date -= timedelta(days=7)
            else:
                first_day = st.session_state.cal_ref_date.replace(day=1)
                st.session_state.cal_ref_date = first_day - timedelta(days=1)
            st.rerun()
    with col_nav2:
        view_opts = {"weekly": t["cal_weekly"], "monthly": t["cal_monthly"]}
        st.session_state.cal_view = st.radio("Vista", ["weekly", "monthly"], format_func=lambda x: view_opts[x], horizontal=True, label_visibility="collapsed")
    with col_nav3:
        st.markdown(f"<h3 style='text-align:center; margin:0;'>{mes_actual} {año_actual}</h3>", unsafe_allow_html=True)
    with col_nav4:
        if st.button(t["cal_next"], use_container_width=True):
            if st.session_state.cal_view == "weekly": st.session_state.cal_ref_date += timedelta(days=7)
            else:
                next_month = st.session_state.cal_ref_date.replace(day=28) + timedelta(days=4)
                st.session_state.cal_ref_date = next_month.replace(day=1)
            st.rerun()

    st.write("")
    user_cal = user_profile.get("meal_calendar") or {}
    if not isinstance(user_cal, dict): user_cal = {}

    # RENDER: VISTA SEMANAL
    if st.session_state.cal_view == "weekly":
        start_of_week = st.session_state.cal_ref_date - timedelta(days=st.session_state.cal_ref_date.weekday())
        days =[start_of_week + timedelta(days=i) for i in range(7)]
        cols = st.columns(7)
        
        lista_dias = dias_cortos_dict.get(lang_code, dias_cortos_dict["English"])
        
        for i, d in enumerate(days):
            with cols[i]:
                is_today = (d == datetime.date.today())
                bg_title = "#10B981" if is_today else "#F8F9FA"
                txt_color = "#FFFFFF" if is_today else "#1E293B"
                
                # Nombre del día exacto del diccionario
                nombre_dia = lista_dias[d.weekday()]
                
                st.markdown(f"<div style='text-align:center; font-weight:bold; padding:8px; background:{bg_title}; color:{txt_color}; border-radius:8px; margin-bottom:10px;'>{nombre_dia} {d.day}</div>", unsafe_allow_html=True)
                
                d_str = d.strftime("%Y-%m-%d")
                meals = user_cal.get(d_str,[])
                for m in meals:
                    c = m.get("color", "#1E293B")
                    st.markdown(f"<div style='background:{c}15; color:{c}; padding:6px 8px; border-radius:8px; font-size:13px; font-weight:600; margin-bottom:6px; border:1px solid {c}30; text-align:center; word-wrap: break-word;'>{m.get('food', '')}</div>", unsafe_allow_html=True)

    # RENDER: VISTA MENSUAL
    else:
        first_day = st.session_state.cal_ref_date.replace(day=1)
        next_month = first_day.replace(day=28) + timedelta(days=4)
        last_day = next_month - timedelta(days=next_month.day)
        start_cal = first_day - timedelta(days=first_day.weekday())
        end_cal = last_day + timedelta(days=(6 - last_day.weekday()))
        
        day_names =[t["day_1"], t["day_2"], t["day_3"], t["day_4"], t["day_5"], t["day_6"], t["day_7"]]
        head_cols = st.columns(7)
        for i, d_name in enumerate(day_names):
            with head_cols[i]: st.markdown(f"<div style='text-align:center; font-size:12px; font-weight:bold; color:#64748B;'>{d_name}</div>", unsafe_allow_html=True)
        
        curr = start_cal
        while curr <= end_cal:
            cols = st.columns(7)
            for i in range(7):
                with cols[i]:
                    d_str = curr.strftime("%Y-%m-%d")
                    is_current_month = curr.month == st.session_state.cal_ref_date.month
                    opacity = "1" if is_current_month else "0.4"
                    
                    st.markdown(f"<div style='opacity:{opacity}; text-align:right; font-size:14px; font-weight:bold; color:#1E293B; margin-bottom:5px;'>{curr.day}</div>", unsafe_allow_html=True)
                    
                    meals = user_cal.get(d_str,[])
                    for m in meals:
                        c = m.get("color", "#1E293B")
                        st.markdown(f"<div style='opacity:{opacity}; background:{c}20; color:{c}; padding:2px 4px; border-radius:4px; font-size:10px; font-weight:700; margin-bottom:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{m.get('food', '')}</div>", unsafe_allow_html=True)
                curr += timedelta(days=1)
            st.divider()

    # FORMULARIO IA INGRESO MANUAL
    st.divider()
    st.subheader(t["cal_add_meal_title"])
    
    meal_options = {
        f"🍳 {t['meal_breakfast']}": (t['meal_breakfast'], "#F97316"),
        f"🥗 {t['meal_lunch']}": (t['meal_lunch'], "#10B981"),
        f"🥪 {t['meal_snack']}": (t['meal_snack'], "#8B5CF6"),
        f"🥩 {t['meal_dinner']}": (t['meal_dinner'], "#3B82F6")
    }
    
    selected_meal_ui = st.radio("Tipo de Comida", list(meal_options.keys()), horizontal=True, label_visibility="collapsed")
    m_type, m_col = meal_options[selected_meal_ui]

    c_f1, c_f2, c_f3 = st.columns([3, 1, 1])
    with c_f1: input_food = st.text_input("", placeholder=t["cal_ph_food"], label_visibility="collapsed")
    with c_f2: input_date = st.date_input("", value=datetime.date.today(), label_visibility="collapsed")
    with c_f3:
        if st.button(t["cal_add_btn"], type="primary", use_container_width=True):
            if input_food:
                with st.spinner(t["cal_analyzing"]):
                    sys_p = "Estima los macros de este alimento. Devuelve un JSON ESTRICTO: {'calories': 100, 'protein': 2, 'fat': 0, 'carbs': 20}"
                    parsed = groq_generic_json(sys_p, f"Alimento: {input_food}")
                    if parsed:
                        entry = {
                            "type": m_type,
                            "food": input_food.capitalize(),
                            "calories": parsed.get('calories',0),
                            "protein": parsed.get('protein',0),
                            "fat": parsed.get('fat',0),
                            "carbs": parsed.get('carbs',0),
                            "color": m_col
                        }
                        add_to_meal_calendar(user_profile["username"], input_date.strftime("%Y-%m-%d"), entry)
                        st.rerun()

    # GESTIÓN DE COMIDAS (Editar / Eliminar)
    st.divider()
    st.markdown(f"<h3 style='text-align:center;'>{t['manage_meals']}</h3>", unsafe_allow_html=True)
    
    col_md1, col_md2 = st.columns([1, 2])
    with col_md1:
        manage_date = st.date_input(t["manage_date"], value=datetime.date.today(), key="manage_cal_date")
        manage_date_str = manage_date.strftime("%Y-%m-%d")
    
    with col_md2:
        day_meals = user_cal.get(manage_date_str,[])
        if not day_meals:
            st.info(t["no_meals"])
        else:
            for idx, m in enumerate(day_meals):
                with st.expander(f"{m.get('type', 'Comida')} - {m.get('food')} ({m.get('calories')} kcal)"):
                    e_food = st.text_input("Nombre de la comida", value=m.get('food'), key=f"e_food_{idx}")
                    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                    e_cal = c_m1.number_input("Calorías", value=int(m.get('calories', 0)), key=f"e_cal_{idx}")
                    e_pro = c_m2.number_input("Prot. (g)", value=int(m.get('protein', 0)), key=f"e_pro_{idx}")
                    e_fat = c_m3.number_input("Grasa (g)", value=int(m.get('fat', 0)), key=f"e_fat_{idx}")
                    e_car = c_m4.number_input("Carb. (g)", value=int(m.get('carbs', 0)), key=f"e_car_{idx}")
                    
                    col_sav, col_del = st.columns(2)
                    if col_sav.button(t["btn_save"], key=f"save_m_{idx}", use_container_width=True, type="primary"):
                        day_meals[idx].update({"food": e_food, "calories": e_cal, "protein": e_pro, "fat": e_fat, "carbs": e_car})
                        user_cal[manage_date_str] = day_meals
                        update_user_data(user_profile["username"], {"meal_calendar": user_cal})
                        st.toast("¡Comida actualizada!")
                        st.rerun()
                        
                    if col_del.button(t["btn_delete"], key=f"del_m_{idx}", use_container_width=True):
                        day_meals.pop(idx)
                        user_cal[manage_date_str] = day_meals
                        update_user_data(user_profile["username"], {"meal_calendar": user_cal})
                        st.toast("¡Comida eliminada!")
                        st.rerun()

# ==========================================
# MÓDULO 4: DASHBOARD DE ANÁLISIS PROFUNDO MÉDICO
# ==========================================
# ==========================================
# MÓDULO 4: DASHBOARD DE ANÁLISIS PROFUNDO MÉDICO
# ==========================================
elif st.session_state.current_page == "mod4":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    
    st.markdown(f"<h2>{t['mod4_title']}</h2>", unsafe_allow_html=True)
    
    periods_list = ["today", "week", "month"]
    period_map = {"today": t["mod4_period_today"], "week": t["mod4_period_week"], "month": t["mod4_period_month"]}
    periodo_key = st.selectbox(t["mod4_period_label"], periods_list, format_func=lambda x: period_map[x])
    
    today = datetime.date.today()
    if periodo_key == "today":
        start_date, end_date = today, today
    elif periodo_key == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    else: # month
        start_date = today.replace(day=1)
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
        
    user_cal = user_profile.get("meal_calendar") or {}
    if not isinstance(user_cal, dict): user_cal = {}
    
    # Acumuladores generales y por tipo de comida
    t_cal = t_pro = t_fat = t_car = 0
    consumed_foods =[]
    meals_breakdown = {}
    
    curr = start_date
    while curr <= end_date:
        d_str = curr.strftime("%Y-%m-%d")
        meals = user_cal.get(d_str,[])
        for m in meals:
            m_type = m.get("type", "Otro")
            
            # Suma general
            t_cal += m.get("calories", 0)
            t_pro += m.get("protein", 0)
            t_fat += m.get("fat", 0)
            t_car += m.get("carbs", 0)
            consumed_foods.append(f"{m.get('food')} ({m.get('calories')} kcal)")
            
            # Suma por tipo de comida
            if m_type not in meals_breakdown:
                meals_breakdown[m_type] = {"Calorías": 0, "Proteínas (g)": 0, "Grasas (g)": 0, "Carbos (g)": 0}
            meals_breakdown[m_type]["Calorías"] += m.get("calories", 0)
            meals_breakdown[m_type]["Proteínas (g)"] += m.get("protein", 0)
            meals_breakdown[m_type]["Grasas (g)"] += m.get("fat", 0)
            meals_breakdown[m_type]["Carbos (g)"] += m.get("carbs", 0)
            
        curr += timedelta(days=1)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # LAYOUT DIVIDIDO: 70% Izquierda (Datos), 30% Derecha (Tarjeta Flip)
    col_left, col_right = st.columns([7, 3], gap="large")
    
    with col_left:
        # Totales generales
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"🔥 {t['mod4_total_cal']}", f"{t_cal} kcal")
        c2.metric(f"🍗 {t['mac_pro']}", f"{t_pro} g")
        c3.metric(f"🥑 {t['mac_fat']}", f"{t_fat} g")
        c4.metric(f"🍞 {t['mac_car']}", f"{t_car} g")
        st.divider()
        
        # Tabla de desglose por comidas
        st.markdown("### 📊 Desglose por Comidas")
        if meals_breakdown:
            df_meals = pd.DataFrame.from_dict(meals_breakdown, orient='index')
            st.dataframe(df_meals.style.format("{:.0f}"), use_container_width=True)
        else:
            st.info("No hay comidas registradas en este período.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botón de Generación IA
        if st.button(t["mod4_gen_btn"], type="primary", use_container_width=True):
            with st.spinner(t["mod4_analyzing"]):
                food_list_str = ', '.join(consumed_foods[:50]) if consumed_foods else 'Ninguno registrado'
                sys_eval = f"""
                Eres un Médico Nutricionista empático y experto evaluando a {user_profile['name']} ({user_profile['weight']}kg, Objetivo: {user_profile['goals']}).
                Datos del período ({period_map[periodo_key]}): {t_cal} kcal totales, {t_pro}g proteína, {t_fat}g grasa, {t_car}g carbos.
                Alimentos consumidos: {food_list_str}.
                
                Genera un JSON ESTRICTO con la siguiente estructura:
                {{
                    "score": <entero del 0 al 100 evaluando la nutrición global>,
                    "funny_comment": "<Comentario médico ingenioso y divertido sobre su nota (max 15 palabras)>",
                    "strengths": ["<Punto fuerte 1>", "<Punto fuerte 2>"],
                    "weaknesses":["<Debilidad a mejorar 1>", "<Debilidad a mejorar 2>"],
                    "markdown_report": "<Un análisis estructurado y amigable en Markdown. Usa encabezados (###), listas (*) y dobles saltos de línea (\\n\\n) para separar los párrafos. Evita el exceso de emojis.>"
                }}
                Traduce TODO el contenido del JSON al {lang_code}.
                """
                
                eval_res = groq_generic_json(sys_eval, "Genera el reporte médico y la tarjeta ahora.")
                if eval_res:
                    st.session_state.mod4_eval_res = eval_res
                else:
                    st.error("Error al generar el análisis. Reintenta.")

    with col_right:
        # LÓGICA DE LA TARJETA ANIMADA (FLIP CARD)
        if "mod4_eval_res" in st.session_state:
            res = st.session_state.mod4_eval_res
            score = res.get("score", 0)
            
            # Determinar color según puntuación
            if score >= 90: bg, text_col = "linear-gradient(135deg, #FFD700, #F59E0B)", "#000000" # Oro
            elif score >= 80: bg, text_col = "linear-gradient(135deg, #A855F7, #7E22CE)", "#FFFFFF" # Morado
            elif score >= 70: bg, text_col = "linear-gradient(135deg, #3B82F6, #1D4ED8)", "#FFFFFF" # Azul
            elif score >= 60: bg, text_col = "linear-gradient(135deg, #84CC16, #4D7C0F)", "#000000" # Verde Claro
            elif score >= 50: bg, text_col = "linear-gradient(135deg, #22C55E, #15803D)", "#FFFFFF" # Verde Oscuro
            elif score >= 40: bg, text_col = "linear-gradient(135deg, #F97316, #C2410C)", "#FFFFFF" # Naranja
            elif score >= 30: bg, text_col = "linear-gradient(135deg, #EF4444, #B91C1C)", "#FFFFFF" # Rojo
            elif score >= 20: bg, text_col = "linear-gradient(135deg, #92400E, #78350F)", "#FFFFFF" # Marrón
            else: bg, text_col = "linear-gradient(135deg, #334155, #0F172A)", "#FFFFFF" # Negro
            
            # Listas limpias con punto a media altura (&bull;)
            str_html = "".join([f"<li style='margin-bottom:6px; padding-left:15px; text-indent:-15px;'>&bull; {s}</li>" for s in res.get("strengths", [])])
            weak_html = "".join([f"<li style='margin-bottom:6px; padding-left:15px; text-indent:-15px;'>&bull; {w}</li>" for w in res.get("weaknesses", [])])
            
            card_html = f"""
            <style>
            body {{ margin:0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: transparent; }}
            .flip-container {{ width: 100%; height: 420px; perspective: 1000px; cursor: pointer; }}
            .flip-card {{ width: 100%; height: 100%; position: relative; transition: transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275); transform-style: preserve-3d; }}
            .flip-container.flipped .flip-card {{ transform: rotateY(180deg); }}
            .front, .back {{ width: 100%; height: 100%; position: absolute; backface-visibility: hidden; border-radius: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 25px; box-sizing: border-box; text-align: center; box-shadow: 0 15px 35px rgba(0,0,0,0.15); }}
            
            /* Front (Misterio/Brillante) */
            .front {{ background: linear-gradient(135deg, #1E293B, #0F172A); color: white; border: 2px solid #38BDF8; animation: glow 2.5s infinite alternate; }}
            .front h3 {{ font-size: 24px; margin: 0 0 15px 0; }}
            .front p {{ color: #94A3B8; font-size: 14px; margin:0; line-height:1.5; }}
            .pulse-icon {{ font-size: 50px; margin-bottom: 20px; animation: bounce 2s infinite; }}
            
            /* Back (Resultados Elegantes) */
            .back {{ background: {bg}; color: {text_col}; transform: rotateY(180deg); border: 2px solid rgba(255,255,255,0.2); }}
            .score {{ font-size: 70px; font-weight: 900; margin: 0; line-height: 1; text-shadow: 2px 2px 10px rgba(0,0,0,0.2); }}
            .comment {{ font-size: 15px; font-style: italic; margin: 15px 0; font-weight: 600; opacity: 0.9; }}
            .lists-container {{ text-align: left; width: 100%; font-size: 13px; font-weight: 500; background: rgba(0,0,0,0.1); padding: 18px; border-radius: 12px; }}
            .lists-container ul {{ padding-left: 0; list-style: none; margin: 0 0 12px 0; line-height: 1.4; }}
            .list-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; opacity: 0.8; display: block; }}
            
            @keyframes glow {{ 0% {{ box-shadow: 0 0 10px #38BDF820; }} 100% {{ box-shadow: 0 0 30px #38BDF880; }} }}
            @keyframes bounce {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
            </style>

            <div class="flip-container" id="card" onclick="this.classList.toggle('flipped')">
                <div class="flip-card">
                    <div class="front">
                        <div class="pulse-icon">✨</div>
                        <h3>¡Análisis Listo!</h3>
                        <p>Toca la carta para revelar<br>tu puntuación y desglose.</p>
                    </div>
                    <div class="back">
                        <h1 class="score">{score}</h1>
                        <p class="comment">"{res.get('funny_comment', '')}"</p>
                        <div class="lists-container">
                            <span class="list-title">Puntos Fuertes</span>
                            <ul>{str_html}</ul>
                            <span class="list-title">A Mejorar</span>
                            <ul style="margin:0;">{weak_html}</ul>
                        </div>
                    </div>
                </div>
            </div>
            """
            # Renderizar la tarjeta clickeable
            st.components.v1.html(card_html, height=440)
            
        else:
            # Estado "Misterioso" antes de darle a generar
            placeholder_html = """
            <style>
            body { margin:0; background: transparent; }
            .mystery-card { width: 100%; height: 420px; border-radius: 20px; background: linear-gradient(135deg, #F8FAFC, #E2E8F0); border: 2px dashed #CBD5E1; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 30px; text-align: center; color: #64748B; transition: all 0.3s ease; }
            .mystery-card:hover { border-color: #3B82F6; background: #F1F5F9; transform: translateY(-5px); box-shadow: 0 10px 25px rgba(59,130,246,0.1); }
            .mystery-icon { font-size: 60px; margin-bottom: 20px; filter: grayscale(100%); opacity: 0.5; }
            </style>
            <div class="mystery-card">
                <div class="mystery-icon">🔮</div>
                <h3 style="margin:0 0 10px 0; color: #334155;">Tarjeta Desactivada</h3>
                <p style="margin:0; font-size:14px; line-height:1.5;">Haz clic en el botón de la izquierda para que la IA escanee tu perfil clínico y active esta tarjeta.</p>
            </div>
            """
            st.components.v1.html(placeholder_html, height=440)

    # REPORTE DETALLADO (Renderizado Nativo en Markdown)
    if "mod4_eval_res" in st.session_state:
        st.divider()
        st.markdown(f"### ✨ Análisis Nutricional")
        
        # Le aplicamos un poco de color sutil a las listas y textos para que sea amigable
        st.markdown("""
        <style>
        .report-content p, .report-content li { color: #475569; font-size: 1.05rem; line-height: 1.7; }
        .report-content h1, .report-content h2, .report-content h3 { color: #1E293B; margin-top: 25px; }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="report-content">', unsafe_allow_html=True)
        # Renderizado nativo: Esto garantiza que los #, * y saltos de línea funcionen perfectamente.
        st.markdown(st.session_state.mod4_eval_res.get('markdown_report', ''))
        st.markdown('</div>', unsafe_allow_html=True)
