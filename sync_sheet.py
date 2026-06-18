import gspread
from google.oauth2.service_account import Credentials
import requests
import time

# 1. Configuration
SPREADSHEET_ID = '1QsE3Y4HyCgcnT3Boi-YfZ857bN9tNZkMWLQ9OjdJlqk'
API_URL = 'http://127.0.0.1:8000/api/v1/issue/'

# 2. Authenticate with Google
scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('google_credentials.json', scopes=scopes)
client = gspread.authorize(creds)

def run_sync():
    print("Fetching data from Google Sheets...")
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    
    # Read all rows
    records = sheet.get_all_records()
    
    row_number = 2 # Start at row 2 (row 1 is headers)
    
    for record in records:
        name = record.get('Name')
        course = record.get('Course')
        grad_date = record.get('Graduation Date')
        tx_hash = record.get('Transaction Hash', '') # Check if column exists
        
        # If the row has data but NO transaction hash, it needs to be anchored!
        if name and course and grad_date and not tx_hash:
            print(f"\nProcessing new graduate: {name}...")
            
            # Prepare the payload for your Django API
            payload = {
                "name": name,
                "course": course,
                "graduation_date": grad_date
            }
            
            # Send data to your Web3 Django Backend
            try:
                print("Anchoring to Sepolia Blockchain...")
                response = requests.post(API_URL, json=payload)
                response_data = response.json()
                
                if response.status_code == 201:
                    new_hash = response_data['transaction_hash']
                    print(f"Success! Hash: {new_hash}")
                    
                    # Update the Google Sheet with the new hash in Column D
                    sheet.update_cell(1, 4, "Transaction Hash") # Ensure header exists
                    sheet.update_cell(row_number, 4, new_hash)
                    print(f"Google Sheet updated for {name}.")
                else:
                    print(f"API Error for {name}: {response_data}")
                    
            except Exception as e:
                print(f"Failed to connect to Django API: {e}")
                
        row_number += 1

if __name__ == "__main__":
    run_sync()