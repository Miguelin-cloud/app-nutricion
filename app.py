import streamlit as st
import json
import os
import datetime
import re
import pandas as pd
import plotly.express as px
from groq import Groq
import extra_streamlit_components as stx
from supabase import create_client, Client

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y CSS (Mobile-First)
# ==========================================
# Usamos layout="wide" para que las columnas respiren mejor en PC. 
# En móvil, Streamlit automáticamente apila las columnas de forma nativa.
st.set_page_config(page_title="Smart AI Nutritionist", page_icon="🍲", layout="wide")

st.markdown("""
    <style>
    .hero-emoji { font-size: 80px; text-align: center; margin: 0; padding: 0; line-height: 1.2; }
    .golden-card {
        background: linear-gradient(135deg, #FFDF00 0%, #D4AF37 100%);
        padding: 2px; border-radius: 12px; margin-bottom: 10px;
    }
    .golden-card-content {
        background-color: #FFFAEC; padding: 15px; border-radius: 10px; text-align: center; color: #333;
    }
    .nutrition-label {
        border: 2px solid #111; padding: 15px; background-color: white; color: black;
        font-family: 'Arial', sans-serif; border-radius: 8px; width: 100%; margin: auto auto 20px auto;
    }
    .nutrition-label h2 { margin: 0; font-size: 24px; font-weight: 900; border-bottom: 8px solid #111; padding-bottom: 5px; color: black; }
    .nut-row { display: flex; justify-content: space-between; border-bottom: 1px solid #999; padding: 4px 0; font-size: 15px; }
    .nut-row.thick { border-bottom: 4px solid #111; }
    .nut-row.indent { padding-left: 15px; font-size: 14px; }
    .nut-bold { font-weight: bold; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    .feed-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #e9ecef; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CONEXIÓN A SUPABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        st.error("Faltan las credenciales de Supabase en st.secrets.")
        st.stop()
    return create_client(url, key)

supabase = init_supabase()

# ==========================================
# SISTEMA MULTIDIOMA Y TEXTOS
# ==========================================
TRANSLATIONS = {
    "🇪🇸 Español": {
        "lang_code": "Spanish",
        "login_sub": "Tu nutricionista inteligente. Inicia sesión o regístrate para continuar.",
        "tab_login": "🔑 Iniciar Sesión", "tab_reg": "📝 Registrarse", "tab_rec": "🆘 Recuperar PIN",
        "user_label": "Usuario (Ej: miguel123)", "pin_label": "PIN (Contraseña)",
        "enter_btn": "Entrar", "login_err": "Usuario o PIN incorrectos.",
        "title": "¡Hola {name}! ¿Qué cocinamos hoy? 🍲",
        "subtitle": "Dime qué ingredientes tienes y crearé la comida perfecta para tus objetivos.",
        "assistant_msg": "Escribe tus ingredientes abajo. ¡Hagamos algo sano y delicioso!",
        "input_placeholder": "Ej: Pechuga de pollo, arroz, brócoli...",
        "find_btn": "🔍 Buscar Recetas",
        "analyzing": "Analizando ingredientes...",
        "here_options": "Opciones para ti:",
        "diff": "Dificultad", "time": "Tiempo", "health": "Salud",
        "cook_btn": "Cocinar {}", "loading_recipe": "Calculando macros para {}...",
        "start_over": "← Empezar de Nuevo", "note": "Nota del Nutricionista:",
        "ingredients": "🛒 Ingredientes", "save_fav": "⭐ Guardar en Favoritos", "saved": "¡Guardado!",
        "instructions": "👨‍🍳 Preparación", "adjust_title": "⚖️ Ajustar Macros",
        "adjust_sub": "¿Necesitas otras cantidades? Pídemelo.", "adjust_ph": "Ej: 'Añade 20g de proteína'",
        "recalc_btn": "Recalcular", "recalculating": "Ajustando...", "profile": "👤 Mi Perfil",
        "update_prof": "Actualizar Perfil", "prof_updated": "¡Perfil actualizado!",
        "favs": "⭐ Favoritos", "no_favs": "Aún no hay favoritos.", "logout": "Cerrar Sesión",
        "feed_title": "Recetas de Moda 🔥", "cook_this": "Cocinar esto 🍳", "download_btn": "⬇️ Descargar Receta",
        "trending": [
            {"name": "Ratatouille", "emoji": "🍅", "desc": "Un clásico lleno de vitaminas y muy bajo en calorías."},
            {"name": "Risotto de Setas", "emoji": "🍄", "desc": "Cremoso, reconfortante y perfecto para cargar energía."},
            {"name": "Poke Bowl de Salmón", "emoji": "🥗", "desc": "Fresco, rico en omega-3 y grasas saludables."},
            {"name": "Shakshuka", "emoji": "🍳", "desc": "Huevos en salsa de tomate especiada. Alto en proteína."}
        ]
    },
    "🇬🇧 English": {
        "lang_code": "English",
        "login_sub": "Your smart nutritionist. Log in or sign up to continue.",
        "tab_login": "🔑 Login", "tab_reg": "📝 Sign Up", "tab_rec": "🆘 Recover PIN",
        "user_label": "Username (e.g., mike123)", "pin_label": "PIN (Password)",
        "enter_btn": "Log In", "login_err": "Incorrect Username or PIN.",
        "title": "Hi {name}! What are we cooking today? 🍲",
        "subtitle": "Tell me your ingredients, and I'll craft the perfect meal for your goals.",
        "assistant_msg": "List your ingredients below. Let's cook!",
        "input_placeholder": "e.g., Chicken breast, rice, broccoli...",
        "find_btn": "🔍 Find Recipes", "analyzing": "Crafting your options...",
        "here_options": "Options for you:", "diff": "Difficulty", "time": "Time", "health": "Health",
        "cook_btn": "Cook {}", "loading_recipe": "Calculating macros for {}...",
        "start_over": "← Start Over", "note": "Nutritionist's Note:",
        "ingredients": "🛒 Ingredients", "save_fav": "⭐ Save Favorite", "saved": "Saved!",
        "instructions": "👨‍🍳 Instructions", "adjust_title": "⚖️ Adjust Macros",
        "adjust_sub": "Need different targets? Just ask.", "adjust_ph": "e.g., 'Add 20g of protein'",
        "recalc_btn": "Recalculate", "recalculating": "Adjusting...", "profile": "👤 My Profile",
        "update_prof": "Update Profile", "prof_updated": "Profile updated!",
        "favs": "⭐ Favorites", "no_favs": "No favorites yet.", "logout": "Logout",
        "feed_title": "Trending Recipes 🔥", "cook_this": "Cook this 🍳", "download_btn": "⬇️ Download Recipe",
        "trending": [
            {"name": "Ratatouille", "emoji": "🍅", "desc": "A vitamin-packed classic, very low in calories."},
            {"name": "Mushroom Risotto", "emoji": "🍄", "desc": "Creamy, comforting, and perfect for carb-loading."},
            {"name": "Salmon Poke Bowl", "emoji": "🥗", "desc": "Fresh, rich in omega-3s and healthy fats."},
            {"name": "Shakshuka", "emoji": "🍳", "desc": "Eggs in spicy tomato sauce. High in protein."}
        ]
    },
    "🇫🇷 Français": {
        "lang_code": "French",
        "login_sub": "Votre nutritionniste intelligent. Connectez-vous ou inscrivez-vous pour continuer.",
        "tab_login": "🔑 Connexion", "tab_reg": "📝 S'inscrire", "tab_rec": "🆘 Récupérer PIN",
        "user_label": "Utilisateur (Ex : michel123)", "pin_label": "PIN (Mot de passe)",
        "enter_btn": "Entrer", "login_err": "Utilisateur ou PIN incorrect.",
        "title": "Bonjour {name} ! Qu'est-ce qu'on cuisine aujourd'hui ? 🍲",
        "subtitle": "Dis-moi quels ingrédients tu as et je créerai le repas parfait pour tes objectifs.",
        "assistant_msg": "Écris tes ingrédients ci-dessous. Cuisinons sainement !",
        "input_placeholder": "Ex : Blanc de poulet, riz, brocoli...",
        "find_btn": "🔍 Trouver des Recettes", "analyzing": "Analyse en cours...",
        "here_options": "Options pour toi :", "diff": "Difficulté", "time": "Temps", "health": "Santé",
        "cook_btn": "Cuisiner {}", "loading_recipe": "Calcul des macros pour {}...",
        "start_over": "← Recommencer", "note": "Note du Nutritionniste :",
        "ingredients": "🛒 Ingrédients", "save_fav": "⭐ Sauvegarder", "saved": "Sauvegardé !",
        "instructions": "👨‍🍳 Préparation", "adjust_title": "⚖️ Ajuster les Macros",
        "adjust_sub": "Besoin d'autres quantités ? Demande-moi.", "adjust_ph": "Ex : 'Ajoute 20g de protéines'",
        "recalc_btn": "Recalculer", "recalculating": "Ajustement...", "profile": "👤 Mon Profil",
        "update_prof": "Mettre à jour", "prof_updated": "Profil mis à jour !",
        "favs": "⭐ Favoris", "no_favs": "Pas encore de favoris.", "logout": "Déconnexion",
        "feed_title": "Recettes Tendance 🔥", "cook_this": "Cuisiner ça 🍳", "download_btn": "⬇️ Télécharger la Recette",
        "trending": [
            {"name": "Ratatouille", "emoji": "🍅", "desc": "Un classique plein de vitamines et très peu calorique."},
            {"name": "Risotto aux Champignons", "emoji": "🍄", "desc": "Crémeux, réconfortant et parfait pour faire le plein d'énergie."},
            {"name": "Poke Bowl au Saumon", "emoji": "🥗", "desc": "Frais, riche en oméga-3 et en bonnes graisses."},
            {"name": "Shakshuka", "emoji": "🍳", "desc": "Œufs à la sauce tomate épicée. Riche en protéines."}
        ]
    },
    "🇮🇹 Italiano": {
        "lang_code": "Italian",
        "login_sub": "Il tuo nutrizionista intelligente. Accedi o registrati per continuare.",
        "tab_login": "🔑 Accedi", "tab_reg": "📝 Registrati", "tab_rec": "🆘 Recupera PIN",
        "user_label": "Utente (Es: michele123)", "pin_label": "PIN (Password)",
        "enter_btn": "Entra", "login_err": "Utente o PIN errati.",
        "title": "Ciao {name}! Cosa cuciniamo oggi? 🍲",
        "subtitle": "Dimmi che ingredienti hai e creerò il pasto perfetto per i tuoi obiettivi.",
        "assistant_msg": "Scrivi i tuoi ingredienti qui sotto. Cuciniamo sano!",
        "input_placeholder": "Es: Petto di pollo, riso, broccoli...",
        "find_btn": "🔍 Trova Ricette", "analyzing": "Analizzando gli ingredienti...",
        "here_options": "Opzioni per te:", "diff": "Difficoltà", "time": "Tempo", "health": "Salute",
        "cook_btn": "Cucina {}", "loading_recipe": "Calcolando i macro per {}...",
        "start_over": "← Ricomincia", "note": "Nota del Nutrizionista:",
        "ingredients": "🛒 Ingredienti", "save_fav": "⭐ Salva nei Preferiti", "saved": "Salvato!",
        "instructions": "👨‍🍳 Preparazione", "adjust_title": "⚖️ Regola i Macro",
        "adjust_sub": "Hai bisogno di altre quantità? Chiedi pure.", "adjust_ph": "Es: 'Aggiungi 20g di proteine'",
        "recalc_btn": "Ricalcola", "recalculating": "Regolazione in corso...", "profile": "👤 Il Mio Profilo",
        "update_prof": "Aggiorna Profilo", "prof_updated": "Profilo aggiornato!",
        "favs": "⭐ Preferiti", "no_favs": "Nessun preferito.", "logout": "Esci",
        "feed_title": "Ricette di Tendenza 🔥", "cook_this": "Cucina questo 🍳", "download_btn": "⬇️ Scarica Ricetta",
        "trending": [
            {"name": "Ratatouille", "emoji": "🍅", "desc": "Un classico ricco di vitamine e a bassissimo contenuto calorico."},
            {"name": "Risotto ai Funghi", "emoji": "🍄", "desc": "Cremoso, confortante e perfetto per fare il pieno di energia."},
            {"name": "Poke Bowl al Salmone", "emoji": "🥗", "desc": "Fresco, ricco di omega-3 e grassi sani."},
            {"name": "Shakshuka", "emoji": "🍳", "desc": "Uova in salsa di pomodoro piccante. Ricco di proteine."}
        ]
    }
}

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def extract_number(val_str):
    """Extrae el valor numérico de un string como '40g' o '450 kcal' para los gráficos."""
    match = re.search(r'\d+', str(val_str))
    return int(match.group()) if match else 0

def format_recipe_for_download(recipe, t_dict):
    """Formatea la receta en texto plano para el archivo descargable."""
    text = f"=== {recipe['recipe_name'].upper()} ===\n"
    text += f"🌍 Origen/Estilo: {recipe.get('region', 'Global')}\n\n"
    text += f"--- {t_dict['ingredients'].upper()} ---\n"
    for ing in recipe["ingredients"]:
        text += f"• {ing['qty']} de {ing['item']}\n"
    text += f"\n--- {t_dict['instructions'].upper()} ---\n"
    for i, step in enumerate(recipe["instructions"]):
        text += f"{i+1}. {step}\n"
    text += f"\n--- MACROS ---\n"
    m = recipe['macros']
    text += f"Calorías: {m.get('calories', '0')} | Proteína: {m.get('protein', '0g')} | Grasas: {m.get('total_fat', '0g')} | Carbohidratos: {m.get('total_carbs', '0g')}\n"
    return text

# ==========================================
# GESTIÓN DE COOKIES (Sesión Persistente)
# ==========================================
cookie_manager = stx.CookieManager(key="cookie_manager")

if "current_username" not in st.session_state:
    st.session_state.current_username = cookie_manager.get(cookie="ai_nutri_session")

def set_login_session(username):
    st.session_state.current_username = username
    expire_date = datetime.datetime.now() + datetime.timedelta(days=365)
    cookie_manager.set("ai_nutri_session", username, expires_at=expire_date)

def logout():
    st.session_state.current_username = None
    try:
        cookie_manager.delete("ai_nutri_session")
    except Exception:
        pass 
    st.session_state.step = "input"

def get_user_data(username):
    if not username:
        return None
    res = supabase.table("app_users_2").select("*").eq("username", username).execute()
    if res.data:
        return res.data[0]
    return None

def update_user_data(username, data_dict):
    if username:
        supabase.table("app_users_2").update(data_dict).eq("username", username).execute()

# ==========================================
# SELECTOR DE IDIOMA Y TRADUCCIONES
# ==========================================
# Usamos session_state para recordar el idioma elegido en toda la app
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "🇪🇸 Español"

def update_lang():
    st.session_state.selected_lang = st.session_state.lang_selector

# Cargamos las traducciones basadas en el estado actual
t = TRANSLATIONS[st.session_state.selected_lang]
lang_code = t["lang_code"]

# ==========================================
# PANTALLA DE AUTENTICACIÓN
# ==========================================
# Lógica para mantener el selector de idioma sincronizado
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "🇪🇸 Español"

def update_lang():
    st.session_state.selected_lang = st.session_state.lang_selector

# Asignamos las variables de traducción basadas en la selección
t = TRANSLATIONS[st.session_state.selected_lang]
lang_code = t["lang_code"]

if not st.session_state.current_username:
    # Selector de idioma elegante y centrado en la pantalla de inicio
    st.write("") # Espacio
    col_lang1, col_lang2, col_lang3 = st.columns([1, 2, 1])
    with col_lang2:
        st.selectbox(
            "🌍 Language / Langue / Lingua / Idioma:", 
            list(TRANSLATIONS.keys()), 
            index=list(TRANSLATIONS.keys()).index(st.session_state.selected_lang),
            key="lang_selector",
            on_change=update_lang
        )
    st.write("---")

    st.title("NutriAI 🍲")
    st.markdown(t.get("login_sub", "Tu nutricionista inteligente. Inicia sesión o regístrate para continuar."))
    
    tab1, tab2, tab3 = st.tabs([t.get("tab_login", "🔑 Iniciar Sesión"), t.get("tab_reg", "📝 Registrarse"), t.get("tab_rec", "🆘 Recuperar PIN")])
    
    with tab1:
        log_user = st.text_input(t.get("user_label", "Usuario"), key="log_user")
        log_pin = st.text_input(t.get("pin_label", "PIN"), type="password", key="log_pin")
        if st.button(t.get("enter_btn", "Entrar"), type="primary", use_container_width=True):
            res = supabase.table("app_users_2").select("*").eq("username", log_user).eq("pin", log_pin).execute()
            if res.data:
                set_login_session(log_user)
                st.rerun()
            else:
                st.error(t.get("login_err", "Usuario o PIN incorrectos."))
                
    with tab2:
        st.markdown(t["reg_step1"])
        reg_user = st.text_input(t["reg_user_label"], key="reg_user")
        reg_pin = st.text_input(t["reg_pin_label"], type="password", key="reg_pin")
        reg_sq = st.selectbox(t["reg_sq_label"], t["reg_sq_options"])
        reg_sa = st.text_input(t["reg_sa_label"])
        
        st.markdown(t["reg_step2"])
        reg_name = st.text_input(t["reg_name_label"])
        col1, col2, col3 = st.columns(3)
        reg_age = col1.number_input(t["reg_age"], min_value=10, max_value=100, step=1, value=25)
        reg_weight = col2.number_input(t["reg_weight"], min_value=30.0, max_value=200.0, step=0.1, value=70.0)
        reg_height = col3.number_input(t["reg_height"], min_value=100, max_value=250, step=1, value=170)
        reg_gender = st.selectbox(t["reg_gender_label"], t["reg_gender_options"])
        
        st.markdown(t["reg_step3"])
        reg_goals = st.text_area(t["reg_goals_label"])
        reg_rest = st.text_input(t["reg_rest_label"])
        
        if st.button(t["reg_btn"], type="primary", use_container_width=True):
            if reg_user and reg_pin and reg_sa and reg_name:
                check = supabase.table("app_users_2").select("username").eq("username", reg_user).execute()
                if check.data:
                    st.error(t["reg_err_user"])
                else:
                    new_user = {
                        "username": reg_user, "pin": reg_pin, "security_question": reg_sq, "security_answer": reg_sa.lower(),
                        "name": reg_name, "age": reg_age, "weight": reg_weight, "height": reg_height, "gender": reg_gender,
                        "goals": reg_goals, "restrictions": reg_rest, "favorites":[]
                    }
                    supabase.table("app_users_2").insert(new_user).execute()
                    set_login_session(reg_user)
                    st.success(t["reg_success"])
                    st.rerun()
            else:
                st.warning(t["reg_warn_fields"])

    with tab3:
        st.markdown(t["rec_title"])
        rec_user = st.text_input(t["rec_user_label"], key="rec_user")
        if st.button(t["rec_btn_search"]):
            res = supabase.table("app_users_2").select("security_question").eq("username", rec_user).execute()
            if res.data:
                st.session_state.recover_user = rec_user
                st.session_state.recover_q = res.data[0]["security_question"]
                st.success(t["rec_found"])
            else:
                st.error(t["rec_not_found"])
                
        if "recover_user" in st.session_state:
            st.info(f"{t['rec_q_label']} **{st.session_state.recover_q}**")
            rec_ans = st.text_input(t["rec_ans_label"])
            new_pin = st.text_input(t["rec_new_pin"], type="password")
            if st.button(t["rec_btn_change"], use_container_width=True):
                res = supabase.table("app_users_2").select("security_answer").eq("username", st.session_state.recover_user).execute()
                if res.data and res.data[0]["security_answer"] == rec_ans.lower():
                    supabase.table("app_users_2").update({"pin": new_pin}).eq("username", st.session_state.recover_user).execute()
                    st.success(t["rec_success"])
                    del st.session_state.recover_user
                else:
                    st.error(t["rec_err_ans"])
                    
    st.stop() 

# ==========================================
# CARGAR PERFIL DEL USUARIO ACTIVO
# ==========================================
user_profile = get_user_data(st.session_state.current_username)
if not user_profile:
    logout()
    st.rerun()

# ==========================================
# ESTADO DE LA SESIÓN DE LA APP
# ==========================================
if "step" not in st.session_state: st.session_state.step = "input"
if "options" not in st.session_state: st.session_state.options = None
if "selected_option" not in st.session_state: st.session_state.selected_option = None
if "full_recipe" not in st.session_state: st.session_state.full_recipe = None

# ==========================================
# IA (GROQ) Y PROMPT CLÍNICO EMPÁTICO
# ==========================================
def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("Groq API Key no encontrada.")
        st.stop()
    return Groq(api_key=api_key)

def call_ai_json(prompt, expected_format_hint, lang_code, u_prof):
    client = get_groq_client()
    system_prompt = f"""
    You are a strict but empathetic Clinical Nutritionist.
    Your client is {u_prof['name']}. 
    Clinical profile: {u_prof['age']} years old, {u_prof['weight']} kg, {u_prof['height']} cm, Gender: {u_prof['gender']}.
    Main goal: "{u_prof['goals']}".
    
    Use their clinical profile to estimate true caloric needs (BMR/TDEE) based on their goal.
    Help them achieve it, BUT do not obsess over extremes. 
    GUARDRAIL: If the user asks for extreme or unhealthy amounts (e.g., massive protein, zero healthy fats, crash diets), 
    you MUST give a CAREFUL, empathetic warning in the 'nutritionist_note'. Always prioritize long-term physical and mental health. 
    Never approve nutritional madness.
    Address them by their name occasionally in the 'nutritionist_note'.
    
    CRITICAL: You MUST reply entirely in {lang_code}.
    ALWAYS reply in valid JSON format.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt + "\n" + expected_format_hint},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

# ==========================================
# UI: BARRA LATERAL (Perfil y Favoritos)
# ==========================================
with st.sidebar:
    # Selector de idioma en el sidebar (solo visible cuando ya han iniciado sesión)
    if st.session_state.current_username:
        st.selectbox(
            "🌐 Language", 
            list(TRANSLATIONS.keys()), 
            index=list(TRANSLATIONS.keys()).index(st.session_state.selected_lang),
            key="lang_selector_sidebar",
            on_change=lambda: st.session_state.update(selected_lang=st.session_state.lang_selector_sidebar)
        )
        st.divider()

    with st.expander(t["profile"], expanded=False):
        upd_weight = st.number_input(t["weight_label"], value=float(user_profile.get("weight", 70.0)))
        upd_goals = st.text_area(t["goals_label"], value=user_profile.get("goals", ""))
        upd_rest = st.text_input(t["rest_label"], value=user_profile.get("restrictions", ""))
        if st.button(t["update_prof"], use_container_width=True):
            update_user_data(user_profile["username"], {"weight": upd_weight, "goals": upd_goals, "restrictions": upd_rest})
            st.success(t["prof_updated"])
            st.rerun()
            
    st.divider()
    
    st.subheader(t["favs"])
    favs = user_profile.get("favorites", [])
    if favs:
        for f in favs:
            with st.expander(f["name"]):
                st.write(f"🔥 {f['calories']} | 💪 {f['protein']}")
    else:
        st.info(t["no_favs"])
        
    st.divider()
    
    if st.button(t["logout"], type="secondary", use_container_width=True):
        logout()
        st.rerun()

# ==========================================
# UI: APLICACIÓN PRINCIPAL
# ==========================================
st.title(t["title"].format(name=user_profile["name"]))
st.markdown(t["subtitle"])

# --- FASE 1: INPUT DE INGREDIENTES Y FEED DE INSPIRACIÓN ---
if st.session_state.step == "input" or st.session_state.step == "options":
    
    # Dividimos la pantalla en Layout de Columnas (70% - 30%)
    col_main, col_feed = st.columns([7, 3])
    
    with col_main:
        ingredients = st.text_area("👨‍🍳 " + t["assistant_msg"], placeholder=t["input_placeholder"], height=150)
        
        if st.button(t["find_btn"], type="primary", use_container_width=True):
            if ingredients:
                with st.spinner(t["analyzing"]):
                    prompt = f"Ingredients: {ingredients}. Restrictions: {user_profile['restrictions']}."
                    format_hint = """
                    Return strictly in this JSON format:
                    {
                        "options":[
                            {
                                "name": "Recipe Name",
                                "hero_emoji": "🥘", 
                                "difficulty": "Easy/Medium/Hard",
                                "time": "XX mins",
                                "health_score": 9,
                                "description": "Brief description"
                            }
                        ]
                    }
                    """
                    res = call_ai_json(prompt, format_hint, lang_code, user_profile)
                    if res and "options" in res:
                        st.session_state.options = res["options"]
                        st.session_state.step = "options"
                        st.rerun()
                        
    # FEED DE INSPIRACIÓN EN LA COLUMNA DERECHA
    with col_feed:
        st.subheader(t["feed_title"])
        with st.container(height=500, border=True):
            for i, recipe in enumerate(t["trending"]):
                st.markdown(f"""
                    <div class="feed-card">
                        <h3 style="margin:0;">{recipe['emoji']} {recipe['name']}</h3>
                        <p style="font-size:14px; color:#555; margin-top:5px;">{recipe['desc']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Botón para generar directamente la receta desde el feed
                if st.button(t["cook_this"], key=f"feed_btn_{i}", use_container_width=True):
                    st.session_state.selected_option = {"name": recipe["name"], "hero_emoji": recipe["emoji"]}
                    st.session_state.step = "recipe_loading"
                    st.rerun()

# --- FASE 2: OPCIONES DE RECETAS (TARJETA DORADA) ---
if st.session_state.step == "options" and st.session_state.options:
    st.divider()
    st.subheader(t["here_options"])
    
    for i, opt in enumerate(st.session_state.options):
        with st.container():
            if i == 0:
                st.markdown("""
                <div class="golden-card">
                    <div class="golden-card-content">
                        <span style="color:#D4AF37; font-weight:bold; font-size:12px;">🌟 CHEF'S RECOMMENDATION 🌟</span>
                        <h1 style="font-size: 50px; margin: 0;">{}</h1>
                        <h3 style="margin: 5px 0;">{}</h3>
                    </div>
                </div>
                """.format(opt.get('hero_emoji', '🍽️'), opt['name']), unsafe_allow_html=True)
            else:
                st.markdown(f"<h1 style='text-align:center; font-size:40px; margin:0;'>{opt.get('hero_emoji', '🍽️')}</h1>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align:center;'>{opt['name']}</h3>", unsafe_allow_html=True)
            
            st.caption(f"**{t['diff']}:** {opt['difficulty']} | **{t['time']}:** {opt['time']} | **{t['health']}:** {opt['health_score']}/10")
            st.write(opt['description'])
            
            if st.button(t["cook_btn"].format(""), key=f"btn_cook_{i}", use_container_width=True):
                st.session_state.selected_option = opt
                st.session_state.step = "recipe_loading"
                st.rerun()
        st.write("---")

# --- FASE 3: GENERAR RECETA COMPLETA ---
if st.session_state.step == "recipe_loading":
    with st.spinner(t["loading_recipe"].format(st.session_state.selected_option['name'])):
        prompt = f"Generate full recipe for '{st.session_state.selected_option['name']}'. Restrictions: {user_profile['restrictions']}."
        format_hint = """
        Return strictly in this JSON format:
        {
            "recipe_name": "Name",
            "region": "City, Country or Region Style",
            "hero_emoji": "🥘",
            "ingredients_emojis": "🍅🧅🍗",
            "nutritionist_note": "Empathetic note addressing the user by name. Remember the Guardrail!",
            "macros": {
                "calories": "450 kcal", "total_fat": "15g", "saturated_fat": "3g", "total_carbs": "30g",
                "total_sugars": "5g", "added_sugars": "0g", "fiber": "6g", "protein": "40g", "sodium": "400mg"
            },
            "ingredients":[{"item": "Chicken breast", "qty": "200g"}],
            "instructions":["Step 1...", "Step 2..."]
        }
        """
        res = call_ai_json(prompt, format_hint, lang_code, user_profile)
        if res:
            st.session_state.full_recipe = res
            st.session_state.step = "recipe_view"
            st.rerun()

# --- FASE 4: VISUALIZACIÓN DE LA RECETA ---
if st.session_state.step == "recipe_view" and st.session_state.full_recipe:
    recipe = st.session_state.full_recipe
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(t["start_over"], use_container_width=True):
            st.session_state.step = "input"
            st.session_state.options = None
            st.session_state.full_recipe = None
            st.rerun()
            
    with col_btn2:
        # Botón de descarga de archivo .txt
        txt_data = format_recipe_for_download(recipe, t)
        st.download_button(
            label=t["download_btn"],
            data=txt_data,
            file_name=f"{recipe['recipe_name'].replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    st.markdown(f"<p class='hero-emoji'>{recipe.get('hero_emoji', '🍽️')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center;'>{recipe['recipe_name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align:center; color:#555;'>🌍 {recipe.get('region', 'Global')}</h4>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; letter-spacing: 5px;'>{recipe.get('ingredients_emojis', '')}</h3>", unsafe_allow_html=True)
    
    st.info(f"**{t['note']}** {recipe.get('nutritionist_note', '')}")
    
    # Layout de 2 columnas para integrar la etiqueta y el gráfico de anillo
    st.divider()
    col_label, col_chart = st.columns(2)
    
    m = recipe['macros']
    
    with col_label:
        st.markdown(f"""
        <div class="nutrition-label">
            <h2>Nutrition Facts</h2>
            <div class="nut-row thick"><span class="nut-bold">Calories</span> <span class="nut-bold">{m.get('calories', '0')}</span></div>
            <div class="nut-row"><span class="nut-bold">Total Fat</span> {m.get('total_fat', '0g')}</div>
            <div class="nut-row indent">Saturated Fat {m.get('saturated_fat', '0g')}</div>
            <div class="nut-row"><span class="nut-bold">Sodium</span> {m.get('sodium', '0mg')}</div>
            <div class="nut-row"><span class="nut-bold">Total Carbohydrate</span> {m.get('total_carbs', '0g')}</div>
            <div class="nut-row indent">Dietary Fiber {m.get('fiber', '0g')}</div>
            <div class="nut-row indent">Total Sugars {m.get('total_sugars', '0g')}</div>
            <div class="nut-row indent">Includes {m.get('added_sugars', '0g')} Added Sugars</div>
            <div class="nut-row thick"><span class="nut-bold">Protein</span> <span class="nut-bold">{m.get('protein', '0g')}</span></div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_chart:
        # Extraemos los números y preparamos los datos para Plotly
        macro_df = pd.DataFrame({
            "Macro": ["Proteína", "Grasas", "Carbohidratos"],
            "Gramos": [
                extract_number(m.get('protein', '0g')),
                extract_number(m.get('total_fat', '0g')),
                extract_number(m.get('total_carbs', '0g'))
            ]
        })
        # Verificamos que no todos los valores sean cero para no romper el gráfico
        if macro_df['Gramos'].sum() > 0:
            fig = px.pie(
                macro_df, 
                values='Gramos', 
                names='Macro', 
                hole=0.55,
                color_discrete_sequence=['#ff6b6b', '#feca57', '#48dbfb']
            )
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20), 
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("Gráfico no disponible para esta receta.")
    
    if st.button(t["save_fav"], use_container_width=True):
        favs = user_profile.get("favorites",[])
        favs.append({
            "name": recipe["recipe_name"],
            "calories": m.get('calories', '0'),
            "protein": m.get('protein', '0g')
        })
        update_user_data(user_profile["username"], {"favorites": favs})
        st.toast(t["saved"])
            
    with st.expander("🛒 " + t["ingredients"], expanded=True):
        for ing in recipe["ingredients"]:
            st.markdown(f"- **{ing['qty']}** {ing['item']}")
            
    with st.expander("👨‍🍳 " + t["instructions"], expanded=True):
        for i, step in enumerate(recipe["instructions"]):
            st.write(f"**{i+1}.** {step}")

    st.divider()

    # --- FASE 5: AJUSTE DE MACROS ---
    st.subheader(t["adjust_title"])
    st.markdown(t["adjust_sub"])
    macro_adjustment = st.text_input("", placeholder=t["adjust_ph"])
    
    if st.button(t["recalc_btn"], use_container_width=True):
        if macro_adjustment:
            with st.spinner(t["recalculating"]):
                prompt = f"Current recipe: {json.dumps(recipe)}. Adjustment: '{macro_adjustment}'. Recalculate quantities."
                format_hint = "Return strictly in the exact same JSON format as the original recipe."
                # NOTA: Corregido el error de tu código original, donde se llamaba dos veces la función perdiendo el u_prof
                new_recipe = call_ai_json(prompt, format_hint, lang_code, user_profile)
                if new_recipe:
                    st.session_state.full_recipe = new_recipe
                    st.rerun()
                    new_recipe = call_ai_json(prompt, format_hint, lang_code)
                    if new_recipe:
                        st.session_state.full_recipe = new_recipe
                        st.rerun()
