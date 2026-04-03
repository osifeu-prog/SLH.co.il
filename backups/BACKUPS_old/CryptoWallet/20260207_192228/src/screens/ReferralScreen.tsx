import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  SafeAreaView,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import QRCode from "react-native-qrcode-svg";
import * as Clipboard from "expo-clipboard";
import { ReferralService } from "../services/referralService";
import { WalletService } from "../services/walletService";
import { APP_CONFIG } from "../utils/constants";

const ReferralScreen = () => {
  const navigation = useNavigation();
  const [referralData, setReferralData] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [stats, setStats] = useState({
    totalReferred: 0,
    totalMeahEarned: 0,
    pendingRewards: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const wallet = await WalletService.getWallet();
      if (!wallet) {
        Alert.alert("שגיאה", "יש לחבר ארנק תחילה");
        navigation.goBack();
        return;
      }

      const referralData = await ReferralService.getReferralData();
      const history = await ReferralService.getReferralHistory();
      const stats = await ReferralService.getStats();

      setReferralData(referralData);
      setHistory(history);
      setStats(stats);
    } catch (error) {
      console.error("Error loading referral data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const copyReferralCode = async () => {
    if (referralData?.referralCode) {
      await Clipboard.setStringAsync(referralData.referralCode);
      Alert.alert("✅", "קוד ההפניה הועתק!");
    }
  };

  const copyReferralLink = async () => {
    if (referralData?.referralCode) {
      const link = ReferralService.generateReferralLink(referralData.referralCode);
      await Clipboard.setStringAsync(link);
      Alert.alert("✅", "לינק ההפניה הועתק!");
    }
  };

  const shareReferral = async () => {
    if (referralData?.referralCode) {
      const link = ReferralService.generateReferralLink(referralData.referralCode);
      const message = `הצטרף ל-Selha Wallet וקבל 100 MEAH בחינם! ${link}`;
      
      try {
        await Clipboard.setStringAsync(message);
        Alert.alert("✅", "הודעה הועתקה ללוח - שתף עם חברים!");
      } catch (error) {
        console.error("Error sharing:", error);
      }
    }
  };

  const claimRewards = async () => {
    if (stats.pendingRewards > 0) {
      const rewards = await ReferralService.claimRewards();
      Alert.alert("🎉", `קבלת ${rewards} MEAH בהצלחה!`);
      await loadData();
    } else {
      Alert.alert("⚠️", "אין תגמולים להעברה כרגע");
    }
  };

  const addTestReferral = async () => {
    const testAddress = "0xTest" + Date.now();
    await ReferralService.addReferredUser(testAddress);
    await loadData();
    Alert.alert("✅", "הפניה לדמו נוספה בהצלחה!");
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4A90E2" />
        <Text style={styles.loadingText}>טוען נתוני הפניות...</Text>
      </View>
    );
  }

  if (!referralData) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>מערכת הפניות</Text>
        <Text style={styles.message}>
          יש לחבר ארנק כדי להשתמש במערכת ההפניות
        </Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.navigate("Wallet" as never)}
        >
          <Text style={styles.buttonText}>חבר ארנק</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.title}>מערכת הפניות</Text>
          <Text style={styles.subtitle}>
            הזמן חברים וקבל פרסים ב-MEAH
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>קוד ההפניה שלך</Text>
          <TouchableOpacity onPress={copyReferralCode}>
            <Text style={styles.referralCode}>
              {referralData.referralCode}
            </Text>
          </TouchableOpacity>
          
          <Text style={styles.note}>
            שתף קוד זה עם חברים
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>QR Code להזמנה</Text>
          <View style={styles.qrContainer}>
            <QRCode
              value={ReferralService.generateReferralLink(referralData.referralCode)}
              size={200}
            />
          </View>
          <Text style={styles.note}>
            סרוק כדי להצטרף
          </Text>
        </View>

        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{stats.totalReferred}</Text>
            <Text style={styles.statLabel}>מוזמנים</Text>
          </View>
          
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{stats.totalMeahEarned}</Text>
            <Text style={styles.statLabel}>MEAH שנצברו</Text>
          </View>
          
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{stats.pendingRewards}</Text>
            <Text style={styles.statLabel}>בהמתנה</Text>
          </View>
        </View>

        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.actionButton} onPress={copyReferralLink}>
            <Text style={styles.actionIcon}>📋</Text>
            <Text style={styles.actionText}>העתק לינק</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.actionButton} onPress={shareReferral}>
            <Text style={styles.actionIcon}>📤</Text>
            <Text style={styles.actionText}>שתף</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.actionButton} onPress={claimRewards}>
            <Text style={styles.actionIcon}>💰</Text>
            <Text style={styles.actionText}>קבל פרסים</Text>
          </TouchableOpacity>
        </View>

        {history.length > 0 && (
          <View style={styles.historyContainer}>
            <Text style={styles.historyTitle}>היסטוריית הפניות</Text>
            {history.slice(0, 5).map((item, index) => (
              <View key={index} style={styles.historyItem}>
                <Text style={styles.historyDate}>
                  {new Date(item.date).toLocaleDateString("he-IL")}
                </Text>
                <Text style={styles.historyAddress}>
                  {item.referredAddress.substring(0, 8)}...
                </Text>
                <Text style={styles.historyReward}>
                  +{item.meahReward} MEAH
                </Text>
                <Text style={[
                  styles.historyStatus,
                  item.status === "completed" ? styles.statusCompleted : styles.statusPending,
                ]}>
                  {item.status === "completed" ? "הושלם" : "בהמתנה"}
                </Text>
              </View>
            ))}
          </View>
        )}

        {/* Test button - remove in production */}
        <TouchableOpacity
          style={[styles.button, styles.testButton]}
          onPress={addTestReferral}
        >
          <Text style={styles.buttonText}>+ הוסף הפניה (לדמו)</Text>
        </TouchableOpacity>

        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>איך זה עובד?</Text>
          <Text style={styles.infoText}>1. שתף את קוד ההפניה שלך עם חברים</Text>
          <Text style={styles.infoText}>2. חברים מצטרפים דרך הקוד/לינק</Text>
          <Text style={styles.infoText}>3. קבל 100 MEAH על כל חבר שהצטרף</Text>
          <Text style={styles.infoText}>4. משוך את הפרסים שלך לארנק</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8f9fa",
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#fff",
  },
  loadingText: {
    marginTop: 20,
    fontSize: 16,
    color: "#666",
  },
  header: {
    padding: 20,
    alignItems: "center",
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e9ecef",
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    color: "#333",
  },
  subtitle: {
    fontSize: 16,
    color: "#666",
    marginTop: 5,
  },
  message: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    margin: 20,
    lineHeight: 24,
  },
  card: {
    backgroundColor: "#fff",
    margin: 15,
    padding: 20,
    borderRadius: 15,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10,
    color: "#333",
  },
  referralCode: {
    fontSize: 28,
    fontWeight: "bold",
    color: "#4A90E2",
    backgroundColor: "#f0f7ff",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
    marginBottom: 10,
  },
  note: {
    fontSize: 14,
    color: "#666",
  },
  qrContainer: {
    padding: 20,
    backgroundColor: "#fff",
    borderRadius: 10,
    marginVertical: 15,
  },
  statsContainer: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginHorizontal: 15,
    marginVertical: 10,
  },
  statCard: {
    backgroundColor: "#fff",
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    flex: 1,
    marginHorizontal: 5,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
  },
  statLabel: {
    fontSize: 12,
    color: "#666",
    marginTop: 5,
  },
  actionsContainer: {
    flexDirection: "row",
    justifyContent: "space-around",
    margin: 15,
    padding: 15,
    backgroundColor: "#fff",
    borderRadius: 15,
  },
  actionButton: {
    alignItems: "center",
    flex: 1,
  },
  actionIcon: {
    fontSize: 24,
    marginBottom: 5,
  },
  actionText: {
    fontSize: 12,
    color: "#333",
  },
  historyContainer: {
    backgroundColor: "#fff",
    margin: 15,
    padding: 20,
    borderRadius: 15,
  },
  historyTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#333",
  },
  historyItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f3f5",
  },
  historyDate: {
    fontSize: 12,
    color: "#666",
  },
  historyAddress: {
    fontSize: 12,
    color: "#666",
    fontFamily: "monospace",
  },
  historyReward: {
    fontSize: 14,
    color: "#34C759",
    fontWeight: "600",
  },
  historyStatus: {
    fontSize: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  statusCompleted: {
    backgroundColor: "#d4edda",
    color: "#155724",
  },
  statusPending: {
    backgroundColor: "#fff3cd",
    color: "#856404",
  },
  button: {
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    marginHorizontal: 15,
    marginVertical: 5,
  },
  testButton: {
    backgroundColor: "#8B4513",
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  infoBox: {
    backgroundColor: "#e7f3ff",
    margin: 15,
    padding: 20,
    borderRadius: 15,
    borderWidth: 1,
    borderColor: "#b8daff",
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#004085",
  },
  infoText: {
    fontSize: 14,
    color: "#004085",
    marginBottom: 8,
    lineHeight: 20,
  },
});

export default ReferralScreen;
