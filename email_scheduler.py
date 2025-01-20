import schedule
import time
from datetime import datetime
from app import db, send_email

def check_and_send_emails():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT first_name, email, administration_times FROM patients")
    patients = cursor.fetchall()
    cursor.close()

    # Afișează ora curentă
    current_time = datetime.now().strftime("%H:%M")
    print(f"Current time: {current_time}")

    for patient in patients:
        print(f"Checking patient: {patient['first_name']} with email: {patient['email']}")
        print(f"Scheduled times raw: {patient['administration_times']}")

        # Curățare și verificare ore
        times = [time.strip() for time in patient['administration_times'].split(',')]
        print(f"Formatted times for comparison: {times}")

        for time_slot in times:
            print(f"Comparing current_time: {current_time} with time_slot: {time_slot}")
            if current_time == time_slot:
                print(f"Match found! Sending email to {patient['email']} at {current_time}")
                subject = "It's time to take your medicine"
                body = f"Hello {patient['first_name']},\n\nThis is a reminder to take your medicine as scheduled at {current_time}."
                send_email(patient['email'], subject, body)
            else:
                print(f"No match for {patient['first_name']} at {time_slot}")

# Programarea funcției pentru a rula la fiecare minut
schedule.every(1).minute.do(check_and_send_emails)

if __name__ == '__main__':
    print("Starting email scheduler...")
    while True:
        schedule.run_pending()
        time.sleep(1)
