import pandas as pd
import mysql.connector

# Citește fișierul CSV
data = pd.read_csv('updated_medicine_with_allergies.csv')

# Înlocuiește valorile NaN cu șiruri goale
data = data.fillna('')

# Conectează-te la baza de date MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="dia22",  # Parola ta MySQL
    database="medicine_recommendation"  # Numele bazei de date
)
cursor = conn.cursor()

# Importă datele în tabel
for _, row in data.iterrows():
    cursor.execute("""
    INSERT INTO medicines (Drug_Name, Reason, Description, Interactions, Allergenic_Ingredients, Contraindications)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (row['Drug_Name'], row['Reason'], row['Description'], row['Interactions'], row['Allergenic_Ingredients'], row['Contraindications']))

# Salvează modificările și închide conexiunea
conn.commit()
cursor.close()
conn.close()

print("Datele au fost importate cu succes în tabelul 'medicines'.")
