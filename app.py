
from flask import Flask, request, render_template
import pickle
import pandas as pd

app = Flask(__name__)

# Încarcă noul fișier CSV cu alergii și contraindicații
medicines = pd.read_csv('updated_medicine_with_allergies.csv')

# Încarcă fișierul pickle existent
similarity = pickle.load(open('similarity.pkl', 'rb'))

def recommend(medicine):
    # Găsește indexul medicamentului selectat
    medicine_index = medicines[medicines['Drug_Name'] == medicine].index[0]
    distances = similarity[medicine_index]
    medicines_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_medicines = []
    for i in medicines_list:
        recommended_medicines.append(medicines.iloc[i[0]].Drug_Name)

    # Verifică existența interacțiunilor
    if 'Interactions' in medicines.columns and pd.notna(medicines.loc[medicine_index, 'Interactions']):
        interactions = medicines.loc[medicine_index, 'Interactions'].split(',')
    else:
        interactions = ["No known interactions for this medicine."]

    # Verificare alergii și contraindicații
    allergenic_ingredients = medicines.loc[medicine_index, 'Allergenic_Ingredients']
    contraindications = medicines.loc[medicine_index, 'Contraindications']
    allergy_warning = []
    contraindication_warning = []

    if pd.notna(allergenic_ingredients):
        allergy_warning = [f"Warning: Contains {ingredient.strip()}." for ingredient in allergenic_ingredients.split(',')]
    
    if pd.notna(contraindications):
        contraindication_warning = [f"Warning: Contraindicated for {condition.strip()}." for condition in contraindications.split(',')]

    return recommended_medicines, interactions, allergy_warning, contraindication_warning

@app.route('/', methods=['GET', 'POST'])
def index():
    recommendations = []
    interactions = []
    allergy_warning = []
    contraindication_warning = []
    selected_medicine_name = None

    if request.method == 'POST':
        selected_medicine_name = request.form['medicine']
        recommendations, interactions, allergy_warning, contraindication_warning = recommend(selected_medicine_name)
    
    return render_template(
        'index.html',
        medicines=medicines['Drug_Name'].values,
        recommendations=recommendations,
        interactions=interactions,
        allergy_warning=allergy_warning,
        contraindication_warning=contraindication_warning,
        selected_medicine_name=selected_medicine_name
    )

@app.route('/details', methods=['GET'])
def details():
    medicine_name = request.args.get('medicine')
    interactions = []
    allergy_warning = []
    contraindication_warning = []

    if medicine_name:
        medicine_index = medicines[medicines['Drug_Name'] == medicine_name].index[0]
        if 'Interactions' in medicines.columns and pd.notna(medicines.loc[medicine_index, 'Interactions']):
            interactions = medicines.loc[medicine_index, 'Interactions'].split(',')

        if pd.notna(medicines.loc[medicine_index, 'Allergenic_Ingredients']):
            allergy_warning = [f"Contains {ingredient.strip()}" for ingredient in medicines.loc[medicine_index, 'Allergenic_Ingredients'].split(',')]

        if pd.notna(medicines.loc[medicine_index, 'Contraindications']):
            contraindication_warning = [f"Contraindicated for {condition.strip()}" for condition in medicines.loc[medicine_index, 'Contraindications'].split(',')]

    return render_template(
        'details.html',
        medicine_name=medicine_name,
        interactions=interactions,
        allergy_warning=allergy_warning,
        contraindication_warning=contraindication_warning
    )

if __name__ == '__main__':
    app.run(debug=True)
