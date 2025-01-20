
from flask import Flask, request, render_template, session
import mysql.connector
import pickle
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Inițializarea aplicației Flask
app = Flask(__name__)

# Configurarea conexiunii la baza de date MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",               # Numele utilizatorului MySQL
    password="dia22",      # Parola utilizatorului MySQL
    database="medicine_recommendation"  # Numele bazei de date
)

# Încarcă matricea de similaritate
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Funcția pentru preluarea medicamentelor din baza de date
def get_medicines():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id, Drug_Name FROM medicines")
    medicines = cursor.fetchall()
    cursor.close()
    return medicines

# Funcția pentru recomandarea medicamentelor bazată pe similaritate
def recommend(medicine):
    # Obține lista medicamentelor
    medicines = get_medicines()
    medicine_names = [m['Drug_Name'] for m in medicines]
    medicine_ids = {m['Drug_Name']: m['id'] for m in medicines}

    # Găsește indexul medicamentului selectat
    if medicine not in medicine_names:
        return [], [], [], []

    medicine_index = medicine_names.index(medicine)

    # Obține vectorul de similaritate pentru medicamentul selectat
    distances = similarity[medicine_index]

    # Sortează medicamentele după similaritate și selectează primele 5 rezultate
    medicines_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    # Creează o listă cu medicamentele recomandate
    recommended_medicines = [medicine_names[i[0]] for i in medicines_list]

    # Obține detalii despre medicamentul selectat
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medicines WHERE Drug_Name = %s", (medicine,))
    selected_medicine = cursor.fetchone()

    # Extrage informațiile despre interacțiuni, alergii și contraindicații
    interactions = selected_medicine['Interactions'].split(',') if selected_medicine['Interactions'] else ["No known interactions."]
    allergy_warning = [f"Warning: Contains {i.strip()}." for i in selected_medicine['Allergenic_Ingredients'].split(',')] if selected_medicine['Allergenic_Ingredients'] else []
    contraindication_warning = [f"Warning: Contraindicated for {i.strip()}." for i in selected_medicine['Contraindications'].split(',')] if selected_medicine['Contraindications'] else []

    cursor.close()

    # Returnează recomandările și avertismentele
    return recommended_medicines, interactions, allergy_warning, contraindication_warning

# Ruta principală (pagina de start)
@app.route('/', methods=['GET', 'POST'])
def index():
    medicines = get_medicines()
    recommendations = []
    interactions = []
    allergy_warning = []
    contraindication_warning = []
    selected_medicine_name = None
    patient_data = {}  # Pentru a păstra datele pacientului temporar

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'recommend':  # Recomandare medicamente
            selected_medicine_name = request.form['medicine']
            recommendations, interactions, allergy_warning, contraindication_warning = recommend(selected_medicine_name)

            # Salvează temporar datele pacientului în variabila locală
            patient_data = {
                'first_name': request.form.get('firstName'),
                'last_name': request.form.get('lastName'),
                'email': request.form.get('email'),
                'doses_per_day': request.form.get('dosesPerDay'),
                'administration_times': request.form.get('administrationTimes'),
                'selected_medicine_name': selected_medicine_name
            }

        elif action == 'submit':  # Salvare pacient în baza de date
            # Preia datele pacientului din formular
            first_name = request.form['firstName']
            last_name = request.form['lastName']
            email = request.form['email']
            doses_per_day = request.form['dosesPerDay']
            administration_times = request.form['administrationTimes']
            selected_medicine_name = request.form['medicine']

            # Salvează pacientul în baza de date
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO patients (first_name, last_name, email, times_per_day, administration_times, Drug_Name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (first_name, last_name, email, doses_per_day, administration_times, selected_medicine_name))
            db.commit()
            cursor.close()
            return "Patient information saved successfully!"

    return render_template(
        'index.html',
        medicines=[m['Drug_Name'] for m in medicines],
        recommendations=recommendations,
        interactions=interactions,
        allergy_warning=allergy_warning,
        contraindication_warning=contraindication_warning,
        selected_medicine_name=selected_medicine_name,
        patient_data=patient_data  # Trimite datele temporare la frontend
    )

# Ruta pentru afișarea detaliilor unui medicament specific
@app.route('/details', methods=['GET'])
def details():
    # Preia numele medicamentului din parametrii URL
    medicine_name = request.args.get('medicine')
    interactions = []
    allergy_warning = []
    contraindication_warning = []

    if medicine_name:
        # Găsește detaliile medicamentului selectat
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM medicines WHERE Drug_Name = %s", (medicine_name,))
        medicine = cursor.fetchone()

        if medicine:
            interactions = medicine['Interactions'].split(',') if medicine['Interactions'] else []
            allergy_warning = [f"Contains {i.strip()}" for i in medicine['Allergenic_Ingredients'].split(',')] if medicine['Allergenic_Ingredients'] else []
            contraindication_warning = [f"Contraindicated for {i.strip()}" for i in medicine['Contraindications'].split(',')] if medicine['Contraindications'] else []

        cursor.close()

    # Redă șablonul HTML pentru pagina de detalii
    return render_template(
        'details.html',
        medicine_name=medicine_name,           # Numele medicamentului
        interactions=interactions,            # Lista interacțiunilor medicamentoase
        allergy_warning=allergy_warning,      # Lista avertismentelor despre alergii
        contraindication_warning=contraindication_warning  # Lista avertismentelor despre contraindicații
    )
    
def send_email(to_email, subject, body):
    try:
        sender_email = "florin.campan95@gmail.com"
        sender_password = "dtsc eksk voie mtip"

        # Configurarea mesajului
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        # Conectarea la serverul SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()

        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Rulează aplicația în modul de debug
if __name__ == '__main__':
    app.run(debug=True)

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

