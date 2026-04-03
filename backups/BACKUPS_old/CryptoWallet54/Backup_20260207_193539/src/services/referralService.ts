import AsyncStorage from "@react-native-async-storage/async-storage";
import { REFERRAL_CONFIG } from "../utils/constants";

export interface ReferralData {
  referralCode: string;
  referredUsers: string[];
  totalMeahEarned: number;
  pendingRewards: number;
  lastRewardDate: string | null;
}

export interface ReferralHistory {
  date: string;
  referredAddress: string;
  meahReward: number;
  status: "pending" | "completed" | "failed";
}

export class ReferralService {
  private static readonly STORAGE_KEY = "selha_referral_data";
  private static readonly HISTORY_KEY = "selha_referral_history";

  // יצירת קוד הפניה ייחודי
  static generateReferralCode(address: string): string {
    const prefix = "SLH";
    const shortAddress = address.substring(2, 8).toUpperCase();
    const randomNum = Math.floor(1000 + Math.random() * 9000);
    return `${prefix}${shortAddress}${randomNum}`;
  }

  // יצירת לינק הפניה
  static generateReferralLink(code: string): string {
    return `${REFERRAL_CONFIG.BASE_URL}/${code}`;
  }

  // שמירת נתוני הפניות
  static async saveReferralData(data: ReferralData): Promise<void> {
    try {
      await AsyncStorage.setItem(
        this.STORAGE_KEY,
        JSON.stringify(data)
      );
    } catch (error) {
      console.error("❌ Error saving referral data:", error);
      throw error;
    }
  }

  // קבלת נתוני הפניות
  static async getReferralData(): Promise<ReferralData | null> {
    try {
      const data = await AsyncStorage.getItem(this.STORAGE_KEY);
      if (!data) return null;
      return JSON.parse(data);
    } catch (error) {
      console.error("❌ Error getting referral data:", error);
      return null;
    }
  }

  // התחלת מערכת הפניות
  static async initializeReferralSystem(address: string): Promise<ReferralData> {
    const referralCode = this.generateReferralCode(address);
    
    const referralData: ReferralData = {
      referralCode,
      referredUsers: [],
      totalMeahEarned: 0,
      pendingRewards: 0,
      lastRewardDate: null,
    };
    
    await this.saveReferralData(referralData);
    return referralData;
  }

  // הוספת משתמש מופנה
  static async addReferredUser(userAddress: string): Promise<void> {
    try {
      const data = await this.getReferralData();
      if (!data) return;
      
      if (!data.referredUsers.includes(userAddress)) {
        data.referredUsers.push(userAddress);
        data.pendingRewards += REFERRAL_CONFIG.REWARD_AMOUNT;
        data.lastRewardDate = new Date().toISOString();
        
        await this.saveReferralData(data);
        
        // שמור היסטוריה
        await this.addToHistory({
          date: new Date().toISOString(),
          referredAddress: userAddress,
          meahReward: REFERRAL_CONFIG.REWARD_AMOUNT,
          status: "pending",
        });
      }
    } catch (error) {
      console.error("❌ Error adding referred user:", error);
    }
  }

  // שמירת היסטוריית הפניות
  static async addToHistory(history: ReferralHistory): Promise<void> {
    try {
      const existing = await AsyncStorage.getItem(this.HISTORY_KEY);
      let historyArray: ReferralHistory[] = [];
      
      if (existing) {
        historyArray = JSON.parse(existing);
      }
      
      historyArray.push(history);
      
      await AsyncStorage.setItem(
        this.HISTORY_KEY,
        JSON.stringify(historyArray)
      );
    } catch (error) {
      console.error("❌ Error saving referral history:", error);
    }
  }

  // קבלת היסטוריית הפניות
  static async getReferralHistory(): Promise<ReferralHistory[]> {
    try {
      const data = await AsyncStorage.getItem(this.HISTORY_KEY);
      if (!data) return [];
      return JSON.parse(data);
    } catch (error) {
      console.error("❌ Error getting referral history:", error);
      return [];
    }
  }

  // קבלת תגמולים
  static async claimRewards(): Promise<number> {
    try {
      const data = await this.getReferralData();
      if (!data || data.pendingRewards === 0) return 0;
      
      const rewards = data.pendingRewards;
      data.totalMeahEarned += rewards;
      data.pendingRewards = 0;
      
      await this.saveReferralData(data);
      return rewards;
    } catch (error) {
      console.error("❌ Error claiming rewards:", error);
      return 0;
    }
  }

  // קבלת סטטיסטיקות
  static async getStats() {
    const data = await this.getReferralData();
    const history = await this.getReferralHistory();
    
    const pending = history.filter(h => h.status === "pending").length;
    const completed = history.filter(h => h.status === "completed").length;
    
    return {
      totalReferred: data?.referredUsers.length || 0,
      totalMeahEarned: data?.totalMeahEarned || 0,
      pendingRewards: data?.pendingRewards || 0,
      pendingCount: pending,
      completedCount: completed,
    };
  }
}
