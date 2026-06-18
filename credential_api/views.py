import os
import json
import hashlib
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from web3 import Web3
from django.conf import settings

# 1. Initialize Web3 Connection
w3 = Web3(Web3.HTTPProvider(os.getenv("ALCHEMY_RPC_URL")))

# 2. Load Smart Contract Configuration
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")

# Load ABI from file
abi_file_path = os.path.join(settings.BASE_DIR, 'credential_api', 'abi.json')
with open(abi_file_path, 'r') as file:
    CONTRACT_ABI = json.load(file)

def get_contract_and_account():
    if not PRIVATE_KEY or PRIVATE_KEY.startswith("YOUR_"):
        raise ValueError("WALLET_PRIVATE_KEY is not configured in the .env file")
    if not CONTRACT_ADDRESS or CONTRACT_ADDRESS.startswith("YOUR_"):
        raise ValueError("CONTRACT_ADDRESS is not configured in the .env file")
    
    try:
        checksum_address = Web3.to_checksum_address(CONTRACT_ADDRESS)
    except ValueError:
        raise ValueError(f"Invalid CONTRACT_ADDRESS format: {CONTRACT_ADDRESS}")
        
    try:
        account_address = w3.eth.account.from_key(PRIVATE_KEY).address
    except Exception as e:
        raise ValueError(f"Invalid WALLET_PRIVATE_KEY: {str(e)}")
        
    try:
        contract = w3.eth.contract(address=checksum_address, abi=CONTRACT_ABI)
    except Exception as e:
        raise ValueError(f"Failed to initialize contract: {str(e)}")
        
    return contract, account_address


@api_view(['POST'])
def issue_credential(request):
    """
    Takes student data (eventually from Google Sheets), hashes it, 
    and anchors the hash to the Sepolia Testnet.
    """
    try:
        # Resolve contract and account configuration
        try:
            contract, account_address = get_contract_and_account()
        except ValueError as val_err:
            return Response({"error": str(val_err)}, status=status.HTTP_400_BAD_REQUEST)

        # Extract data from the incoming request payload
        student_name = request.data.get("name")
        course = request.data.get("course")
        grad_date = request.data.get("graduation_date")

        if not all([student_name, course, grad_date]):
             return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Create a unified string and hash it (SHA-256)
        raw_string = f"{student_name}-{course}-{grad_date}"
        document_hash = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
        
        # Convert hex string to bytes32 format for Solidity
        bytes32_hash = Web3.to_bytes(hexstr=document_hash)

        # Build the Web3 Transaction
        nonce = w3.eth.get_transaction_count(account_address)
        txn = contract.functions.issueCredential(bytes32_hash).build_transaction({
            'chainId': 11155111, # Sepolia Chain ID
           'gas': 300000,                                 # Lowered ceiling
            'maxFeePerGas': w3.to_wei('30', 'gwei'),       # Balanced network fee
            'maxPriorityFeePerGas': w3.to_wei('2', 'gwei'), # <--- Bumped to 5
            'nonce': nonce,
        })

        # Sign and Send the Transaction
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # Return the success payload to the user
        return Response({
            "status": "success",
            "message": "Credential successfully anchored to blockchain.",
            "student": student_name,
            "document_hash": document_hash,
            "transaction_hash": tx_hash.hex(),
            "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hash.hex()}"
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def verify_credential(request, document_hash):
    """
    Takes a hash from the URL and checks the Sepolia contract
    to see if it is a valid, officially issued credential.
    """
    try:
        # Resolve contract configuration
        try:
            contract, _ = get_contract_and_account()
        except ValueError as val_err:
            return Response({"error": str(val_err)}, status=status.HTTP_400_BAD_REQUEST)

        # Convert the incoming hex string back to bytes32 format
        bytes32_hash = Web3.to_bytes(hexstr=document_hash)

        # Call the verify function on the smart contract (Read-only)
        result = contract.functions.verifyCredential(bytes32_hash).call()
        
        # The contract returns a tuple: (isValid, timestamp)
        is_valid = result[0]
        timestamp = result[1]

        if is_valid:
            return Response({
                "status": "success",
                "message": "Credential is valid.",
                "document_hash": document_hash,
                "anchored_timestamp": timestamp
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "failed",
                "message": "Credential not found or has been revoked.",
                "document_hash": document_hash
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
