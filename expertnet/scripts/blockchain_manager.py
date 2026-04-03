import json
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('vault/.env')

class BlockchainManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        with open('abi/contract_abi.json', 'r') as f:
            self.abi = json.load(f)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.abi)

    def get_token_info(self):
        try:
            return {
                "name": self.contract.functions.name().call(),
                "symbol": self.contract.functions.symbol().call(),
                "total_supply": self.contract.functions.totalSupply().call() / (10**18)
            }
        except:
            return None

    def get_balance(self, wallet_address):
        try:
            balance = self.contract.functions.balanceOf(wallet_address).call()
            return balance / (10**18)
        except:
            return 0
