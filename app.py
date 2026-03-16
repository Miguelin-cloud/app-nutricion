import streamlit as st
import sqlite3
import json
from groq import Groq
import os

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y CSS
# ==========================================
st.set_page_config(page_title="Smart AI Nutritionist", page_icon="🍲", layout="wide")

# Inyectamos CSS personalizado para hacer la app bonita y profesional
st.markdown("""
    <style>
    /* Hero Emoji Gigante */
    .hero-emoji { font-size: 100px; text-align: center; margin: 0; padding: 0; line-height: 1.2; }
    
    /* Tarjeta Dorada para la Recomendación */
    .golden-card {
        background: linear-gradient(135deg, #FFDF00 0%, #D4AF37 100%);
        padding: 2px;
        border-radius: 12px;
        margin-bottom: 10px;
    }
    .golden-card-content {
        background-color: #FFFAEC;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        color: #333;
    }
    
    /* Etiqueta Nutricional Profesional */
    .nutrition-label {
        border: 2px solid #111;
        padding: 15px;
        background-color: white;
        color: black;
        font-family: 'Arial', sans-serif;
        border-radius: 8px;
        max-width: 350px;
        margin: auto;
    }
    .nutrition-label h2 { margin: 0; font-size: 28px; font-weight: 900; border-bottom: 8px solid #111; padding-bottom: 5px; color: black; }
    .nut-row { display: flex; justify-content: space-between; border-bottom: 1px solid #999; padding: 4px 0; font-size: 15px; }
    .nut-row.thick { border-bottom: 4px solid #111; }
    .nut-row.indent { padding-left: 15px; font-size: 14px; }
    .nut-bold { font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SISTEMA MULTIDIOMA
# ==========================================
TRANSLATIONS = {
    "🇪🇸 Español": {
        "lang_code": "Spanish",
        "profile": "👤 Perfil Nutricional",
        "diet": "Restricciones (Ej: Vegano, Alergia nueces)",
        "update_prof": "Actualizar Perfil",
        "prof_updated": "¡Perfil actualizado!",
        "favs": "⭐ Recetas Favoritas",
        "no_favs": "Aún no hay favoritos.",
        "title": "¿Qué tenemos para hoy? 🍲",
        "subtitle": "Dime qué ingredientes tienes y crearé la comida perfecta para ti.",
        "assistant_msg": "Escribe tus ingredientes abajo. ¡Hagamos algo sano y delicioso!",
        "input_placeholder": "Ej: Pechuga de pollo, arroz, brócoli, salsa de soja...",
        "find_btn": "🔍 Buscar Recetas",
        "analyzing": "Analizando ingredientes y diseñando opciones...",
        "here_options": "Aquí tienes lo que podemos preparar:",
        "diff": "Dificultad",
        "time": "Tiempo",
        "health": "Salud",
        "cook_btn": "Cocinar {}",
        "loading_recipe": "Calculando macros perfectos para {}...",
        "start_over": "← Empezar de Nuevo",
        "note": "Nota del Nutricionista:",
        "ingredients": "🛒 Ingredientes",
        "save_fav": "⭐ Guardar en Favoritos",
        "saved": "¡Guardado en Favoritos!",
        "instructions": "👨‍🍳 Instrucciones de Preparación",
        "adjust_title": "⚖️ Ajustar Macros",
        "adjust_sub": "¿Necesitas otras cantidades? Pídemelo y recalcularé la receta.",
        "adjust_ph": "Ej: 'Añade 20g de proteína' o 'Baja los carbohidratos'",
        "recalc_btn": "Recalcular Receta",
        "recalculating": "Ajustando cantidades y recalculando..."
    },
    "🇬🇧 English": {
        "lang_code": "English",
        "profile": "👤 Nutrition Profile",
        "diet": "Restrictions (e.g., Vegan, Nut Allergy)",
        "update_prof": "Update Profile",
        "prof_updated": "Profile updated!",
        "favs": "⭐ Favorite Recipes",
        "no_favs": "No favorites saved yet.",
        "title": "What do we have for today? 🍲",
        "subtitle": "Tell me what ingredients you have, and I'll craft the perfect meal.",
        "assistant_msg": "List your ingredients below. Let's make something healthy and delicious!",
        "input_placeholder": "e.g., Chicken breast, rice, broccoli, soy sauce...",
        "find_btn": "🔍 Find Recipes",
        "analyzing": "Analyzing ingredients and crafting options...",
        "here_options": "Here is what we can make:",
        "diff": "Difficulty",
        "time": "Time",
        "health": "Health",
        "cook_btn": "Cook {}",
        "loading_recipe": "Formulating perfect macros for {}...",
        "start_over": "← Start Over",
        "note": "Nutritionist's Note:",
        "ingredients": "🛒 Ingredients",
        "save_fav": "⭐ Save to Favorites",
        "saved": "Saved to Favorites!",
        "instructions": "👨‍🍳 Instructions",
        "adjust_title": "⚖️ Adjust Macros",
        "adjust_sub": "Need to hit different targets? Tell me to recalculate.",
        "adjust_ph": "e.g., 'Add 20g more protein' or 'Reduce carbs'",
        "recalc_btn": "Recalculate Recipe",
        "recalculating": "Adjusting quantities and recalculating..."
    },
    "🇫🇷 Français": {
        "lang_code": "French",
        "profile": "👤 Profil Nutritionnel",
        "diet": "Restrictions (ex: Végan, Allergie aux noix)",
        "update_prof": "Mettre à jour le profil",
        "prof_updated": "Profil mis à jour !",
        "favs": "⭐ Recettes Favorites",
        "no_favs": "Aucun favori enregistré.",
        "title": "Qu'avons-nous pour aujourd'hui ? 🍲",
        "subtitle": "Dites-moi quels ingrédients vous avez, et je créerai le repas parfait.",
        "assistant_msg": "Énumérez vos ingrédients ci-dessous. Faisons quelque chose de sain !",
        "input_placeholder": "ex: Blanc de poulet, riz, brocoli, sauce soja...",
        "find_btn": "🔍 Trouver des recettes",
        "analyzing": "Analyse des ingrédients et création d'options...",
        "here_options": "Voici ce que nous pouvons préparer :",
        "diff": "Difficulté",
        "time": "Temps",
        "health": "Santé",
        "cook_btn": "Cuisiner {}",
        "loading_recipe": "Formulation des macros parfaites pour {}...",
        "start_over": "← Recommencer",
        "note": "Note du Nutritionniste :",
        "ingredients": "🛒 Ingrédients",
        "save_fav": "⭐ Enregistrer aux favoris",
        "saved": "Enregistré aux favoris !",
        "instructions": "👨‍🍳 Instructions",
        "adjust_title": "⚖️ Ajuster les Macros",
        "adjust_sub": "Besoin d'autres cibles ? Dites-le moi pour recalculer.",
        "adjust_ph": "ex: 'Ajouter 20g de protéines' ou 'Réduire les glucides'",
        "recalc_btn": "Recalculer la recette",
        "recalculating": "Ajustement des quantités et recalcul..."
    },
    "🇮🇹 Italiano": {
        "lang_code": "Italian",
        "profile": "👤 Profilo Nutrizionale",
        "diet": "Restrizioni (es. Vegano, Allergie)",
        "update_prof": "Aggiorna Profilo",
        "prof_updated": "Profilo aggiornato!",
        "favs": "⭐ Ricette Preferite",
        "no_favs": "Ancora nessun preferito.",
        "title": "Cosa abbiamo per oggi? 🍲",
        "subtitle": "Dimmi quali ingredienti hai e creerò il pasto perfetto.",
        "assistant_msg": "Elenca i tuoi ingredienti qui sotto. Facciamo qualcosa di sano!",
        "input_placeholder": "es. Petto di pollo, riso, broccoli, salsa di soia...",
        "find_btn": "🔍 Trova Ricette",
        "analyzing": "Analisi degli ingredienti in corso...",
        "here_options": "Ecco cosa possiamo preparare:",
        "diff": "Difficoltà",
        "time": "Tempo",
        "health": "Salute",
        "cook_btn": "Cucina {}",
        "loading_recipe": "Calcolando i macro perfetti per {}...",
        "start_over": "← Ricomincia",
        "note": "Nota del Nutrizionista:",
        "ingredients": "🛒 Ingredienti",
        "save_fav": "⭐ Salva nei Preferiti",
        "saved": "Salvato nei Preferiti!",
        "instructions": "👨‍🍳 Istruzioni",
        "adjust_title": "⚖️ Regola Macro",
        "adjust_sub": "Hai bisogno di obiettivi diversi? Dimmi di ricalcolare.",
        "adjust_ph": "es. 'Aggiungi 20g di proteine' o 'Riduci i carboidrati'",
        "recalc_btn": "Ricalcola Ricetta",
        "recalculating": "Regolazione delle quantità in corso..."
    }
}

# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ==========================================
DB_FILE = "nutrition_app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (id INTEGER PRIMARY KEY, restrictions TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS favorite_recipes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, recipe_data TEXT)''')
    c.execute("SELECT * FROM user_profile WHERE id=1")
    if not c.fetchone():
        c.execute("INSERT INTO user_profile (id, restrictions) VALUES (1, '')")
    conn.commit()
    conn.close()

def get_restrictions():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT restrictions FROM user_profile WHERE id=1")
    res = c.fetchone()[0]
    conn.close()
    return res

def update_restrictions(new_restrictions):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE user_profile SET restrictions=? WHERE id=1", (new_restrictions,))
    conn.commit()
    conn.close()

def save_favorite(name, recipe_data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO favorite_recipes (name, recipe_data) VALUES (?, ?)", (name, json.dumps(recipe_data)))
    conn.commit()
    conn.close()

def get_favorites():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, recipe_data FROM favorite_recipes")
    favorites = c.fetchall()
    conn.close()
    return favorites

init_db()

# ==========================================
# ESTADO DE LA SESIÓN
# ==========================================
if "step" not in st.session_state: st.session_state.step = "input"
if "options" not in st.session_state: st.session_state.options = None
if "selected_option" not in st.session_state: st.session_state.selected_option = None
if "full_recipe" not in st.session_state: st.session_state.full_recipe = None

# ==========================================
# IA (GROQ)
# ==========================================
def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("Groq API Key not found.")
        st.stop()
    return Groq(api_key=api_key)

def call_ai_json(prompt, expected_format_hint, lang_code):
    client = get_groq_client()
    system_prompt = f"""
    You are a strict fitness nutritionist, but with empathy and realistic thoughts. 
    You encourage the user to hit their goals, acknowledge when an ingredient might not be the healthiest but offer practical balance, and maintain a highly structured, professional yet warm tone.
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
# UI: BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    selected_lang = st.selectbox("🌐 Idioma / Language", list(TRANSLATIONS.keys()))
    t = TRANSLATIONS[selected_lang]
    lang_code = t["lang_code"]
    
    st.divider()
    st.title(t["profile"])
    current_restrictions = get_restrictions()
    new_restrictions = st.text_area(t["diet"], value=current_restrictions)
    if st.button(t["update_prof"]):
        update_restrictions(new_restrictions)
        st.success(t["prof_updated"])
    
    st.divider()
    st.title(t["favs"])
    favs = get_favorites()
    if favs:
        for fav_name, fav_data in favs:
            with st.expander(fav_name):
                data = json.loads(fav_data)
                st.write(f"🔥 {data['macros']['calories']}")
                st.write(f"💪 {data['macros']['protein']}")
    else:
        st.info(t["no_favs"])

# ==========================================
# UI: APLICACIÓN PRINCIPAL
# ==========================================
st.title(t["title"])
st.markdown(t["subtitle"])

# --- FASE 1: INPUT DE INGREDIENTES ---
if st.session_state.step == "input" or st.session_state.step == "options":
    with st.chat_message("assistant"):
        st.write(t["assistant_msg"])
        
    ingredients = st.text_input("", placeholder=t["input_placeholder"])
    
    if st.button(t["find_btn"], type="primary"):
        if ingredients:
            with st.spinner(t["analyzing"]):
                prompt = f"Ingredients: {ingredients}. Restrictions: {get_restrictions()}."
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
                res = call_ai_json(prompt, format_hint, lang_code)
                if res and "options" in res:
                    st.session_state.options = res["options"]
                    st.session_state.step = "options"
                    st.rerun()

# --- FASE 2: OPCIONES DE RECETAS (TARJETA DORADA) ---
if st.session_state.step == "options" and st.session_state.options:
    st.divider()
    st.subheader(t["here_options"])
    cols = st.columns(3)
    
    for i, opt in enumerate(st.session_state.options):
        with cols[i]:
            if i == 0:
                # Recomendación del Chef (Tarjeta Dorada)
                st.markdown("""
                <div class="golden-card">
                    <div class="golden-card-content">
                        <span style="color:#D4AF37; font-weight:bold; font-size:14px;">🌟 CHEF'S RECOMMENDATION 🌟</span>
                        <h1 style="font-size: 60px; margin: 0;">{}</h1>
                        <h3 style="margin: 5px 0;">{}</h3>
                    </div>
                </div>
                """.format(opt.get('hero_emoji', '🍽️'), opt['name']), unsafe_allow_html=True)
            else:
                # Tarjetas Normales
                st.markdown(f"<h1 style='text-align:center; font-size:50px; margin:0;'>{opt.get('hero_emoji', '🍽️')}</h1>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align:center;'>{opt['name']}</h3>", unsafe_allow_html=True)
            
            st.write(f"**{t['diff']}:** {opt['difficulty']}")
            st.write(f"**{t['time']}:** {opt['time']}")
            st.write(f"**{t['health']}:** {opt['health_score']}/10")
            st.caption(opt['description'])
            
            if st.button(t["cook_btn"].format(""), key=f"btn_cook_{i}", use_container_width=True):
                st.session_state.selected_option = opt
                st.session_state.step = "recipe_loading"
                st.rerun()

# --- FASE 3: GENERAR RECETA COMPLETA ---
if st.session_state.step == "recipe_loading":
    with st.spinner(t["loading_recipe"].format(st.session_state.selected_option['name'])):
        prompt = f"Generate full recipe for '{st.session_state.selected_option['name']}'. Restrictions: {get_restrictions()}."
        format_hint = """
        Return strictly in this JSON format. Be precise with the nutrition label:
        {
            "recipe_name": "Name",
            "hero_emoji": "🥘",
            "ingredients_emojis": "🍅🧅🍗🌿",
            "nutritionist_note": "A short, empathetic note...",
            "macros": {
                "calories": "450 kcal",
                "total_fat": "15g",
                "saturated_fat": "3g",
                "total_carbs": "30g",
                "total_sugars": "5g",
                "added_sugars": "0g",
                "fiber": "6g",
                "protein": "40g",
                "sodium": "400mg"
            },
            "ingredients":[{"item": "Chicken breast", "qty": "200g"}],
            "instructions":["Step 1...", "Step 2..."]
        }
        """
        res = call_ai_json(prompt, format_hint, lang_code)
        if res:
            st.session_state.full_recipe = res
            st.session_state.step = "recipe_view"
            st.rerun()

# --- FASE 4: VISUALIZACIÓN DE LA RECETA ---
if st.session_state.step == "recipe_view" and st.session_state.full_recipe:
    recipe = st.session_state.full_recipe
    
    if st.button(t["start_over"]):
        st.session_state.step = "input"
        st.session_state.options = None
        st.session_state.full_recipe = None
        st.rerun()

    # Cabecera Visual (Emoji Gigante y Título)
    st.markdown(f"<p class='hero-emoji'>{recipe.get('hero_emoji', '🍽️')}</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:center;'>{recipe['recipe_name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; letter-spacing: 5px;'>{recipe.get('ingredients_emojis', '')}</h2>", unsafe_allow_html=True)
    
    st.info(f"**{t['note']}** {recipe.get('nutritionist_note', '')}")
    
    st.divider()
    
    # Layout de 2 Columnas (Info / Preparación)
    col_info, col_prep = st.columns([1, 1.5])
    
    with col_info:
        # Etiqueta Nutricional Realista
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
        
        st.write("")
        if st.button(t["save_fav"], use_container_width=True):
            save_favorite(recipe["recipe_name"], recipe)
            st.success(t["saved"])
            
    with col_prep:
        st.subheader(t["ingredients"])
        for ing in recipe["ingredients"]:
            st.markdown(f"- **{ing['qty']}** {ing['item']}")
            
        st.subheader(t["instructions"])
        with st.expander("Ver Pasos de Preparación", expanded=True):
            for i, step in enumerate(recipe["instructions"]):
                st.write(f"**{i+1}.** {step}")

    st.divider()

    # --- FASE 5: AJUSTE DE MACROS ---
    st.subheader(t["adjust_title"])
    st.markdown(t["adjust_sub"])
    
    adj_col1, adj_col2 = st.columns([3, 1])
    with adj_col1:
        macro_adjustment = st.text_input("", placeholder=t["adjust_ph"])
    with adj_col2:
        st.markdown("<br>", unsafe_allow_html=True) 
        if st.button(t["recalc_btn"], use_container_width=True):
            if macro_adjustment:
                with st.spinner(t["recalculating"]):
                    prompt = f"Current recipe: {json.dumps(recipe)}. Adjustment requested: '{macro_adjustment}'. Recalculate quantities and macros."
                    format_hint = """
                    Return strictly in the exact same JSON format as the original recipe.
                    Update the macros, ingredients, and instructions accordingly.
                    """
                    new_recipe = call_ai_json(prompt, format_hint, lang_code)
                    if new_recipe:
                        st.session_state.full_recipe = new_recipe
                        st.rerun()