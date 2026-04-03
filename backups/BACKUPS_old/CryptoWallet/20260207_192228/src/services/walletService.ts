import AsyncStorage from "@react-native-async-storage/async-storage";
import { ethers } from "ethers";
import { SLH_CONTRACT_ADDRESS, BSC_RPC_URL } from "../utils/constants";

export interface WalletData {
  address: string;
  privateKey?: string;
  mnemonic?: string;
  isImported: boolean;
  isSLHWallet: boolean;
  balance: string;
  slhBalance: string;
  createdAt: string;
  lastSync: string;
}

export class WalletService {
  private static readonly STORAGE_KEY = "selha_wallet_data";

  // שמירת ארנק
  static async saveWallet(walletData: WalletData): Promise<void> {
    try {
      const dataToSave = {
        ...walletData,
        lastSync: new Date().toISOString(),
      };
      
      await AsyncStorage.setItem(
        this.STORAGE_KEY, 
        JSON.stringify(dataToSave)
      );
      
      console.log("✅ Wallet saved successfully");
    } catch (error) {
      console.error("❌ Error saving wallet:", error);
      throw error;
    }
  }

  // קבלת ארנק
  static async getWallet(): Promise<WalletData | null> {
    try {
      const data = await AsyncStorage.getItem(this.STORAGE_KEY);
      if (!data) return null;
      
      return JSON.parse(data);
    } catch (error) {
      console.error("❌ Error getting wallet:", error);
      return null;
    }
  }

  // בדיקת יתרת SLH
  static async getSLHBalance(address: string): Promise<string> {
    try {
      const provider = new ethers.JsonRpcProvider(BSC_RPC_URL);
      const contractABI = [
        "function balanceOf(address owner) view returns (uint256)",
        "function decimals() view returns (uint8)"
      ];
      
      const contract = new ethers.Contract(
        SLH_CONTRACT_ADDRESS,
        contractABI,
        provider
      );
      
      const balance = await contract.balanceOf(address);
      const decimals = await contract.decimals();
      
      const formattedBalance = ethers.formatUnits(balance, decimals);
      return formattedBalance;
      
    } catch (error) {
      console.error("❌ Error fetching SLH balance:", error);
      return "0.0";
    }
  }

  // בדיקת יתרת BNB
  static async getBNBBalance(address: string): Promise<string> {
    try {
      const provider = new ethers.JsonRpcProvider(BSC_RPC_URL);
      const balance = await provider.getBalance(address);
      return ethers.formatEther(balance);
    } catch (error) {
      console.error("❌ Error fetching BNB balance:", error);
      return "0.0";
    }
  }

  // יצירת ארנק חדש
  static async createNewWallet(): Promise<WalletData> {
    try {
      const wallet = ethers.Wallet.createRandom();
      
      const walletData: WalletData = {
        address: wallet.address,
        privateKey: wallet.privateKey,
        mnemonic: wallet.mnemonic?.phrase,
        isImported: false,
        isSLHWallet: false,
        balance: "0.0",
        slhBalance: "0.0",
        createdAt: new Date().toISOString(),
        lastSync: new Date().toISOString(),
      };
      
      await this.saveWallet(walletData);
      return walletData;
      
    } catch (error) {
      console.error("❌ Error creating wallet:", error);
      throw error;
    }
  }

  // ייבוא ארנק מקיים
  static async importWallet(privateKeyOrMnemonic: string): Promise<WalletData> {
    try {
      let wallet: ethers.Wallet;
      
      if (privateKeyOrMnemonic.includes(" ")) {
        // Seed phrase
        wallet = ethers.Wallet.fromPhrase(privateKeyOrMnemonic);
      } else {
        // Private key
        wallet = new ethers.Wallet(privateKeyOrMnemonic);
      }
      
      const slhBalance = await this.getSLHBalance(wallet.address);
      const bnbBalance = await this.getBNBBalance(wallet.address);
      
      const walletData: WalletData = {
        address: wallet.address,
        privateKey: wallet.privateKey,
        mnemonic: wallet.mnemonic?.phrase,
        isImported: true,
        isSLHWallet: false,
        balance: bnbBalance,
        slhBalance: slhBalance,
        createdAt: new Date().toISOString(),
        lastSync: new Date().toISOString(),
      };
      
      await this.saveWallet(walletData);
      return walletData;
      
    } catch (error) {
      console.error("❌ Error importing wallet:", error);
      throw error;
    }
  }

  // עדכון יתרות
  static async updateBalances(): Promise<void> {
    try {
      const wallet = await this.getWallet();
      if (!wallet) return;
      
      const slhBalance = await this.getSLHBalance(wallet.address);
      const bnbBalance = await this.getBNBBalance(wallet.address);
      
      wallet.balance = bnbBalance;
      wallet.slhBalance = slhBalance;
      wallet.lastSync = new Date().toISOString();
      
      await this.saveWallet(wallet);
      
    } catch (error) {
      console.error("❌ Error updating balances:", error);
    }
  }

  // בדיקת תקינות כתובת
  static isValidAddress(address: string): boolean {
    return ethers.isAddress(address);
  }

  // מחיקת ארנק
  static async deleteWallet(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.STORAGE_KEY);
      console.log("✅ Wallet deleted successfully");
    } catch (error) {
      console.error("❌ Error deleting wallet:", error);
      throw error;
    }
  }
}
  static async importWallet(privateKey: string, isRecovery: boolean = false): Promise<any> {
    // בדוק אם כבר יש ארנק שמור
    const existingWallet = await this.getWallet();
    
    if (existingWallet && !isRecovery) {
      throw new Error("ייבוא ארנק זמין רק לשחזור. כבר יש ארנק מחובר.");
    }

    // המשך בקוד הרגיל...
    // [הקוד הקיים שלך]
  }
