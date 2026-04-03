import AsyncStorage from "@react-native-async-storage/async-storage";
import { ethers } from "ethers";
import {
  NETWORKS,
  CONTRACTS,
  CONVERSION_RATES,
} from "../utils/constants";

// ממשקים
interface Transaction {
  hash: string;
  from: string;
  to: string;
  value: string;
  timestamp: number;
  status: "pending" | "completed" | "failed";
}

interface StakeInfo {
  amount: number;
  startTime: number;
  rewardRate: number;
  earned: number;
  duration: number; // בימים
}

// שירות להמרת מטבעות
class ConversionService {
  private static instance: ConversionService;
  private currentNetwork = NETWORKS.BSC_TESTNET; // ברירת מחדל לטסט נט

  static getInstance(): ConversionService {
    if (!ConversionService.instance) {
      ConversionService.instance = new ConversionService();
    }
    return ConversionService.instance;
  }

  // החלף רשת
  async switchNetwork(networkType: "mainnet" | "testnet") {
    this.currentNetwork = 
      networkType === "mainnet" ? NETWORKS.BSC_MAINNET : NETWORKS.BSC_TESTNET;
    
    await AsyncStorage.setItem(
      "selected_network",
      networkType
    );
    
    return this.currentNetwork;
  }

  // קבל רשת נוכחית
  async getCurrentNetwork() {
    const saved = await AsyncStorage.getItem("selected_network");
    if (saved === "mainnet") {
      this.currentNetwork = NETWORKS.BSC_MAINNET;
    }
    return this.currentNetwork;
  }

  // המרת SLH ל-MEAH
  async convertSLHtoMEAH(slhAmount: number, walletAddress: string): Promise<Transaction> {
    try {
      // כאן יתווסף בעתיד החיבור לחוזה החכם
      // כרגע - סימולציה
      
      const meahAmount = slhAmount * CONVERSION_RATES.SLH_TO_MEAH;
      
      const tx: Transaction = {
        hash: `0x${Math.random().toString(16).substring(2)}`,
        from: walletAddress,
        to: CONTRACTS.MEAH_TOKEN,
        value: meahAmount.toString(),
        timestamp: Date.now(),
        status: "completed",
      };

      // שמור היסטוריה
      await this.saveTransaction(tx);
      
      // עדכן יתרות
      await this.updateBalances(walletAddress, slhAmount, meahAmount);

      return tx;
    } catch (error) {
      console.error("Conversion error:", error);
      throw new Error("ההמרה נכשלה");
    }
  }

  // סטייקינג של SLH
  async stakeSLH(amount: number, duration: number = 30): Promise<StakeInfo> {
    try {
      const stakeInfo: StakeInfo = {
        amount,
        startTime: Date.now(),
        rewardRate: CONVERSION_RATES.STAKE_REWARD_RATE,
        earned: 0,
        duration,
      };

      // שמור סטייקינג
      await AsyncStorage.setItem(
        "staking_info",
        JSON.stringify(stakeInfo)
      );

      // התחל טיימר לתגמולים
      this.startRewardTimer(stakeInfo);

      return stakeInfo;
    } catch (error) {
      console.error("Staking error:", error);
      throw new Error("סטייקינג נכשל");
    }
  }

  // משיכת תגמולי סטייקינג
  async claimStakingRewards(): Promise<number> {
    try {
      const stakeInfoStr = await AsyncStorage.getItem("staking_info");
      if (!stakeInfoStr) throw new Error("אין סטייקינג פעיל");

      const stakeInfo: StakeInfo = JSON.parse(stakeInfoStr);
      
      // חשב תגמולים
      const daysStaked = (Date.now() - stakeInfo.startTime) / (1000 * 60 * 60 * 24);
      const rewards = stakeInfo.amount * stakeInfo.rewardRate * (daysStaked / 365);

      // אפס טיימר
      stakeInfo.startTime = Date.now();
      stakeInfo.earned += rewards;

      await AsyncStorage.setItem(
        "staking_info",
        JSON.stringify(stakeInfo)
      );

      return rewards;
    } catch (error) {
      console.error("Claim error:", error);
      throw new Error("משיכת תגמולים נכשלה");
    }
  }

  // קבל יתרות
  async getBalances(walletAddress: string): Promise<{
    slh: number;
    meah: number;
    bnb: number;
    staked: number;
    pendingRewards: number;
  }> {
    try {
      // כאן יתווסף קריאה לבלוקצ'יין
      // כרגע - נתוני דמו
      return {
        slh: 1000,
        meah: 444000,
        bnb: 0.5,
        staked: 500,
        pendingRewards: 25.6,
      };
    } catch (error) {
      console.error("Balance error:", error);
      return {
        slh: 0,
        meah: 0,
        bnb: 0,
        staked: 0,
        pendingRewards: 0,
      };
    }
  }

  // פונקציות עזר פרטיות
  private async saveTransaction(tx: Transaction): Promise<void> {
    try {
      const historyStr = await AsyncStorage.getItem("transaction_history");
      const history: Transaction[] = historyStr ? JSON.parse(historyStr) : [];
      
      history.push(tx);
      
      await AsyncStorage.setItem(
        "transaction_history",
        JSON.stringify(history.slice(-50)) // שמור 50 הטרנזקציות האחרונות
      );
    } catch (error) {
      console.error("Save transaction error:", error);
    }
  }

  private async updateBalances(
    walletAddress: string,
    slhChange: number,
    meahChange: number
  ): Promise<void> {
    try {
      const balances = await this.getBalances(walletAddress);
      
      await AsyncStorage.setItem(
        "cached_balances",
        JSON.stringify({
          ...balances,
          slh: balances.slh - slhChange,
          meah: balances.meah + meahChange,
          lastUpdated: Date.now(),
        })
      );
    } catch (error) {
      console.error("Update balances error:", error);
    }
  }

  private startRewardTimer(stakeInfo: StakeInfo): void {
    // טיימר לדמו - בעתיד יחובר לאירועי בלוקצ'יין
    console.log("Reward timer started for stake:", stakeInfo);
  }
}

// יצירת מופע יחיד
export const conversionService = ConversionService.getInstance();

// שירות סטייקינג מתקדם
export class AdvancedStakingService {
  private static instance: AdvancedStakingService;

  static getInstance(): AdvancedStakingService {
    if (!AdvancedStakingService.instance) {
      AdvancedStakingService.instance = new AdvancedStakingService();
    }
    return AdvancedStakingService.instance;
  }

  async getStakingPlans() {
    return [
      {
        id: "basic",
        name: "תוכנית בסיסית",
        duration: 30,
        apy: 15,
        minAmount: 100,
        description: "סטייקינג בסיסי ל-30 יום",
      },
      {
        id: "premium",
        name: "תוכנית פרימיום",
        duration: 90,
        apy: 25,
        minAmount: 500,
        description: "סטייקינג מתקדם ל-90 יום",
      },
      {
        id: "vip",
        name: "תוכנית VIP",
        duration: 180,
        apy: 40,
        minAmount: 1000,
        description: "סטייקינג VIP ל-180 יום",
      },
    ];
  }

  async calculateRewards(amount: number, duration: number, apy: number) {
    const dailyRate = apy / 365 / 100;
    const totalRewards = amount * dailyRate * duration;
    return totalRewards;
  }
}

export const stakingService = AdvancedStakingService.getInstance();
