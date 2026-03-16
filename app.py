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

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y PWA
# ==========================================
st.set_page_config(page_title="NutriAI | Chef Inteligente", page_icon="🌿", layout="wide")

# Inyección PWA (Fuerza a Chrome a reconocerla como App Instalable)
st.components.v1.html("""
<script>
    var manifest = {
        "name": "NutriAI Chef", "short_name": "NutriAI",
        "start_url": window.location.pathname, "display": "standalone",
        "background_color": "#0f172a", "theme_color": "#0f172a",
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
    var meta2 = document.createElement('meta'); meta2.name = "apple-mobile-web-app-status-bar-style"; meta2.content = "black-translucent"; document.head.appendChild(meta2);
</script>
""", height=0, width=0)

# ==========================================
# CSS PREMIUM (Glassmorphism, Botones & Contraste)
# ==========================================
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.95)), 
                    url("https://images.unsplash.com/photo-1498837167922-41cfa6f5ae8f?auto=format&fit=crop&w=1920&q=80") no-repeat center center fixed !important;
        background-size: cover !important; color: #f1f5f9;
    }
    
    /* 🔥 Contenedor Principal (Oscuro) */
    .block-container {
        background: rgba(30, 41, 59, 0.45) !important;
        backdrop-filter: blur(16px) !important; -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* 🔥 BARRA LATERAL REDISEÑADA (Beige Glassmorphism) */[data-testid="stSidebar"] {
        background: rgba(245, 245, 220, 0.4) !important;
        backdrop-filter: blur(16px) !important; -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Forzar texto oscuro SOLO en la barra lateral para garantizar contraste */[data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4, 
    [data-testid="stSidebar"] span,[data-testid="stSidebar"] label,
    [data-testid="stSidebar"] strong, [data-testid="stSidebar"] div {
        color: #1e293b !important;
    }

    /* Ajuste de inputs y botones dentro del Sidebar para encajar con fondo claro */
    [data-testid="stSidebar"] div[data-baseweb="input"] > div, 
    [data-testid="stSidebar"] div[data-baseweb="textarea"] > div {
        background-color: rgba(255, 255, 255, 0.5) !important;
        border: 1px solid rgba(30, 41, 59, 0.2) !important; color: #1e293b !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="input"] input, 
    [data-testid="stSidebar"] div[data-baseweb="textarea"] textarea { color: #1e293b !important; }
    
    /* Expanders del Sidebar */
    [data-testid="stSidebar"][data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.3) !important;
        border: 1px solid rgba(30, 41, 59, 0.1) !important;
    }[data-testid="stSidebar"] [data-testid="stExpander"] summary {
        background-color: rgba(245, 245, 220, 0.6) !important; border-radius: 8px !important;
    }

    /* Textos Principal Oscuros */
    h1, h2, h3, h4, p, label, .stMarkdown { color: #f8fafc !important; }

    /* 🔥 Botones Principales Premium */
    .stButton > button {
        background: linear-gradient(45deg, #10b981, #3b82f6) !important;
        color: white !important; border: none !important; border-radius: 8px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important; font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button * { color: white !important; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important; }

    /* Botones de eliminar (Lista de compra) */
    button[key^="del_"] { background: transparent !important; box-shadow: none !important; color: #ef4444 !important; font-size: 1.2rem !important; }
    button[key^="del_"]:hover { transform: scale(1.1) !important; }

    /* Botones Secundarios */
    .stDownloadButton > button, button[kind="secondaryFormSubmit"], button[kind="secondary"] {
        background: rgba(30, 41, 59, 0.8) !important; 
        border: 1px solid #3b82f6 !important; color: #ffffff !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"] * { color: #ffffff !important; }
    
    /* 🔥 Tarjetas Grandes del Dashboard */
    .dashboard-grid .stButton > button {
        height: 160px !important; font-size: 22px !important;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        border-radius: 20px !important;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9)) !important;
        border: 2px solid rgba(255,255,255,0.1) !important;
    }
    .dashboard-grid .stButton > button:hover { border: 2px solid #10b981 !important; transform: scale(1.02); }

    /* 🔥 Desplegables Main UI (Alto Contraste) */
    .block-container[data-testid="stExpander"] {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 10px !important;
    }
    .block-container [data-testid="stExpander"] summary {
        background-color: rgba(15, 23, 42, 0.9) !important; color: #ffffff !important; border-radius: 10px !important;
    }

    /* Inputs Oscuros Main UI */
    .block-container div[data-baseweb="input"] > div, .block-container div[data-baseweb="select"] > div {
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255,255,255,0.2) !important; border-radius: 8px !important; color: white !important;
    }
    .block-container div[data-baseweb="input"] input, .block-container div[data-baseweb="select"] div { color: white !important; }

    /* 🔥 Flechitas Visibles */
    button[data-testid="stSidebarCollapseButton"] { background-color: rgba(245, 245, 220, 0.9) !important; border-radius: 50% !important; }
    button[data-testid="stSidebarCollapseButton"] svg { fill: #1e293b !important; color: #1e293b !important; }
    button[data-testid="collapsedControl"] { background-color: rgba(15, 23, 42, 0.6) !important; border-radius: 50% !important; }
    button[data-testid="collapsedControl"] svg { fill: #ffffff !important; color: #ffffff !important; }

    .brand-logo { font-family: 'Georgia', serif; font-size: 3rem; font-weight: bold; text-align: center; margin-bottom: 0px; background: -webkit-linear-gradient(45deg, #10b981, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
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

if "auth_checked" not in st.session_state:
    st.session_state.auth_checked = False
if "current_username" not in st.session_state:
    st.session_state.current_username = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

if not st.session_state.auth_checked:
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
    with col_s2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if lottie_cooking: st_lottie(lottie_cooking, height=300, key="splash_anim")
        phrases =["Encendiendo los fogones...", "Preparando tu cocina inteligente...", "Afilando los cuchillos...", "Calentando las sartenes..."]
        st.markdown(f"<h2 style='text-align:center;'>{random.choice(phrases)}</h2>", unsafe_allow_html=True)
        
    js_val = st_javascript('window.localStorage.getItem("nutri_username") || window.sessionStorage.getItem("nutri_username") || "NONE"')
    
    if js_val == 0:
        st.stop()
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
    if today not in logs:
        logs[today] = []
    logs[today].append(entry_data)
    update_user_data(username, {"daily_logs": logs})

# ==========================================
# SISTEMA MULTIDIOMA Y TEXTOS
# ==========================================
TRANSLATIONS = {
    "🇪🇸 Español": {
        "lang_code": "Spanish",
        "title": "¡Hola {name}! ¿Qué cocinamos hoy? 🍲", "subtitle": "Tu ecosistema inteligente de nutrición y cocina.",
        "assistant_msg": "¿Qué hay en la despensa? ¡Hagamos magia!", "avail_ing_label": "Ingredientes disponibles hoy", "avoid_today_label": "¿Algo que evitar hoy?", "find_btn": "🍳 Buscar Recetas Mágicas",
        "analyzing": "El Chef está analizando...", "here_options": "Opciones para ti:", "diff": "Dificultad", "time": "Tiempo", "health": "Salud",
        "cook_btn": "Cocinar {}", "loading_recipe": "Calculando macros exactos...", "start_over": "← Empezar de Nuevo", "note": "Nota del Nutricionista:",
        "ingredients": "🛒 Ingredientes", "save_fav": "⭐ Guardar en Favoritos", "saved": "¡Guardado!", "instructions": "👨‍🍳 Preparación", "adjust_title": "⚖️ Ajustar Macros",
        "adjust_sub": "¿Necesitas otras cantidades?", "adjust_ph": "Ej: 'Añade 20g de proteína'", "recalc_btn": "Recalcular", "recalculating": "Ajustando receta...",
        "profile": "👤 Mi Perfil", "update_prof": "Actualizar Perfil", "prof_updated": "¡Perfil actualizado!", "favs": "⭐ Favoritos", "no_favs": "Aún no hay favoritos.",
        "logout": "Cerrar Sesión", "news_title": "📰 Tendencias Nutricionales", "feed_title": "Últimas Noticias 🔥", "cook_this": "Cocinar esto 🍳", "download_btn": "⬇️ Descargar",
        "keep_logged_in": "Mantener sesión iniciada", "chef_recom": "🌟 RECOMENDACIÓN ESTRELLA DEL CHEF 🌟",
        "auth_app_name": "NutriAI 🌿", "auth_subtitle": "Tu chef y nutricionista personal impulsado por IA.", "tab_login": "🔑 Iniciar Sesión", "tab_register": "📝 Registrarse", "tab_recover": "🆘 Recuperar PIN",
        "username_label_login": "Usuario", "pin_label_login": "PIN", "login_btn": "Entrar a la Cocina 🚀", "login_error": "Usuario o PIN incorrectos.",
        "reg_section1": "1. Datos de Acceso", "create_user_label": "Crea un Usuario único", "create_pin_label": "Crea un PIN corto", "security_question_label": "Pregunta de Seguridad",
        "security_options":["¿Nombre de tu primera mascota?", "¿Ciudad de nacimiento?", "¿Nombre de tu colegio?"], "security_answer_label": "Respuesta",
        "reg_section2": "2. Tu Perfil Clínico", "name_label": "Nombre Real", "age_label": "Edad", "weight_label": "Peso (kg)", "height_label": "Altura (cm)", "gender_label": "Género", "gender_options":["Masculino", "Femenino", "Otro"],
        "reg_section3": "3. Objetivos", "goals_label": "Objetivo principal", "rest_label": "Restricciones Crónicas", "create_account_btn": "Crear Cuenta 🚀", "username_taken": "Usuario en uso.",
        "account_created": "¡Cuenta creada!", "fill_required": "Rellena los campos.", "forgot_pin_text": "¿Olvidaste tu PIN?", "search_user_label": "Introduce tu Usuario",
        "search_user_btn": "Buscar", "user_found": "Usuario encontrado.", "user_not_found": "Usuario no encontrado.", "recover_question_prefix": "Pregunta:", "your_answer_label": "Respuesta", "new_pin_label": "Nuevo PIN",
        "change_pin_btn": "Cambiar PIN", "pin_changed_success": "¡PIN cambiado!", "wrong_answer": "Incorrecta.", "current_weight_label": "Peso Actual (kg)",
        "profile_goals_label": "Objetivos", "profile_restrictions_label": "Restricciones", "macro_protein": "Proteínas", "macro_fat": "Grasas", "macro_carbs": "Carbohidratos",
        "dash_mod1": "🍳\nCocina Inteligente", "dash_mod2": "🛒\nLista de Compras", "dash_mod3": "📅\nPlanificador", "dash_mod4": "📊\nResumen Diario", "back_home": "🏠 Volver al Menú",
        "add_to_log": "📝 Añadir al registro de hoy", "log_success": "¡Añadido al registro de hoy!",
        "shop_title": "Lista de la Compra Dinámica", "search_web_label": "¿Qué te gustaría preparar?", "search_web_btn": "🔍 Buscar y Extraer Ingredientes",
        "shop_list_title": "Tu Inventario de Compra", "add_item_btn": "Añadir Item", "clear_list": "🗑️ Vaciar Lista",
        "plan_title": "Planificador Semanal", "save_plan": "💾 Guardar Planificación", "plan_saved": "¡Planificación guardada!",
        "nutri_title": "Resumen Nutricional Diario", "manual_log_label": "¿Qué has comido fuera de la app? (Ej: 1 Manzana)", "manual_log_btn": "➕ Añadir",
        "eval_btn": "🩺 Evaluar mi día", "total_today": "Total de hoy", "analyzing_nutri": "Evaluando datos médicos...",
        # Nuevas categorías y textos Módulo 2
        "cat_produce": "🥦 Frutas y Verduras", "cat_dairy": "🥛 Lácteos y Huevos", "cat_white_meat": "🍗 Carnes Blancas", 
        "cat_red_meat": "🥩 Carnes Rojas", "cat_seafood": "🐟 Pescados y Mariscos", "cat_pantry": "🥫 Despensa y Granos", "cat_other": "🛒 Otros",
        "add_to_list": "Añadir a la lista", "delete_item": "Eliminar", "type_food": "Escribe un alimento suelto..."
    },
    "🇬🇧 English": {
        "lang_code": "English", "title": "Hi {name}! What are we cooking today? 🍲", "subtitle": "Your smart nutrition ecosystem.",
        "assistant_msg": "What's in the pantry?", "avail_ing_label": "Available ingredients", "avoid_today_label": "Anything to avoid?", "find_btn": "🍳 Find Magic Recipes",
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
        "profile_goals_label": "Goals", "profile_restrictions_label": "Restrictions", "macro_protein": "Protein", "macro_fat": "Fat", "macro_carbs": "Carbs",
        "dash_mod1": "🍳\nSmart Cooking", "dash_mod2": "🛒\nShopping List", "dash_mod3": "📅\nWeekly Planner", "dash_mod4": "📊\nDaily Summary", "back_home": "🏠 Back to Home",
        "add_to_log": "📝 Add to today's log", "log_success": "Added to log!",
        "shop_title": "Dynamic Shopping List", "search_web_label": "What do you want to cook?", "search_web_btn": "🔍 Search & Extract",
        "shop_list_title": "Your Groceries", "add_item_btn": "Add Item", "clear_list": "🗑️ Clear List",
        "plan_title": "Weekly Planner", "save_plan": "💾 Save Plan", "plan_saved": "Plan saved!",
        "nutri_title": "Daily Nutritional Summary", "manual_log_label": "Ate outside the app? (e.g., 1 Apple)", "manual_log_btn": "➕ Add",
        "eval_btn": "🩺 Evaluate my day", "total_today": "Total today", "analyzing_nutri": "Evaluating medical data...",
        "cat_produce": "🥦 Fruits & Vegetables", "cat_dairy": "🥛 Dairy & Eggs", "cat_white_meat": "🍗 White Meat", 
        "cat_red_meat": "🥩 Red Meat", "cat_seafood": "🐟 Seafood", "cat_pantry": "🥫 Pantry & Grains", "cat_other": "🛒 Other",
        "add_to_list": "Add to list", "delete_item": "Delete", "type_food": "Type a food item..."
    },
    "🇫🇷 Français": {
        "lang_code": "French", "title": "Bonjour {name} !", "subtitle": "Votre écosystème nutritionnel.",
        "assistant_msg": "Qu'y a-t-il dans le frigo ?", "avail_ing_label": "Ingrédients disponibles", "avoid_today_label": "À éviter ?", "find_btn": "🍳 Trouver",
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
        "profile_goals_label": "Objectifs", "profile_restrictions_label": "Restrictions", "macro_protein": "Protéines", "macro_fat": "Graisses", "macro_carbs": "Glucides",
        "dash_mod1": "🍳\nCuisine Intelligente", "dash_mod2": "🛒\nListe de Courses", "dash_mod3": "📅\nPlanificateur", "dash_mod4": "📊\nRésumé Quotidien", "back_home": "🏠 Retour",
        "add_to_log": "📝 Ajouter au journal", "log_success": "Ajouté !", "shop_title": "Liste de Courses", "search_web_label": "Que voulez-vous cuisiner ?", "search_web_btn": "🔍 Extraire",
        "shop_list_title": "Inventaire", "add_item_btn": "Ajouter", "clear_list": "🗑️ Vider", "plan_title": "Planificateur", "save_plan": "💾 Sauvegarder", "plan_saved": "Sauvegardé !",
        "nutri_title": "Résumé Nutritionnel", "manual_log_label": "Mangé dehors ?", "manual_log_btn": "➕ Ajouter", "eval_btn": "🩺 Évaluer", "total_today": "Total", "analyzing_nutri": "Évaluation...",
        "cat_produce": "🥦 Fruits et Légumes", "cat_dairy": "🥛 Produits Laitiers", "cat_white_meat": "🍗 Viande Blanche", 
        "cat_red_meat": "🥩 Viande Rouge", "cat_seafood": "🐟 Poissons et Fruits de Mer", "cat_pantry": "🥫 Garde-manger", "cat_other": "🛒 Autre",
        "add_to_list": "Ajouter", "delete_item": "Supprimer", "type_food": "Écrivez un aliment..."
    },
    "🇮🇹 Italiano": {
        "lang_code": "Italian", "title": "Ciao {name}!", "subtitle": "Il tuo ecosistema nutrizionale.",
        "assistant_msg": "Cosa c'è in dispensa?", "avail_ing_label": "Ingredienti", "avoid_today_label": "Da evitare?", "find_btn": "🍳 Trova Ricette",
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
        "profile_goals_label": "Obiettivi", "profile_restrictions_label": "Restrizioni", "macro_protein": "Proteine", "macro_fat": "Grassi", "macro_carbs": "Carboidrati",
        "dash_mod1": "🍳\nCucina Intelligente", "dash_mod2": "🛒\nLista della Spesa", "dash_mod3": "📅\nPianificatore", "dash_mod4": "📊\nRiassunto Quotidiano", "back_home": "🏠 Torna alla Home",
        "add_to_log": "📝 Aggiungi al diario", "log_success": "Aggiunto!", "shop_title": "Lista della Spesa", "search_web_label": "Cosa vuoi cucinare?", "search_web_btn": "🔍 Estrai",
        "shop_list_title": "La tua spesa", "add_item_btn": "Aggiungi", "clear_list": "🗑️ Svuota lista", "plan_title": "Pianificatore", "save_plan": "💾 Salva", "plan_saved": "Salvato!",
        "nutri_title": "Riassunto Nutrizionale", "manual_log_label": "Mangiato fuori?", "manual_log_btn": "➕ Aggiungi", "eval_btn": "🩺 Valuta la mia giornata", "total_today": "Totale di oggi", "analyzing_nutri": "Valutazione...",
        "cat_produce": "🥦 Frutta e Verdura", "cat_dairy": "🥛 Latticini e Uova", "cat_white_meat": "🍗 Carne Bianca", 
        "cat_red_meat": "🥩 Carne Rossa", "cat_seafood": "🐟 Pesce e Frutti di Mare", "cat_pantry": "🥫 Dispensa e Cereali", "cat_other": "🛒 Altro",
        "add_to_list": "Aggiungi alla lista", "delete_item": "Elimina", "type_food": "Scrivi un alimento..."
    }
}

t_trending =[{"name": "Ratatouille", "emoji": "🍅", "desc": "Un clásico lleno de vitaminas y muy bajo en calorías."}, {"name": "Risotto de Setas", "emoji": "🍄", "desc": "Cremoso, reconfortante y perfecto para cargar energía."}, {"name": "Poke Bowl de Salmón", "emoji": "🥗", "desc": "Fresco, rico en omega-3 y grasas saludables."}, {"name": "Shakshuka", "emoji": "🍳", "desc": "Huevos en salsa de tomate especiada. Alto en proteína."}]

if "selected_lang" not in st.session_state: st.session_state.selected_lang = "🇪🇸 Español"
cols_top = st.columns([1, 6, 1])
with cols_top[2]: st.selectbox("", options=list(TRANSLATIONS.keys()), key="selected_lang", label_visibility="collapsed")
t = TRANSLATIONS[st.session_state.selected_lang]
lang_code = t["lang_code"]

# ==========================================
# PANTALLA DE AUTENTICACIÓN
# ==========================================
if not st.session_state.current_username:
    st.markdown(f"<h1 class='brand-logo'>{t['auth_app_name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='brand-subtitle'>{t['auth_subtitle']}</p>", unsafe_allow_html=True)
    
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
# FUNCIONES IA (GROQ) Y EXTRACCIÓN
# ==========================================
def call_ai_json(prompt, expected_format_hint, lang_code, u_prof, avail_ing="", avoid_tdy="", num_recipes=3):
    client = Groq(api_key=st.secrets.get("GROQ_API_KEY"))
    system_prompt = f"""
    You are a Michelin-star Executive Chef and Clinical Nutritionist.
    Your client is {u_prof['name']}. Profile: {u_prof['age']} y/o, {u_prof['weight']} kg, {u_prof['height']} cm, Gender: {u_prof['gender']}.
    Main goal: "{u_prof['goals']}". Restrictions: "{u_prof['restrictions']}".[DYNAMIC GENERATION] Generate exactly {num_recipes} recipe options.[CHEF'S RECOMMENDATION - CRITICAL] Analyze the client's profile/goals. Tag exactly ONE recipe with `"is_chefs_recommendation": true` that is the healthiest for them. All others `false`.
    """
    if avail_ing: system_prompt += f"\n[GOLDEN RULE] Recipes MUST be based EXCLUSIVELY on: {avail_ing}. Do NOT invent main ingredients."
    if avoid_tdy: system_prompt += f"\n[STRICT PROHIBITION] Under NO circumstances include: {avoid_tdy}."

    system_prompt += f"\nCRITICAL: Reply entirely in {lang_code}. ALWAYS valid JSON format."
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": system_prompt + "\n" + expected_format_hint}, {"role": "user", "content": prompt}], response_format={"type": "json_object"}, temperature=0.7)
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

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
    text = f"=== {recipe['recipe_name'].upper()} ===\n🌍 Origen/Estilo: {recipe.get('region', 'Global')}\n\n--- {t_dict['ingredients'].upper()} ---\n"
    for ing in recipe["ingredients"]: text += f"• {ing['qty']} de {ing['item']}\n"
    text += f"\n--- {t_dict['instructions'].upper()} ---\n"
    for i, step in enumerate(recipe["instructions"]): text += f"{i+1}. {step}\n"
    m = recipe['macros']
    text += f"\n--- MACROS ---\nCalorías: {m.get('calories', '0')} | Proteína: {m.get('protein', '0g')} | Grasas: {m.get('total_fat', '0g')} | Carbohidratos: {m.get('total_carbs', '0g')}\n"
    return text

# ==========================================
# FUNCIÓN CACHÉ PARA NOTICIAS (DuckDuckGo)
# ==========================================
@st.cache_data(ttl=datetime.timedelta(days=3))
def fetch_nutrition_news(lang_code):
    query_map = {
        "Spanish": "últimas tendencias nutrición alimentación comida saludable",
        "English": "latest nutrition healthy food diet trends news",
        "French": "actualités nutrition tendances alimentation saine",
        "Italian": "notizie nutrizione tendenze dieta sana"
    }
    query = query_map.get(lang_code, "healthy nutrition trends")
    try:
        results = list(DDGS().text(query, max_results=3))
        return results
    except Exception as e:
        return[]

# ==========================================
# UI: BARRA LATERAL REDISEÑADA
# ==========================================
with st.sidebar:
    st.markdown(f"<h2 style='text-align:center;'>👨‍🍳 Chef {user_profile['name']}</h2>", unsafe_allow_html=True)
    with st.expander(t["profile"], expanded=False):
        upd_weight = st.number_input(t["current_weight_label"], value=float(user_profile.get("weight", 70.0)))
        upd_goals = st.text_area(t["profile_goals_label"], value=user_profile.get("goals", ""))
        upd_rest = st.text_input(t["profile_restrictions_label"], value=user_profile.get("restrictions", ""))
        if st.button(t["update_prof"], use_container_width=True):
            update_user_data(user_profile["username"], {"weight": upd_weight, "goals": upd_goals, "restrictions": upd_rest})
            st.success(t["prof_updated"])
            st.rerun()
            
    st.divider()
    st.subheader(t["favs"])
    favs = user_profile.get("favorites",[])
    if favs:
        for f in favs:
            with st.expander(f["name"]): st.write(f"🔥 {f['calories']} | 💪 {f['protein']}")
    else: st.info(t["no_favs"])
        
    st.divider()
    with st.expander(t["news_title"], expanded=False):
        st.subheader(t["feed_title"])
        news_items = fetch_nutrition_news(lang_code)
        
        if news_items:
            for news in news_items:
                st.markdown(f"""
                <div style='background: rgba(255, 255, 255, 0.4); padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 1px solid rgba(0,0,0,0.05);'>
                    <h4 style='margin:0; font-size:14px; font-weight:700;'>{news.get('title', '')}</h4>
                    <p style='font-size:12px; margin-top:6px; margin-bottom:6px; line-height:1.4;'>{news.get('body', '')[:90]}...</p>
                    <a href='{news.get('href', '#')}' target='_blank' style='font-size:12px; color:#2563eb; font-weight:bold; text-decoration:none;'>Leer más →</a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No hay tendencias disponibles hoy.")
                
    st.divider()
    if st.button(t["logout"], type="secondary", use_container_width=True):
        logout()

# ==========================================
# HEADER PRINCIPAL
# ==========================================
st.markdown(f"<h1 class='brand-logo'>NutriAI</h1>", unsafe_allow_html=True)

# ==========================================
# RUTEO DE PÁGINAS (DASHBOARD)
# ==========================================
if st.session_state.current_page == "home":
    st.markdown(f"<h2 style='text-align:center;'>{t['title'].format(name=user_profile['name'])}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; font-size:1.2rem; color:#cbd5e1;'>{t['subtitle']}</p><br>", unsafe_allow_html=True)
    
    st.markdown('<div class="dashboard-grid">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button(t["dash_mod1"], use_container_width=True):
            st.session_state.current_page = "mod1"
            st.session_state.step = "input"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t["dash_mod3"], use_container_width=True):
            st.session_state.current_page = "mod3"
            st.rerun()
    with c2:
        if st.button(t["dash_mod2"], use_container_width=True):
            st.session_state.current_page = "mod2"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(t["dash_mod4"], use_container_width=True):
            st.session_state.current_page = "mod4"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

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
                ing_count = len([x for x in re.split(r',|\sy\s|\sand\s|\set\s', available_ingredients) if x.strip()])
                n_recipes = 5 if ing_count >= 4 else 3
                
                lottie_placeholder = st.empty()
                with lottie_placeholder.container():
                    st.markdown("<br>", unsafe_allow_html=True)
                    if lottie_cooking: st_lottie(lottie_cooking, height=200, key="loading_anim_1")
                    st.markdown(f"<h3 style='text-align:center;'>{t['analyzing']}</h3>", unsafe_allow_html=True)
                
                prompt = f"Generate {n_recipes} recipe options strictly using the available ingredients provided."
                format_hint = """{ "options":[ { "name": "Recipe", "hero_emoji": "🥘", "difficulty": "Easy", "time": "20 mins", "health_score": 9, "description": "Desc", "is_chefs_recommendation": true } ] }"""
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
            with st.container():
                if opt.get("is_chefs_recommendation", False):
                    st.markdown(f"""
                    <div class="golden-card">
                        <div class="golden-card-content">
                            <span style="color:#D4AF37; font-weight:bold; letter-spacing:2px; font-size:14px;">{t['chef_recom']}</span>
                            <h1 style="font-size: 55px; margin: 5px 0;">{opt.get('hero_emoji', '🍽️')}</h1>
                            <h2 style="margin: 0; color: white;">{opt['name']}</h2>
                            <p style="color:#cbd5e1; font-style:italic; margin-top:5px;">Alineado 100% con tu perfil de salud</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<h1 style='text-align:center; font-size:40px; margin:0;'>{opt.get('hero_emoji', '🍽️')}</h1><h3 style='text-align:center;'>{opt['name']}</h3>", unsafe_allow_html=True)
                
                st.caption(f"**{t['diff']}:** {opt['difficulty']} | **{t['time']}:** {opt['time']} | **{t['health']}:** {opt['health_score']}/10")
                st.write(opt['description'])
                
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
            st.markdown(f"<h3 style='text-align:center;'>{t['loading_recipe'].format(st.session_state.selected_option['name'])}</h3>", unsafe_allow_html=True)
        
        # PROMPT MEJORADO: Tono pedagógico y macros detallados
        prompt = f"Genera la receta completa para '{st.session_state.selected_option['name']}'. Actúa como un chef amigable y pedagógico. Explica el porqué de cada paso de forma detallada, clara y cercana para que no haya dudas."
        format_hint = """{ 
            "recipe_name": "Name", 
            "region": "Style", 
            "hero_emoji": "🥘", 
            "ingredients_emojis": "🍅🧅", 
            "nutritionist_note": "Empathetic note", 
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
            "ingredients":[{"item": "Ing", "qty": "200g"}], 
            "instructions":[
                "1. 🍳 Empezaremos calentando la sartén a fuego medio para que los sabores se liberen lentamente...", 
                "2. 🔪 Ahora cortamos..."
            ] 
        }"""
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
                st.session_state.step, st.session_state.options, st.session_state.full_recipe, st.session_state.avail_ing, st.session_state.avoid_tdy = "input", None, None, "", ""
                st.rerun()
        with col_btn2:
            txt_data = format_recipe_for_download(recipe, t)
            st.download_button(label=t["download_btn"], data=txt_data, file_name=f"{recipe['recipe_name'].replace(' ', '_')}.txt", mime="text/plain", use_container_width=True)

        st.markdown(f"<p class='hero-emoji'>{recipe.get('hero_emoji', '🍽️')}</p><h2 style='text-align:center;'>{recipe['recipe_name']}</h2><h4 style='text-align:center; color:#cbd5e1;'>🌍 {recipe.get('region', 'Global')}</h4><h3 style='text-align:center; letter-spacing: 5px;'>{recipe.get('ingredients_emojis', '')}</h3>", unsafe_allow_html=True)
        st.info(f"**{t['note']}** {recipe.get('nutritionist_note', '')}")
        st.divider()
        
        col_label, col_chart = st.columns(2)
        m = recipe['macros']
        
        with col_label:
            # ETIQUETA NUTRICIONAL DETALLADA TIPO FDA
            st.markdown(f"""
            <div class="nutrition-label">
                <h2>Nutrition Facts</h2>
                <div class="nut-row thick"><span class="nut-bold">Calories</span> <span class="nut-bold">{m.get('calories', '0')}</span></div>
                <div class="nut-row"><span class="nut-bold">Total Fat</span> {m.get('total_fat', '0g')}</div>
                <div class="nut-row" style="padding-left: 1.5rem;">Saturated Fat {m.get('saturated_fat', '0g')}</div>
                <div class="nut-row"><span class="nut-bold">Sodium</span> {m.get('sodium', '0mg')}</div>
                <div class="nut-row"><span class="nut-bold">Total Carbohydrate</span> {m.get('total_carbs', '0g')}</div>
                <div class="nut-row" style="padding-left: 1.5rem;">Dietary Fiber {m.get('fiber', '0g')}</div>
                <div class="nut-row" style="padding-left: 1.5rem;">Total Sugars {m.get('sugars', '0g')}</div>
                <div class="nut-row thick"><span class="nut-bold">Protein</span> <span class="nut-bold">{m.get('protein', '0g')}</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_chart:
            # GRÁFICO PLOTLY CON LEYENDA Y TEXTOS EN BLANCO
            macro_df = pd.DataFrame({
                "Macro":[t.get("macro_protein", "Protein"), t.get("macro_fat", "Fat"), t.get("macro_carbs", "Carbs")], 
                "Gramos":[extract_number(m.get('protein', '0g')), extract_number(m.get('total_fat', '0g')), extract_number(m.get('total_carbs', '0g'))]
            })
            if macro_df['Gramos'].sum() > 0:
                fig = px.pie(macro_df, values='Gramos', names='Macro', hole=0.55, color_discrete_sequence=['#ff6b6b', '#feca57', '#48dbfb'])
                fig.update_traces(textfont_color='white')
                fig.update_layout(
                    margin=dict(t=20, b=20, l=20, r=20), 
                    showlegend=True, 
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", 
                        y=-0.3, 
                        xanchor="center", 
                        x=0.5,
                        font=dict(color='white') # Leyenda forzada a color blanco
                    ), 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='white') # Fuente general del gráfico en blanco
                )
                st.plotly_chart(fig, use_container_width=True)
        
        c_act1, c_act2 = st.columns(2)
        with c_act1:
            if st.button(t["save_fav"], use_container_width=True):
                favs = user_profile.get("favorites",[])
                favs.append({"name": recipe["recipe_name"], "calories": m.get('calories', '0'), "protein": m.get('protein', '0g')})
                update_user_data(user_profile["username"], {"favorites": favs})
                st.toast(t["saved"])
        with c_act2:
            if st.button(t["add_to_log"], type="primary", use_container_width=True):
                entry = {"name": recipe["recipe_name"], "calories": extract_number(m.get('calories', '0')), "protein": extract_number(m.get('protein', '0')), "fat": extract_number(m.get('total_fat', '0')), "carbs": extract_number(m.get('total_carbs', '0'))}
                append_to_daily_log(user_profile["username"], entry)
                st.toast(t["log_success"], icon="✅")
                
        with st.expander("🛒 " + t["ingredients"], expanded=True):
            for ing in recipe["ingredients"]: st.markdown(f"- **{ing['qty']}** {ing['item']}")
                
        with st.expander("👨‍🍳 " + t["instructions"], expanded=True):
            for i, step in enumerate(recipe["instructions"]): 
                st.write(f"{step}") # Se asume que el JSON ya trae el número y el emoji

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
# MÓDULO 2: LISTA DE LA COMPRA & BÚSQUEDA WEB
# ==========================================
# ==========================================
# MÓDULO 2: LISTA DE LA COMPRA E INVENTARIO
# ==========================================
elif st.session_state.current_page == "mod2":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    st.markdown(f"<h2 style='text-align:center;'>{t['shop_title']}</h2>", unsafe_allow_html=True)
    
    # 1. Input Manual Elegante con Clasificación Groq
    st.markdown("<br>", unsafe_allow_html=True)
    col_in, col_btn = st.columns([4, 1])
    with col_in:
        new_item = st.text_input("Ingrediente", placeholder=t["type_food"], label_visibility="collapsed")
    with col_btn:
        add_pressed = st.button(t["add_to_list"], type="primary", use_container_width=True)
        
    if add_pressed and new_item:
        with st.spinner("Categorizando alimento..."):
            sys_prompt = "Eres un organizador de despensas experto. Categoriza el alimento dado por el usuario en EXACTAMENTE UNA de estas categorías JSON estrictas: 'cat_produce', 'cat_dairy', 'cat_white_meat', 'cat_red_meat', 'cat_seafood', 'cat_pantry', 'cat_other'. Devuelve un JSON: {\"category\": \"cat_...\"}."
            parsed = groq_generic_json(sys_prompt, f"Alimento: {new_item}")
            
            category = "cat_other"
            if parsed and "category" in parsed:
                category = parsed["category"]
                
            shop_list = user_profile.get("shopping_list",[])
            # Limpieza en caso de existir la estructura "legacy"
            if isinstance(shop_list, list) and len(shop_list) > 0 and "category" not in shop_list[0]:
                shop_list =[]
                
            shop_list.append({"item": new_item.capitalize(), "category": category})
            update_user_data(user_profile["username"], {"shopping_list": shop_list})
            st.rerun()

    st.divider()
    st.subheader(t["shop_list_title"])
    
    shop_list = user_profile.get("shopping_list",[])
    
    if not shop_list or not isinstance(shop_list, list) or (len(shop_list)>0 and "category" not in shop_list[0]):
        st.info("🛒 Tu lista de la compra está limpia y vacía.")
    else:
        # 2. Agrupación por Categoría Estricta
        categorized = {}
        for idx, obj in enumerate(shop_list):
            cat = obj.get("category", "cat_other")
            if cat not in categorized: categorized[cat] = []
            categorized[cat].append((idx, obj.get("item", "")))
            
        # 3. Visualización Ordenada por Expander y Eliminar 1 a 1
        category_order =["cat_produce", "cat_dairy", "cat_white_meat", "cat_red_meat", "cat_seafood", "cat_pantry", "cat_other"]
        
        for cat in category_order:
            if cat in categorized and categorized[cat]:
                items_in_cat = categorized[cat]
                # Título traducido dinámicamente + conteo
                with st.expander(f"{t.get(cat, cat)} ({len(items_in_cat)})", expanded=True):
                    for idx, item_name in items_in_cat:
                        col_item, col_del = st.columns([6, 1])
                        with col_item:
                            st.markdown(f"<p style='margin-top: 5px; font-weight: 500; font-size: 1.1rem;'>• {item_name}</p>", unsafe_allow_html=True)
                        with col_del:
                            # Botón minimalista para borrar
                            if st.button("❌", key=f"del_{idx}"):
                                shop_list.pop(idx)
                                update_user_data(user_profile["username"], {"shopping_list": shop_list})
                                st.rerun()

    # Botón Global de Vaciar Lista
    if isinstance(shop_list, list) and len(shop_list) > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        col_space, col_clear = st.columns([3, 1])
        with col_clear:
            if st.button(t["clear_list"], type="secondary", use_container_width=True):
                update_user_data(user_profile["username"], {"shopping_list":

# ==========================================
# MÓDULO 3: PLANIFICADOR SEMANAL
# ==========================================
elif st.session_state.current_page == "mod3":
    if st.button(t["back_home"], type="secondary"): go_home()
    st.divider()
    st.markdown(f"<h2>{t['plan_title']}</h2>", unsafe_allow_html=True)
    
    planner = user_profile.get("weekly_planner") or {}
    days =["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    new_plan = {}
    for day in days:
        new_plan[day] = st.text_input(f"📅 {day}", value=planner.get(day, ""), placeholder="Ej: Pollo a la plancha / Descanso")
        
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
    
    # Calcular totales
    t_cal = sum(item.get("calories", 0) for item in today_data)
    t_pro = sum(item.get("protein", 0) for item in today_data)
    t_fat = sum(item.get("fat", 0) for item in today_data)
    t_car = sum(item.get("carbs", 0) for item in today_data)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 Calorías", f"{t_cal} kcal")
    c2.metric("🍗 Proteínas", f"{t_pro} g")
    c3.metric("🥑 Grasas", f"{t_fat} g")
    c4.metric("🍞 Carbos", f"{t_car} g")
    
    with st.expander("Ver detalle de hoy", expanded=True):
        if not today_data: st.write("No has registrado nada hoy.")
        for d in today_data:
            st.write(f"- **{d['name']}**: {d['calories']} kcal (P:{d['protein']}g | G:{d['fat']}g | C:{d['carbs']}g)")

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
