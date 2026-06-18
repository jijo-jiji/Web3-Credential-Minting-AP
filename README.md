# Web3 Immutable Data Anchoring & Verification API

This project is a decentralized application (dApp) backend built with Django REST Framework and Web3.py. It automates the process of verifying and anchoring high-value digital records (e.g., academic credentials, employment contracts, software licenses, or compliance certificates) onto the Ethereum Sepolia Testnet and synchronizes status updates back to a Google Sheet.

🎯 The Business Case: Universal Data Privacy & Compliance

## 🎯 The Business Case: Universal Data Privacy & Compliance

Storing personal identifiable information (PII) like employee salaries, medical records, or student details directly on a public blockchain violently violates privacy frameworks like the PDPA and GDPR.

This architecture solves that by acting as a universal cryptographic bridge. It takes plain-text data from a Web2 source (e.g., Google Sheets, ERPs, or legacy databases), runs it through a SHA-256 one-way hashing algorithm, and only anchors the resulting 64-character digital fingerprint to the blockchain. Third parties can verify data mathematically without ever exposing the raw records on a public ledger.

---

## 🏗️ System Architecture

graph TD
    A[Web2 Database / Google Sheet] <-->|Read/Write via API| B(Sync Engine: sync_sheet.py)
    B -->|POST Record Info| C[Django Backend]
    C -->|Hash Data & Send Txn| D[Alchemy RPC Node]
    D -->|Anchor Hash| E[Sepolia Smart Contract]
    C -->|Return Txn Hash| B

- **Web2 Database (Google Sheets Demo)**: Serves as the administrative dashboard. The synchronizer script reads new entries and writes back transaction hashes once they are successfully anchored on-chain.
- **Django Backend**: Generates a SHA-256 hash of the target information, formats it for Solidity (`bytes32`), and signs/sends a transaction to anchor it.
- **Sepolia Smart Contract**: Stores valid hashes immutably on the Ethereum blockchain for decentralized verification. Contains logic to prevent duplicate record entries to save gas.

Web2 Database (Google Sheets Demo): Serves as the administrative dashboard. The synchronizer script reads new entries and writes back transaction hashes once they are successfully anchored on-chain.

## 🚀 Setup & Installation

### 1. Prerequisites
- **Python 3.10+**
- A **Google Cloud Platform (GCP)** project with the Google Sheets and Google Drive APIs enabled.
- An **Alchemy** (or Infura) API Key for Ethereum Sepolia.
- A **Sepolia wallet** with test ETH.

Clone the repository and set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt


3. Environment Configuration (.env)

Create a .env file in the root directory:

# Web3 Configuration
ALCHEMY_RPC_URL="[https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY](https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY)"
WALLET_PRIVATE_KEY="YOUR_WALLET_PRIVATE_KEY"
CONTRACT_ADDRESS="YOUR_SMART_CONTRACT_ADDRESS"

# Django Configuration
DJANGO_SECRET_KEY="your-secret-key"
DEBUG=True

### 4. Smart Contract ABI & Google Credentials
For security and code cleanliness, sensitive files and massive JSON arrays are kept out of the main logic:
- **`google_credentials.json`**: Place your GCP Service Account credential JSON file in the root directory. Ensure the target Google Sheet is shared with the `client_email` specified in this file (Editor permissions).
- **`abi.json`**: Create this file in your `credential_api` folder and paste the compiled Application Binary Interface (ABI) of your Solidity smart contract so Web3.py can interact with it.

For security and code cleanliness, sensitive files and massive JSON arrays are kept out of the main logic:

## 📡 API Endpoints

### 1. Issue & Anchor Record
Hashes the payload data, signs it with the server wallet, and anchors it on the blockchain. *(Note: This demo is currently configured for an Academic Credential schema, but the underlying engine accepts any JSON structure).*

* **URL**: `/api/v1/issue/`
* **Method**: `POST`
* **Payload**:
  ```json
  {
    "name": "Azizi",
    "course": "Software Engineering",
    "graduation_date": "2026-10-01"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "Record successfully anchored to blockchain.",
    "document_hash": "dfba51eec2cbf7eafec61e535081287c022edf7ec353abd738efbe5b805b31a1",
    "transaction_hash": "0x07c118db7ad5...",
    "explorer_url": "https://sepolia.etherscan.io/tx/0x07c118db7ad5..."
  }
  ```

### 2. Verify Record
Queries the smart contract directly to verify if the given SHA-256 hash was officially issued. This is a read-only call (0 gas).

* **URL**: `/api/v1/verify/<document_hash>/`
* **Method**: `GET`
* **Success Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Record is valid and mathematically verified.",
    "document_hash": "dfba51eec2cbf7eafec61e535081287c022edf7ec353abd738efbe5b805b31a1",
    "anchored_timestamp": 1718686080
  }
  ```

URL: /api/v1/issue/

## ⚙️ Usage (Demo Flow)

python manage.py runserver

### Step 2: Run the Web2-to-Web3 Sync Script
To scan the spreadsheet for new un-anchored records, process them, and save the transaction hashes back to Google Sheets, run:
```bash
python sync_sheet.py
```

---

## 🛣️ Production Roadmap (Future Scope)

While this prototype uses a manual trigger for the synchronization script, a production-grade deployment for enterprise clients would implement:
- **Event-Driven Webhooks**: Replacing the polling script with direct Webhook triggers from CRMs, ERPs, or Google Apps Script.
- **Asynchronous Task Queues**: Using Celery/Redis to handle Web3 transactions in the background to prevent API blocking during Ethereum network congestion.
- **Key Management Systems (KMS)**: Migrating the `.env` private key to AWS KMS or HashiCorp Vault for enterprise-grade cryptographic security.