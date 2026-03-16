import streamlit as st
import json
import os
import datetime
from groq import Groq
import extra_streamlit_components as stx
from supabase import create_client, Client

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y CSS (Mobile-First)
# ==========================================
st.set_page_config(page_title="Smart AI Nutritionist", page_icon="🍲", layout="centered")

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
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
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
        "favs": "⭐ Favoritos", "no_favs": "Aún no hay favoritos.", "logout": "Cerrar Sesión"
    },
    "🇬🇧 English": {
        "lang_code": "English",
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
        "favs": "⭐ Favorites", "no_favs": "No favorites yet.", "logout": "Logout"
    }
}

# ==========================================
# GESTIÓN DE COOKIES (Sesión Persistente)
# ==========================================
@st.cache_resource(experimental_allow_widgets=True)
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# Usamos session_state para reflejar cambios de UI al instante sin esperar la recarga de la cookie
if "current_username" not in st.session_state:
    st.session_state.current_username = cookie_manager.get(cookie="ai_nutri_session")

def set_login_session(username):
    st.session_state.current_username = username
    expire_date = datetime.datetime.now() + datetime.timedelta(days=365)
    cookie_manager.set("ai_nutri_session", username, expires_at=expire_date)

def logout():
    st.session_state.current_username = None
    cookie_manager.delete("ai_nutri_session")
    st.session_state.step = "input"

def get_user_data(username):
    res = supabase.table("app_users").select("*").eq("username", username).execute()
    if res.data:
        return res.data[0]
    return None

def update_user_data(username, data_dict):
    supabase.table("app_users").update(data_dict).eq("username", username).execute()

# Selector de Idioma Global
with st.sidebar:
    selected_lang = st.selectbox("🌐 Language", list(TRANSLATIONS.keys()))
t = TRANSLATIONS[selected_lang]
lang_code = t["lang_code"]

# ==========================================
# PANTALLA DE AUTENTICACIÓN (Login/Registro)
# ==========================================
if not st.session_state.current_username:
    st.title("NutriAI 🍲")
    st.markdown("Tu nutricionista inteligente. Inicia sesión o regístrate para continuar.")
    
    tab1, tab2, tab3 = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse", "🆘 Recuperar PIN"])
    
    with tab1:
        log_user = st.text_input("Usuario (Ej: miguel123)", key="log_user")
        log_pin = st.text_input("PIN (Contraseña)", type="password", key="log_pin")
        if st.button("Entrar", type="primary", use_container_width=True):
            res = supabase.table("app_users").select("*").eq("username", log_user).eq("pin", log_pin).execute()
            if res.data:
                set_login_session(log_user)
                st.rerun()
            else:
                st.error("Usuario o PIN incorrectos.")
                
    with tab2:
        st.markdown("**1. Datos de Acceso**")
        reg_user = st.text_input("Crea un Usuario único", key="reg_user")
        reg_pin = st.text_input("Crea un PIN corto", type="password", key="reg_pin")
        reg_sq = st.selectbox("Pregunta de Seguridad",["¿Nombre de tu primera mascota?", "¿Ciudad de nacimiento?", "¿Nombre de tu colegio?"])
        reg_sa = st.text_input("Respuesta de Seguridad (Útil si olvidas el PIN)")
        
        st.markdown("**2. Tu Perfil Clínico**")
        reg_name = st.text_input("Nombre Real (Para tratarte con cercanía)")
        col1, col2, col3 = st.columns(3)
        reg_age = col1.number_input("Edad", min_value=10, max_value=100, step=1, value=25)
        reg_weight = col2.number_input("Peso (kg)", min_value=30.0, max_value=200.0, step=0.1, value=70.0)
        reg_height = col3.number_input("Altura (cm)", min_value=100, max_value=250, step=1, value=170)
        reg_gender = st.selectbox("Género",["Masculino", "Femenino", "Otro"])
        
        st.markdown("**3. Objetivos**")
        reg_goals = st.text_area("Objetivo principal (Ej: Perder grasa, ganar masa muscular)")
        reg_rest = st.text_input("Restricciones (Ej: Vegano, Intolerante a la lactosa)")
        
        if st.button("Crear Cuenta y Entrar 🚀", type="primary", use_container_width=True):
            if reg_user and reg_pin and reg_sa and reg_name:
                # Comprobar si el usuario existe
                check = supabase.table("app_users").select("username").eq("username", reg_user).execute()
                if check.data:
                    st.error("Ese Nombre de Usuario ya está en uso. Elige otro.")
                else:
                    new_user = {
                        "username": reg_user, "pin": reg_pin, "security_question": reg_sq, "security_answer": reg_sa.lower(),
                        "name": reg_name, "age": reg_age, "weight": reg_weight, "height": reg_height, "gender": reg_gender,
                        "goals": reg_goals, "restrictions": reg_rest, "favorites":[]
                    }
                    supabase.table("app_users").insert(new_user).execute()
                    set_login_session(reg_user)
                    st.success("¡Cuenta creada!")
                    st.rerun()
            else:
                st.warning("Por favor, rellena los campos obligatorios.")

    with tab3:
        st.markdown("¿Olvidaste tu PIN?")
        rec_user = st.text_input("Introduce tu Usuario", key="rec_user")
        if st.button("Buscar Usuario"):
            res = supabase.table("app_users").select("security_question").eq("username", rec_user).execute()
            if res.data:
                st.session_state.recover_user = rec_user
                st.session_state.recover_q = res.data[0]["security_question"]
                st.success("Usuario encontrado.")
            else:
                st.error("Usuario no encontrado.")
                
        if "recover_user" in st.session_state:
            st.info(f"Pregunta: **{st.session_state.recover_q}**")
            rec_ans = st.text_input("Tu Respuesta")
            new_pin = st.text_input("Nuevo PIN", type="password")
            if st.button("Cambiar PIN", use_container_width=True):
                res = supabase.table("app_users").select("security_answer").eq("username", st.session_state.recover_user).execute()
                if res.data and res.data[0]["security_answer"] == rec_ans.lower():
                    supabase.table("app_users").update({"pin": new_pin}).eq("username", st.session_state.recover_user).execute()
                    st.success("¡PIN cambiado con éxito! Ya puedes iniciar sesión.")
                    del st.session_state.recover_user
                else:
                    st.error("Respuesta incorrecta.")
                    
    st.stop() # Detiene la app aquí si no hay sesión iniciada

# ==========================================
# CARGAR PERFIL DEL USUARIO ACTIVO
# ==========================================
user_profile = get_user_data(st.session_state.current_username)
if not user_profile:
    # Si la cookie existe pero el usuario fue borrado de la DB
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
    with st.expander(t["profile"], expanded=False):
        upd_weight = st.number_input("Peso Actual (kg)", value=float(user_profile.get("weight", 70.0)))
        upd_goals = st.text_area("Objetivos", value=user_profile.get("goals", ""))
        upd_rest = st.text_input("Restricciones", value=user_profile.get("restrictions", ""))
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
    if st.button(t.get("logout", "Cerrar Sesión"), type="secondary", use_container_width=True):
        logout()
        st.rerun()

# ==========================================
# UI: APLICACIÓN PRINCIPAL
# ==========================================
st.title(t["title"].format(name=user_profile["name"]))
st.markdown(t["subtitle"])

# --- FASE 1: INPUT DE INGREDIENTES ---
if st.session_state.step == "input" or st.session_state.step == "options":
    ingredients = st.text_area("👨‍🍳 " + t["assistant_msg"], placeholder=t["input_placeholder"])
    
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
    
    if st.button(t["start_over"], use_container_width=True):
        st.session_state.step = "input"
        st.session_state.options = None
        st.session_state.full_recipe = None
        st.rerun()

    st.markdown(f"<p class='hero-emoji'>{recipe.get('hero_emoji', '🍽️')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center;'>{recipe['recipe_name']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align:center; letter-spacing: 5px;'>{recipe.get('ingredients_emojis', '')}</h3>", unsafe_allow_html=True)
    
    st.info(f"**{t['note']}** {recipe.get('nutritionist_note', '')}")
    
    m = recipe['macros']
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
                new_recipe = call_ai_json(prompt, format_hint, lang_code, user_profile)
                if new_recipe:
                    st.session_state.full_recipe = new_recipe
                    st.rerun()
                    new_recipe = call_ai_json(prompt, format_hint, lang_code)
                    if new_recipe:
                        st.session_state.full_recipe = new_recipe
                        st.rerun()
