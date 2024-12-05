from flask import Flask, request, render_template   # Creează și gestionează aplicația web.
import pickle    # Încarcă fișiere salvate cu date serializate (de ex. matricea de similaritate).
import pandas as pd   # Manipulează datele dintr-un fișier CSV.

# Inițializarea aplicației Flask
app = Flask(__name__)

# Încarcă fișierul CSV cu informații despre medicamente, incluzând alergii și contraindicații
medicines = pd.read_csv('updated_medicine_with_allergies.csv')

# Încarcă matricea de similaritate cosinus dintre medicamente
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Funcția care generează recomandări de medicamente similare
def recommend(medicine):
    # Găsește indexul medicamentului selectat în DataFrame
    medicine_index = medicines[medicines['Drug_Name'] == medicine].index[0]
    
    # Obține vectorul de similaritate pentru medicamentul selectat
    distances = similarity[medicine_index]
    
    # Sortează medicamentele după similaritate și selectează primele 5 rezultate
    medicines_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    # Creează o listă cu numele medicamentelor recomandate
    recommended_medicines = []
    for i in medicines_list:
        recommended_medicines.append(medicines.iloc[i[0]].Drug_Name)

    # Verifică existența interacțiunilor medicamentoase
    if 'Interactions' in medicines.columns and pd.notna(medicines.loc[medicine_index, 'Interactions']):
        interactions = medicines.loc[medicine_index, 'Interactions'].split(',')
    else:
        interactions = ["No known interactions for this medicine."]

    # Verifică ingredientele alergene și contraindicațiile
    allergenic_ingredients = medicines.loc[medicine_index, 'Allergenic_Ingredients']
    contraindications = medicines.loc[medicine_index, 'Contraindications']
    allergy_warning = []
    contraindication_warning = []

    # Creează mesaje de avertizare pentru alergii
    if pd.notna(allergenic_ingredients):
        allergy_warning = [f"Warning: Contains {ingredient.strip()}." for ingredient in allergenic_ingredients.split(',')]
    
    # Creează mesaje de avertizare pentru contraindicații
    if pd.notna(contraindications):
        contraindication_warning = [f"Warning: Contraindicated for {condition.strip()}." for condition in contraindications.split(',')]

    # Returnează recomandările, interacțiunile și avertismentele
    return recommended_medicines, interactions, allergy_warning, contraindication_warning

# Ruta principală (pagina de start)
@app.route('/', methods=['GET', 'POST'])
def index():
    # Inițializează variabilele pentru recomandări, interacțiuni și avertismente
    recommendations = []
    interactions = []
    allergy_warning = []
    contraindication_warning = []
    selected_medicine_name = None

    # Dacă utilizatorul trimite un formular (POST), generează recomandări
    if request.method == 'POST':
        selected_medicine_name = request.form['medicine']  # Preia medicamentul selectat
        # Obține recomandările și avertismentele pentru medicamentul selectat
        recommendations, interactions, allergy_warning, contraindication_warning = recommend(selected_medicine_name)
    
    # Redă șablonul HTML pentru pagina principală
    return render_template(
        'index.html',
        medicines=medicines['Drug_Name'].values,  # Lista medicamentelor disponibile
        recommendations=recommendations,         # Medicamentele recomandate
        interactions=interactions,               # Interacțiunile medicamentoase
        allergy_warning=allergy_warning,         # Avertismente despre alergii
        contraindication_warning=contraindication_warning,  # Avertismente despre contraindicații
        selected_medicine_name=selected_medicine_name       # Numele medicamentului selectat
    )

# Ruta pentru afișarea detaliilor unui medicament specific
@app.route('/details', methods=['GET'])
def details():
    # Preia numele medicamentului din parametrii URL
    medicine_name = request.args.get('medicine')
    interactions = []
    allergy_warning = []
    contraindication_warning = []

    # Dacă un medicament a fost selectat, obține detaliile acestuia
    if medicine_name:
        medicine_index = medicines[medicines['Drug_Name'] == medicine_name].index[0]
        # Verifică interacțiunile medicamentoase
        if 'Interactions' in medicines.columns and pd.notna(medicines.loc[medicine_index, 'Interactions']):
            interactions = medicines.loc[medicine_index, 'Interactions'].split(',')

        # Verifică ingredientele alergene
        if pd.notna(medicines.loc[medicine_index, 'Allergenic_Ingredients']):
            allergy_warning = [f"Contains {ingredient.strip()}" for ingredient in medicines.loc[medicine_index, 'Allergenic_Ingredients'].split(',')]

        # Verifică contraindicațiile
        if pd.notna(medicines.loc[medicine_index, 'Contraindications']):
            contraindication_warning = [f"Contraindicated for {condition.strip()}" for condition in medicines.loc[medicine_index, 'Contraindications'].split(',')]

    # Redă șablonul HTML pentru pagina de detalii
    return render_template(
        'details.html',
        medicine_name=medicine_name,           # Numele medicamentului
        interactions=interactions,            # Lista interacțiunilor medicamentoase
        allergy_warning=allergy_warning,      # Lista avertismentelor despre alergii
        contraindication_warning=contraindication_warning  # Lista avertismentelor despre contraindicații
    )

# Rulează aplicația în modul de debug
if __name__ == '__main__':
    app.run(debug=True)
