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
    .lang-select { display:flex; justify-content:flex-end; align-items:center; margin-bottom:10px; }
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
        st.error("Supabase credentials missing in st.secrets.")
        st.stop()
    return create_client(url, key)

supabase = init_supabase()

# ==========================================
# SISTEMA MULTIDIOMA Y TEXTOS
# ==========================================
TRANSLATIONS = {
    "🇪🇸 Español": {
        "lang_code": "Spanish",
        "title": "¡Hola {name}! ¿Qué cocinamos hoy? 🍲",
        "subtitle": "Crearé la comida perfecta usando ÚNICAMENTE lo que tengas a mano.",
        "assistant_msg": "¿Qué hay en la despensa? ¡Hagamos magia!",
        "avail_ing_label": "Ingredientes disponibles hoy (Ej: 2 huevos, medio tomate, arroz)",
        "avoid_today_label": "¿Algo que no te apetezca o quieras evitar hoy? (Ej: fritos, sin sal, picante)",
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
        "news_title": "📰 Noticias",
        "feed_title": "Recetas de Moda 🔥", "cook_this": "Cocinar esto 🍳", "download_btn": "⬇️ Descargar Receta",
        "trending":[
            {"name": "Ratatouille", "emoji": "🍅", "desc": "Un clásico lleno de vitaminas y muy bajo en calorías."},
            {"name": "Risotto de Setas", "emoji": "🍄", "desc": "Cremoso, reconfortante y perfecto para cargar energía."},
            {"name": "Poke Bowl de Salmón", "emoji": "🥗", "desc": "Fresco, rico en omega-3 y grasas saludables."},
            {"name": "Shakshuka", "emoji": "🍳", "desc": "Huevos en salsa de tomate especiada. Alto en proteína."}
        ],
        "auth_app_name": "NutriAI 🍲",
        "auth_subtitle": "Tu nutricionista inteligente. Inicia sesión o regístrate para continuar.",
        "tab_login": "🔑 Iniciar Sesión", "tab_register": "📝 Registrarse", "tab_recover": "🆘 Recuperar PIN",
        "username_label_login": "Usuario (Ej: miguel123)", "pin_label_login": "PIN (Contraseña)",
        "login_btn": "Entrar", "login_error": "Usuario o PIN incorrectos.",
        "reg_section1": "1. Datos de Acceso", "create_user_label": "Crea un Usuario único",
        "create_pin_label": "Crea un PIN corto", "security_question_label": "Pregunta de Seguridad",
        "security_options":["¿Nombre de tu primera mascota?", "¿Ciudad de nacimiento?", "¿Nombre de tu colegio?"],
        "security_answer_label": "Respuesta de Seguridad (Útil si olvidas el PIN)",
        "reg_section2": "2. Tu Perfil Clínico", "name_label": "Nombre Real (Para tratarte con cercanía)",
        "age_label": "Edad", "weight_label": "Peso (kg)", "height_label": "Altura (cm)",
        "gender_label": "Género", "gender_options":["Masculino", "Femenino", "Otro"],
        "reg_section3": "3. Objetivos", "goals_label": "Objetivo principal (Ej: Perder grasa, ganar masa muscular)",
        "rest_label": "Restricciones Crónicas (Ej: Vegano, Intolerante a la lactosa)",
        "create_account_btn": "Crear Cuenta y Entrar 🚀", "username_taken": "Ese Nombre de Usuario ya está en uso. Elige otro.",
        "account_created": "¡Cuenta creada!", "fill_required": "Por favor, rellena los campos obligatorios.",
        "forgot_pin_text": "¿Olvidaste tu PIN?", "search_user_label": "Introduce tu Usuario",
        "search_user_btn": "Buscar Usuario", "user_found": "Usuario encontrado.", "user_not_found": "Usuario no encontrado.",
        "recover_question_prefix": "Pregunta:", "your_answer_label": "Tu Respuesta", "new_pin_label": "Nuevo PIN",
        "change_pin_btn": "Cambiar PIN", "pin_changed_success": "¡PIN cambiado con éxito! Ya puedes iniciar sesión.",
        "wrong_answer": "Respuesta incorrecta.", "current_weight_label": "Peso Actual (kg)",
        "profile_goals_label": "Objetivos", "profile_restrictions_label": "Restricciones",
        "macro_protein": "Proteínas", "macro_fat": "Grasas", "macro_carbs": "Carbohidratos"
    },
    "🇬🇧 English": {
        "lang_code": "English",
        "title": "Hi {name}! What are we cooking today? 🍲",
        "subtitle": "I will craft the perfect meal using ONLY what you have on hand.",
        "assistant_msg": "What's in the pantry? Let's make magic!",
        "avail_ing_label": "Available ingredients today (e.g., 2 eggs, half a tomato, rice)",
        "avoid_today_label": "Anything to avoid today? (e.g., fried food, no salt, spicy)",
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
        "news_title": "📰 News",
        "feed_title": "Trending Recipes 🔥", "cook_this": "Cook this 🍳", "download_btn": "⬇️ Download Recipe",
        "trending":[
            {"name": "Ratatouille", "emoji": "🍅", "desc": "A vitamin-packed classic, very low in calories."},
            {"name": "Mushroom Risotto", "emoji": "🍄", "desc": "Creamy, comforting, and perfect for carb-loading."},
            {"name": "Salmon Poke Bowl", "emoji": "🥗", "desc": "Fresh, rich in omega-3s and healthy fats."},
            {"name": "Shakshuka", "emoji": "🍳", "desc": "Eggs in spicy tomato sauce. High in protein."}
        ],
        "auth_app_name": "NutriAI 🍲", "auth_subtitle": "Your smart nutritionist. Log in or sign up to continue.",
        "tab_login": "🔑 Log In", "tab_register": "📝 Register", "tab_recover": "🆘 Recover PIN",
        "username_label_login": "Username (e.g., miguel123)", "pin_label_login": "PIN (Password)",
        "login_btn": "Enter", "login_error": "Incorrect username or PIN.",
        "reg_section1": "1. Access Data", "create_user_label": "Create a unique Username",
        "create_pin_label": "Create a short PIN", "security_question_label": "Security Question",
        "security_options":["What was your first pet's name?", "City of birth?", "Name of your school?"],
        "security_answer_label": "Security Answer (Useful if you forget your PIN)",
        "reg_section2": "2. Your Clinical Profile", "name_label": "Full Name (to address you properly)",
        "age_label": "Age", "weight_label": "Weight (kg)", "height_label": "Height (cm)",
        "gender_label": "Gender", "gender_options":["Male", "Female", "Other"],
        "reg_section3": "3. Goals", "goals_label": "Main goal (e.g., Lose fat, gain muscle)",
        "rest_label": "Chronic Restrictions (e.g., Vegan, Lactose intolerant)",
        "create_account_btn": "Create Account & Enter 🚀", "username_taken": "That username is already taken. Choose another.",
        "account_created": "Account created!", "fill_required": "Please fill the required fields.",
        "forgot_pin_text": "Forgot your PIN?", "search_user_label": "Enter your Username",
        "search_user_btn": "Find User", "user_found": "User found.", "user_not_found": "User not found.",
        "recover_question_prefix": "Question:", "your_answer_label": "Your Answer", "new_pin_label": "New PIN",
        "change_pin_btn": "Change PIN", "pin_changed_success": "PIN changed successfully! You can now log in.",
        "wrong_answer": "Incorrect answer.", "current_weight_label": "Current Weight (kg)",
        "profile_goals_label": "Goals", "profile_restrictions_label": "Restrictions",
        "macro_protein": "Protein", "macro_fat": "Fat", "macro_carbs": "Carbohydrates"
    },
    "🇫🇷 Français": {
        "lang_code": "French",
        "title": "Bonjour {name} ! Qu'est-ce qu'on cuisine aujourd'hui ? 🍲",
        "subtitle": "Je créerai le repas parfait en utilisant UNIQUEMENT ce que tu as sous la main.",
        "assistant_msg": "Qu'y a-t-il dans le frigo ? Faisons de la magie !",
        "avail_ing_label": "Ingrédients disponibles aujourd'hui (Ex: 2 œufs, demi tomate, riz)",
        "avoid_today_label": "Quelque chose à éviter aujourd'hui ? (Ex: fritures, sans sel, épicé)",
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
        "news_title": "📰 Actualités",
        "feed_title": "Recettes Tendance 🔥", "cook_this": "Cuisiner ça 🍳", "download_btn": "⬇️ Télécharger la Recette",
        "trending":[
            {"name": "Ratatouille", "emoji": "🍅", "desc": "Un classique plein de vitamines et très peu calorique."},
            {"name": "Risotto aux Champignons", "emoji": "🍄", "desc": "Crémeux, réconfortant et parfait pour faire le plein d'énergie."},
            {"name": "Poke Bowl au Saumon", "emoji": "🥗", "desc": "Frais, riche en oméga-3 et en bonnes graisses."},
            {"name": "Shakshuka", "emoji": "🍳", "desc": "Œufs à la sauce tomate épicée. Riche en protéines."}
        ],
        "auth_app_name": "NutriAI 🍲", "auth_subtitle": "Votre nutritionniste intelligent. Connectez-vous ou inscrivez-vous pour continuer.",
        "tab_login": "🔑 Se connecter", "tab_register": "📝 S'inscrire", "tab_recover": "🆘 Récupérer le PIN",
        "username_label_login": "Nom d'utilisateur (ex : miguel123)", "pin_label_login": "PIN (Mot de passe)",
        "login_btn": "Entrer", "login_error": "Nom d'utilisateur ou PIN incorrect.",
        "reg_section1": "1. Données d'accès", "create_user_label": "Créez un nom d'utilisateur unique",
        "create_pin_label": "Créez un PIN court", "security_question_label": "Question de sécurité",
        "security_options":["Nom de votre premier animal ?", "Ville de naissance ?", "Nom de votre école ?"],
        "security_answer_label": "Réponse de sécurité (utile si vous oubliez le PIN)",
        "reg_section2": "2. Votre profil clinique", "name_label": "Nom complet (pour s'adresser correctement à vous)",
        "age_label": "Âge", "weight_label": "Poids (kg)", "height_label": "Taille (cm)",
        "gender_label": "Genre", "gender_options":["Homme", "Femme", "Autre"],
        "reg_section3": "3. Objectifs", "goals_label": "Objectif principal (ex : Perdre de la graisse, prendre de la masse)",
        "rest_label": "Restrictions Chroniques (ex : Végétalien, Intolérant au lactose)",
        "create_account_btn": "Créer un compte et entrer 🚀", "username_taken": "Ce nom d'utilisateur est déjà pris. Choisissez-en un autre.",
        "account_created": "Compte créé !", "fill_required": "Veuillez remplir les champs obligatoires.",
        "forgot_pin_text": "Vous avez oublié votre PIN ?", "search_user_label": "Entrez votre nom d'utilisateur",
        "search_user_btn": "Rechercher l'utilisateur", "user_found": "Utilisateur trouvé.", "user_not_found": "Utilisateur non trouvé.",
        "recover_question_prefix": "Question :", "your_answer_label": "Votre réponse", "new_pin_label": "Nouveau PIN",
        "change_pin_btn": "Changer le PIN", "pin_changed_success": "PIN modifié avec succès ! Vous pouvez maintenant vous connecter.",
        "wrong_answer": "Réponse incorrecte.", "current_weight_label": "Poids actuel (kg)",
        "profile_goals_label": "Objectifs", "profile_restrictions_label": "Restrictions",
        "macro_protein": "Protéines", "macro_fat": "Graisses", "macro_carbs": "Glucides"
    },
    "🇮🇹 Italiano": {
        "lang_code": "Italian",
        "title": "Ciao {name}! Cosa cuciniamo oggi? 🍲",
        "subtitle": "Creerò il pasto perfetto usando SOLO quello che hai a disposizione.",
        "assistant_msg": "Cosa c'è in dispensa? Facciamo una magia!",
        "avail_ing_label": "Ingredienti disponibili oggi (Es: 2 uova, mezzo pomodoro, riso)",
        "avoid_today_label": "Qualcosa che vuoi evitare oggi? (Es: fritti, senza sale, piccante)",
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
        "news_title": "📰 Notizie",
        "feed_title": "Ricette di Tendenza 🔥", "cook_this": "Cucina questo 🍳", "download_btn": "⬇️ Scarica Ricetta",
        "trending":[
            {"name": "Ratatouille", "emoji": "🍅", "desc": "Un classico ricco di vitamine e a bassissimo contenuto calorico."},
            {"name": "Risotto ai Funghi", "emoji": "🍄", "desc": "Cremoso, confortante e perfetto per fare il pieno di energia."},
            {"name": "Poke Bowl al Salmone", "emoji": "🥗", "desc": "Fresco, ricco di omega-3 e grassi sani."},
            {"name": "Shakshuka", "emoji": "🍳", "desc": "Uova in salsa di pomodoro piccante. Ricco di proteine."}
        ],
        "auth_app_name": "NutriAI 🍲", "auth_subtitle": "Il tuo nutrizionista intelligente. Accedi o registrati per continuare.",
        "tab_login": "🔑 Accedi", "tab_register": "📝 Registrati", "tab_recover": "🆘 Recupera PIN",
        "username_label_login": "Nome utente (es: miguel123)", "pin_label_login": "PIN (Password)",
        "login_btn": "Entra", "login_error": "Nome utente o PIN errati.",
        "reg_section1": "1. Dati di accesso", "create_user_label": "Crea un nome utente unico",
        "create_pin_label": "Crea un PIN corto", "security_question_label": "Domanda di sicurezza",
        "security_options":["Nome del tuo primo animale?", "Città di nascita?", "Nome della tua scuola?"],
        "security_answer_label": "Risposta di sicurezza (utile se dimentichi il PIN)",
        "reg_section2": "2. Il tuo profilo clinico", "name_label": "Nome completo (per rivolgerci a te correttamente)",
        "age_label": "Età", "weight_label": "Peso (kg)", "height_label": "Altezza (cm)",
        "gender_label": "Genere", "gender_options":["Maschio", "Femmina", "Altro"],
        "reg_section3": "3. Obiettivi", "goals_label": "Obiettivo principale (es: Perdere grasso, aumentare massa)",
        "rest_label": "Restrizioni Croniche (es: Vegano, Intollerante al lattosio)",
        "create_account_btn": "Crea account & Entra 🚀", "username_taken": "Quel nome utente è già in uso. Scegline un altro.",
        "account_created": "Account creato!", "fill_required": "Per favore, compila i campi obbligatori.",
        "forgot_pin_text": "Hai dimenticato il PIN?", "search_user_label": "Inserisci il tuo nome utente",
        "search_user_btn": "Cerca Utente", "user_found": "Utente trovato.", "user_not_found": "Utente non trovato.",
        "recover_question_prefix": "Domanda:", "your_answer_label": "La tua risposta", "new_pin_label": "Nuovo PIN",
        "change_pin_btn": "Cambia PIN", "pin_changed_success": "PIN modificato con successo! Ora puoi accedere.",
        "wrong_answer": "Risposta errata.", "current_weight_label": "Peso attuale (kg)",
        "profile_goals_label": "Obiettivi", "profile_restrictions_label": "Restrizioni",
        "macro_protein": "Proteine", "macro_fat": "Grassi", "macro_carbs": "Carboidrati"
    }
}

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def extract_number(val_str):
    match = re.search(r'\d+', str(val_str))
    return int(match.group()) if match else 0

def format_recipe_for_download(recipe, t_dict):
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
# LANGUAGE SELECTOR (Top-right)
# ==========================================
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "🇪🇸 Español" if "🇪🇸 Español" in TRANSLATIONS else list(TRANSLATIONS.keys())[0]

cols_top = st.columns([1, 6, 1])
with cols_top[2]:
    st.selectbox(
        "",
        options=list(TRANSLATIONS.keys()),
        key="selected_lang",
        help="Select language / Selecciona idioma"
    )

t = TRANSLATIONS[st.session_state.selected_lang]
lang_code = t["lang_code"]

# ==========================================
# PANTALLA DE AUTENTICACIÓN
# ==========================================
if not st.session_state.current_username:
    st.title(t["auth_app_name"])
    st.markdown(t["auth_subtitle"])
    
    tab1, tab2, tab3 = st.tabs([t["tab_login"], t["tab_register"], t["tab_recover"]])
    
    with tab1:
        log_user = st.text_input(t["username_label_login"], key="log_user")
        log_pin = st.text_input(t["pin_label_login"], type="password", key="log_pin")
        if st.button(t["login_btn"], type="primary", use_container_width=True):
            res = supabase.table("app_users_2").select("*").eq("username", log_user).eq("pin", log_pin).execute()
            if res.data:
                set_login_session(log_user)
                st.rerun()
            else:
                st.error(t["login_error"])
                
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
                if check.data:
                    st.error(t["username_taken"])
                else:
                    new_user = {
                        "username": reg_user, "pin": reg_pin, "security_question": reg_sq, "security_answer": reg_sa.lower(),
                        "name": reg_name, "age": reg_age, "weight": reg_weight, "height": reg_height, "gender": reg_gender,
                        "goals": reg_goals, "restrictions": reg_rest, "favorites":[]
                    }
                    supabase.table("app_users_2").insert(new_user).execute()
                    set_login_session(reg_user)
                    st.success(t["account_created"])
                    st.rerun()
            else:
                st.warning(t["fill_required"])
    
    with tab3:
        st.markdown(t["forgot_pin_text"])
        rec_user = st.text_input(t["search_user_label"], key="rec_user")
        if st.button(t["search_user_btn"]):
            res = supabase.table("app_users_2").select("security_question").eq("username", rec_user).execute()
            if res.data:
                st.session_state.recover_user = rec_user
                st.session_state.recover_q = res.data[0]["security_question"]
                st.success(t["user_found"])
            else:
                st.error(t["user_not_found"])
                
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
                else:
                    st.error(t["wrong_answer"])
                    
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
if "avail_ing" not in st.session_state: st.session_state.avail_ing = ""
if "avoid_tdy" not in st.session_state: st.session_state.avoid_tdy = ""

# ==========================================
# IA (GROQ) Y PROMPT CLÍNICO + REGLAS ESTRICTAS DE DESPENSA
# ==========================================
def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("Groq API Key not found.")
        st.stop()
    return Groq(api_key=api_key)

def call_ai_json(prompt, expected_format_hint, lang_code, u_prof, avail_ing="", avoid_tdy=""):
    client = get_groq_client()
    
    system_prompt = f"""
    You are a strict but empathetic Clinical Nutritionist and Executive Chef.
    Your client is {u_prof['name']}. 
    Clinical profile: {u_prof['age']} years old, {u_prof['weight']} kg, {u_prof['height']} cm, Gender: {u_prof['gender']}.
    Main goal: "{u_prof['goals']}".
    Chronic restrictions: "{u_prof['restrictions']}".
    
    Use their clinical profile to estimate true caloric needs (BMR/TDEE) based on their goal.
    Help them achieve it, BUT do not obsess over extremes. 
    GUARDRAIL: If the user asks for extreme or unhealthy amounts (e.g., massive protein, zero healthy fats, crash diets), 
    you MUST give a CAREFUL, empathetic warning in the 'nutritionist_note'. Always prioritize long-term physical and mental health. 
    Never approve nutritional madness. Address them by their name occasionally in the 'nutritionist_note'.
    """
    
    if avail_ing:
        system_prompt += f"""
        \n[GOLDEN RULE - STRICT INGREDIENT ENFORCEMENT]
        The recipes MUST be based EXCLUSIVELY on these provided ingredients: {avail_ing}.
        Do NOT invent or include main ingredients that the user has not listed.
        [PANTRY FLEXIBILITY] You are allowed to use common "pantry staples" (water, olive oil, salt, pepper, garlic, common dry spices) assuming the user has them.
        """
        
    if avoid_tdy:
        system_prompt += f"""
        \n[STRICT PROHIBITION FOR TODAY]
        Under NO circumstances should you include anything related to: {avoid_tdy}. 
        If the user says "no salt", do NOT use salt even as a pantry staple. If they say "no fried", ensure cooking methods are baked, boiled, or grilled.
        """

    system_prompt += f"\nCRITICAL: You MUST reply entirely in {lang_code}.\nALWAYS reply in valid JSON format."
    
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
# UI: BARRA LATERAL (Perfil, Favoritos y Noticias)
# ==========================================
with st.sidebar:
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
            with st.expander(f["name"]):
                st.write(f"🔥 {f['calories']} | 💪 {f['protein']}")
    else:
        st.info(t["no_favs"])
        
    st.divider()
    
    # --- MOVIDO: FEED DE INSPIRACIÓN / NOTICIAS EN EL SIDEBAR ---
    with st.expander(t["news_title"], expanded=False):
        st.subheader(t["feed_title"])
        for i, recipe in enumerate(t["trending"]):
            st.markdown(f"""
                <div class="feed-card">
                    <h3 style="margin:0;">{recipe['emoji']} {recipe['name']}</h3>
                    <p style="font-size:14px; color:#555; margin-top:5px;">{recipe['desc']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(t["cook_this"], key=f"feed_btn_{i}", use_container_width=True):
                st.session_state.selected_option = {"name": recipe["name"], "hero_emoji": recipe["emoji"]}
                st.session_state.avail_ing = ""
                st.session_state.avoid_tdy = ""
                st.session_state.step = "recipe_loading"
                st.rerun()
                
    st.divider()
    if st.button(t.get("logout", "Logout"), type="secondary", use_container_width=True):
        logout()
        st.rerun()

# ==========================================
# UI: APLICACIÓN PRINCIPAL
# ==========================================
st.title(t["title"].format(name=user_profile["name"]))
st.markdown(t["subtitle"])

# --- FASE 1: INPUT DE INGREDIENTES A ANCHO COMPLETO ---
if st.session_state.step == "input" or st.session_state.step == "options":
    
    st.markdown(f"#### 👨‍🍳 {t['assistant_msg']}")
    
    available_ingredients = st.text_area(
        t["avail_ing_label"], 
        placeholder=t.get("input_placeholder", ""), 
        height=100
    )
    
    avoid_today = st.text_input(
        "🚫 " + t["avoid_today_label"], 
        placeholder="Ej: fritos, sin sal, picante..."
    )
    
    if st.button(t["find_btn"], type="primary", use_container_width=True):
        if available_ingredients:
            st.session_state.avail_ing = available_ingredients
            st.session_state.avoid_tdy = avoid_today
            
            with st.spinner(t["analyzing"]):
                prompt = "Generate 3 recipe options strictly using the available ingredients provided."
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
                res = call_ai_json(prompt, format_hint, lang_code, user_profile, available_ingredients, avoid_today)
                if res and "options" in res:
                    st.session_state.options = res["options"]
                    st.session_state.step = "options"
                    st.rerun()
        else:
            st.warning(t["fill_required"])

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
        prompt = f"Generate full recipe for '{st.session_state.selected_option['name']}'."
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
            "ingredients":[{"item": "Ingredient Name", "qty": "200g"}],
            "instructions":["Step 1...", "Step 2..."]
        }
        """
        res = call_ai_json(prompt, format_hint, lang_code, user_profile, st.session_state.avail_ing, st.session_state.avoid_tdy)
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
            st.session_state.avail_ing = ""
            st.session_state.avoid_tdy = ""
            st.rerun()
            
    with col_btn2:
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
        macro_df = pd.DataFrame({
            "Macro":[t.get("macro_protein", "Protein"), t.get("macro_fat", "Fat"), t.get("macro_carbs", "Carbs")],
            "Gramos":[extract_number(m.get('protein', '0g')), extract_number(m.get('total_fat', '0g')), extract_number(m.get('total_carbs', '0g'))]
        })
        if macro_df['Gramos'].sum() > 0:
            fig = px.pie(
                macro_df, values='Gramos', names='Macro', hole=0.55,
                color_discrete_sequence=['#ff6b6b', '#feca57', '#48dbfb']
            )
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(t.get("chart_not_avail", "Gráfico no disponible para esta receta."))
    
    if st.button(t["save_fav"], use_container_width=True):
        favs = user_profile.get("favorites",[])
        favs.append({"name": recipe["recipe_name"], "calories": m.get('calories', '0'), "protein": m.get('protein', '0g')})
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
                new_recipe = call_ai_json(prompt, format_hint, lang_code, user_profile, st.session_state.avail_ing, st.session_state.avoid_tdy)
                if new_recipe:
                    st.session_state.full_recipe = new_recipe
                    st.rerun()
