import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  TextInput,
  SafeAreaView,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { conversionService, stakingService } from "../services/conversionService";
import { WalletService } from "../services/walletService";
import { CONVERSION_RATES } from "../utils/constants";

const ConvertStakeScreen = () => {
  const navigation = useNavigation();
  const [activeTab, setActiveTab] = useState<"convert" | "stake" | "history">("convert");
  const [isLoading, setIsLoading] = useState(false);
  const [balances, setBalances] = useState<any>(null);
  const [slhAmount, setSlhAmount] = useState("");
  const [selectedPlan, setSelectedPlan] = useState<any>(null);
  const [stakingInfo, setStakingInfo] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);

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

      const balancesData = await conversionService.getBalances(wallet.address);
      setBalances(balancesData);

      // טען תוכניות סטייקינג
      const plans = await stakingService.getStakingPlans();
      if (plans.length > 0) {
        setSelectedPlan(plans[0]);
      }

      // טען היסטוריה
      const historyStr = await AsyncStorage.getItem("transaction_history");
      if (historyStr) {
        setTransactions(JSON.parse(historyStr).reverse());
      }
    } catch (error) {
      console.error("Load data error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConvert = async () => {
    if (!slhAmount || parseFloat(slhAmount) <= 0) {
      Alert.alert("שגיאה", "הזן כמות חוקית");
      return;
    }

    if (parseFloat(slhAmount) > balances.slh) {
      Alert.alert("שגיאה", "אין מספיק SLH בארנק");
      return;
    }

    setIsLoading(true);
    try {
      const wallet = await WalletService.getWallet();
      const tx = await conversionService.convertSLHtoMEAH(
        parseFloat(slhAmount),
        wallet.address
      );

      Alert.alert(
        "הצלחה! 🎉",
        `המרת ${slhAmount} SLH ל-${parseFloat(slhAmount) * CONVERSION_RATES.SLH_TO_MEAH} MEAH`,
        [
          {
            text: "מעולה",
            onPress: () => {
              setSlhAmount("");
              loadData();
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert("שגיאה", "ההמרה נכשלה");
    } finally {
      setIsLoading(false);
    }
  };

  const handleStake = async () => {
    if (!selectedPlan) {
      Alert.alert("שגיאה", "בחר תוכנית סטייקינג");
      return;
    }

    if (selectedPlan.minAmount > balances.slh) {
      Alert.alert("שגיאה", `דרוש מינימום ${selectedPlan.minAmount} SLH`);
      return;
    }

    setIsLoading(true);
    try {
      const stakeInfo = await conversionService.stakeSLH(
        selectedPlan.minAmount,
        selectedPlan.duration
      );

      setStakingInfo(stakeInfo);

      Alert.alert(
        "סטייקינג הופעל! 🔒",
        `הנחת ${selectedPlan.minAmount} SLH ל-${selectedPlan.duration} ימים\nתשואה צפויה: ${selectedPlan.apy}% לשנה`,
        [
          {
            text: "מצוין",
            onPress: loadData,
          },
        ]
      );
    } catch (error) {
      Alert.alert("שגיאה", "הפעלת סטייקינג נכשלה");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClaimRewards = async () => {
    setIsLoading(true);
    try {
      const rewards = await conversionService.claimStakingRewards();
      
      Alert.alert(
        "תגמולים נמשכו! 💰",
        `משכת ${rewards.toFixed(2)} MEAH מתגמולי סטייקינג`,
        [
          {
            text: "יופי",
            onPress: loadData,
          },
        ]
      );
    } catch (error) {
      Alert.alert("שגיאה", "משיכת תגמולים נכשלה");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !balances) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4A90E2" />
        <Text style={styles.loadingText}>טוען נתונים...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.title}>המרה וסטייקינג</Text>
          <Text style={styles.subtitle}>
            המר SLH ל-MEAH והנח לגדול
          </Text>
        </View>

        <View style={styles.balanceCard}>
          <Text style={styles.balanceTitle}>יתרות נוכחיות</Text>
          <View style={styles.balanceRow}>
            <Text style={styles.balanceLabel}>SLH:</Text>
            <Text style={styles.balanceValue}>{balances?.slh || 0}</Text>
          </View>
          <View style={styles.balanceRow}>
            <Text style={styles.balanceLabel}>MEAH:</Text>
            <Text style={styles.balanceValue}>{balances?.meah || 0}</Text>
          </View>
          <View style={styles.balanceRow}>
            <Text style={styles.balanceLabel}>מונח בסטייקינג:</Text>
            <Text style={styles.balanceValue}>{balances?.staked || 0} SLH</Text>
          </View>
          <View style={styles.balanceRow}>
            <Text style={styles.balanceLabel}>תגמולים ממתינים:</Text>
            <Text style={[styles.balanceValue, styles.rewardText]}>
              {balances?.pendingRewards || 0} MEAH
            </Text>
          </View>
        </View>

        <View style={styles.tabsContainer}>
          <TouchableOpacity
            style={[styles.tab, activeTab === "convert" && styles.activeTab]}
            onPress={() => setActiveTab("convert")}
          >
            <Text style={[styles.tabText, activeTab === "convert" && styles.activeTabText]}>
              המרה
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === "stake" && styles.activeTab]}
            onPress={() => setActiveTab("stake")}
          >
            <Text style={[styles.tabText, activeTab === "stake" && styles.activeTabText]}>
              סטייקינג
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, activeTab === "history" && styles.activeTab]}
            onPress={() => setActiveTab("history")}
          >
            <Text style={[styles.tabText, activeTab === "history" && styles.activeTabText]}>
              היסטוריה
            </Text>
          </TouchableOpacity>
        </View>

        {activeTab === "convert" && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>המר SLH ל-MEAH</Text>
            <Text style={styles.rateInfo}>
              שער המרה: 1 SLH = {CONVERSION_RATES.SLH_TO_MEAH} MEAH
            </Text>

            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                placeholder="כמות SLH להמרה"
                keyboardType="numeric"
                value={slhAmount}
                onChangeText={setSlhAmount}
              />
              <TouchableOpacity
                style={styles.maxButton}
                onPress={() => setSlhAmount(balances?.slh?.toString() || "0")}
              >
                <Text style={styles.maxButtonText}>MAX</Text>
              </TouchableOpacity>
            </View>

            {slhAmount && (
              <View style={styles.previewCard}>
                <Text style={styles.previewText}>
                  תקבל: {(parseFloat(slhAmount) * CONVERSION_RATES.SLH_TO_MEAH).toLocaleString()} MEAH
                </Text>
              </View>
            )}

            <TouchableOpacity
              style={[styles.actionButton, styles.primaryButton]}
              onPress={handleConvert}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.actionButtonText}>המר עכשיו</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        {activeTab === "stake" && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>תוכניות סטייקינג</Text>

            <View style={styles.plansContainer}>
              {[
                {
                  id: "basic",
                  name: "בסיסית",
                  duration: 30,
                  apy: 15,
                  minAmount: 100,
                },
                {
                  id: "premium",
                  name: "פרימיום",
                  duration: 90,
                  apy: 25,
                  minAmount: 500,
                },
                {
                  id: "vip",
                  name: "VIP",
                  duration: 180,
                  apy: 40,
                  minAmount: 1000,
                },
              ].map((plan) => (
                <TouchableOpacity
                  key={plan.id}
                  style={[
                    styles.planCard,
                    selectedPlan?.id === plan.id && styles.selectedPlan,
                  ]}
                  onPress={() => setSelectedPlan(plan)}
                >
                  <Text style={styles.planName}>{plan.name}</Text>
                  <Text style={styles.planApy}>{plan.apy}% APY</Text>
                  <Text style={styles.planDuration}>{plan.duration} ימים</Text>
                  <Text style={styles.planMin}>מינימום: {plan.minAmount} SLH</Text>
                </TouchableOpacity>
              ))}
            </View>

            {selectedPlan && (
              <View style={styles.calculationCard}>
                <Text style={styles.calculationTitle}>תשואה צפויה:</Text>
                <Text style={styles.calculationResult}>
                  {selectedPlan.minAmount} SLH × {selectedPlan.apy}% × {selectedPlan.duration} ימים
                </Text>
                <Text style={styles.calculationResult}>
                  = {((selectedPlan.minAmount * selectedPlan.apy * selectedPlan.duration) / 36500).toFixed(2)} MEAH
                </Text>
              </View>
            )}

            <TouchableOpacity
              style={[styles.actionButton, styles.successButton]}
              onPress={handleStake}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.actionButtonText}>הפעל סטייקינג</Text>
              )}
            </TouchableOpacity>

            {stakingInfo && (
              <TouchableOpacity
                style={[styles.actionButton, styles.warningButton]}
                onPress={handleClaimRewards}
                disabled={isLoading}
              >
                <Text style={styles.actionButtonText}>משוך תגמולים</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {activeTab === "history" && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>היסטוריית טרנזקציות</Text>

            {transactions.length === 0 ? (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>אין טרנזקציות עדיין</Text>
                <Text style={styles.emptyStateSubtext}>
                  ביצוע המרה או סטייקינג יצור רשומה כאן
                </Text>
              </View>
            ) : (
              transactions.map((tx, index) => (
                <View key={index} style={styles.transactionCard}>
                  <View style={styles.transactionHeader}>
                    <Text style={styles.transactionType}>
                      {tx.to === CONTRACTS.MEAH_TOKEN ? "המרה" : "סטייקינג"}
                    </Text>
                    <Text style={styles.transactionDate}>
                      {new Date(tx.timestamp).toLocaleDateString("he-IL")}
                    </Text>
                  </View>
                  <Text style={styles.transactionAmount}>
                    {tx.value} {tx.to === CONTRACTS.MEAH_TOKEN ? "MEAH" : "SLH"}
                  </Text>
                  <Text style={styles.transactionHash}>
                    {tx.hash.substring(0, 16)}...
                  </Text>
                  <View style={[
                    styles.statusBadge,
                    tx.status === "completed" ? styles.statusCompleted : 
                    tx.status === "pending" ? styles.statusPending : 
                    styles.statusFailed
                  ]}>
                    <Text style={styles.statusText}>
                      {tx.status === "completed" ? "הושלם" : 
                       tx.status === "pending" ? "בהמתנה" : "נכשל"}
                    </Text>
                  </View>
                </View>
              ))
            )}
          </View>
        )}

        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>מדוע להמיר ולהניח?</Text>
          <Text style={styles.infoText}>
            • המרת SLH ל-MEAH נותנת לך גישה למערכת התגמולים
          </Text>
          <Text style={styles.infoText}>
            • סטייקינג עוזר לאבטחת הרשת ומניב תשואה
          </Text>
          <Text style={styles.infoText}>
            • ככל שיותר מטבעות מונחים, הערך הקהילתי עולה
          </Text>
          <Text style={styles.infoText}>
            • השתתפות פעילה מזכה בפרסים נוספים
          </Text>
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
  balanceCard: {
    backgroundColor: "#fff",
    margin: 15,
    padding: 20,
    borderRadius: 15,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  balanceTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#333",
    textAlign: "center",
  },
  balanceRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  balanceLabel: {
    fontSize: 16,
    color: "#666",
  },
  balanceValue: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333",
  },
  rewardText: {
    color: "#34C759",
  },
  tabsContainer: {
    flexDirection: "row",
    marginHorizontal: 15,
    marginBottom: 10,
    backgroundColor: "#fff",
    borderRadius: 10,
    padding: 5,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: "#4A90E2",
  },
  tabText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#666",
  },
  activeTabText: {
    color: "#fff",
  },
  tabContent: {
    padding: 15,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#333",
    textAlign: "center",
  },
  rateInfo: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    marginBottom: 20,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
  },
  input: {
    flex: 1,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
  },
  maxButton: {
    backgroundColor: "#4A90E2",
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderRadius: 10,
    marginLeft: 10,
  },
  maxButtonText: {
    color: "#fff",
    fontWeight: "600",
  },
  previewCard: {
    backgroundColor: "#e7f3ff",
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
    alignItems: "center",
  },
  previewText: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#004085",
  },
  plansContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  planCard: {
    backgroundColor: "#fff",
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    flex: 1,
    marginHorizontal: 5,
    borderWidth: 2,
    borderColor: "transparent",
  },
  selectedPlan: {
    borderColor: "#4A90E2",
    backgroundColor: "#f0f7ff",
  },
  planName: {
    fontSize: 16,
    fontWeight: "bold",
    marginBottom: 5,
    color: "#333",
  },
  planApy: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#34C759",
    marginBottom: 5,
  },
  planDuration: {
    fontSize: 14,
    color: "#666",
    marginBottom: 5,
  },
  planMin: {
    fontSize: 12,
    color: "#999",
  },
  calculationCard: {
    backgroundColor: "#f8f9fa",
    padding: 20,
    borderRadius: 10,
    marginBottom: 20,
  },
  calculationTitle: {
    fontSize: 16,
    fontWeight: "bold",
    marginBottom: 10,
    color: "#333",
  },
  calculationResult: {
    fontSize: 14,
    color: "#666",
    marginBottom: 5,
  },
  actionButton: {
    padding: 16,
    borderRadius: 10,
    alignItems: "center",
    marginBottom: 10,
  },
  primaryButton: {
    backgroundColor: "#4A90E2",
  },
  successButton: {
    backgroundColor: "#34C759",
  },
  warningButton: {
    backgroundColor: "#FF9500",
  },
  actionButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  emptyState: {
    alignItems: "center",
    padding: 40,
  },
  emptyStateText: {
    fontSize: 18,
    color: "#666",
    marginBottom: 10,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: "#999",
    textAlign: "center",
  },
  transactionCard: {
    backgroundColor: "#fff",
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  transactionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  transactionType: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333",
  },
  transactionDate: {
    fontSize: 14,
    color: "#666",
  },
  transactionAmount: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#4A90E2",
    marginBottom: 5,
  },
  transactionHash: {
    fontSize: 12,
    color: "#999",
    fontFamily: "monospace",
    marginBottom: 10,
  },
  statusBadge: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
  },
  statusCompleted: {
    backgroundColor: "#d4edda",
  },
  statusPending: {
    backgroundColor: "#fff3cd",
  },
  statusFailed: {
    backgroundColor: "#f8d7da",
  },
  statusText: {
    fontSize: 12,
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

export default ConvertStakeScreen;
