import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { WalletService } from "../services/walletService";
import { ReferralService } from "../services/referralService";
import { APP_CONFIG } from "../utils/constants";

const HomeScreen = () => {
  const navigation = useNavigation();
  const [wallet, setWallet] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadWallet();
  }, []);

  const loadWallet = async () => {
    setIsLoading(true);
    try {
      const walletData = await WalletService.getWallet();
      setWallet(walletData);
      
      if (walletData) {
        // אתחל מערכת הפניות אם לא קיימת
        let referralData = await ReferralService.getReferralData();
        if (!referralData) {
          referralData = await ReferralService.initializeReferralSystem(walletData.address);
        }
      }
    } catch (error) {
      console.error("Error loading wallet:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4A90E2" />
        <Text style={styles.loadingText}>טוען...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Selha Wallet 🚀</Text>
        <Text style={styles.version}>v{APP_CONFIG.VERSION}</Text>
      </View>

      {!wallet ? (
        <View style={styles.welcomeCard}>
          <Text style={styles.welcomeTitle}>ברוך הבא!</Text>
          <Text style={styles.welcomeText}>
            חבר את הארנק שלך להתחלה מהירה
          </Text>
          
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => navigation.navigate("Wallet" as never)}
          >
            <Text style={styles.buttonText}>חבר ארנק</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.walletCard}>
          <Text style={styles.cardTitle}>ארנק SLH</Text>
          <Text style={styles.address}>
            {wallet.address.substring(0, 10)}...{wallet.address.substring(wallet.address.length - 8)}
          </Text>
          
          <View style={styles.balanceContainer}>
            <Text style={styles.balanceLabel}>יתרת SLH</Text>
            <Text style={styles.balance}>{wallet.slhBalance || "0.0"}</Text>
          </View>
          
          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={() => navigation.navigate("Referral" as never)}
          >
            <Text style={styles.buttonText}>מערכת הפניות</Text>
          </TouchableOpacity>
        </View>
      )}

      <View style={styles.features}>
        <Text style={styles.sectionTitle}>תכונות עיקריות</Text>
        
        <TouchableOpacity style={styles.featureItem}>
          <Text style={styles.featureIcon}>👛</Text>
          <Text style={styles.featureText}>ניהול ארנק SLH</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.featureItem}>
          <Text style={styles.featureIcon}>👥</Text>
          <Text style={styles.featureText}>הזמן חברים - קבל MEAH</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.featureItem}>
          <Text style={styles.featureIcon}>💾</Text>
          <Text style={styles.featureText}>גיבוי מאובטח</Text>
        </TouchableOpacity>
      </View>
      
      <Text style={styles.footer}>
        © {new Date().getFullYear()} {APP_CONFIG.COMPANY}
      </Text>
    </ScrollView>
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
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 20,
    backgroundColor: "#fff",
    borderBottomWidth: 1,
    borderBottomColor: "#e9ecef",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
  },
  version: {
    fontSize: 12,
    color: "#666",
  },
  welcomeCard: {
    backgroundColor: "#fff",
    margin: 20,
    padding: 30,
    borderRadius: 15,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  welcomeTitle: {
    fontSize: 22,
    fontWeight: "bold",
    marginBottom: 10,
    color: "#333",
  },
  welcomeText: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    marginBottom: 30,
    lineHeight: 24,
  },
  walletCard: {
    backgroundColor: "#fff",
    margin: 20,
    padding: 25,
    borderRadius: 15,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#333",
  },
  address: {
    fontSize: 16,
    color: "#666",
    fontFamily: "monospace",
    textAlign: "center",
    marginBottom: 25,
    backgroundColor: "#f8f9fa",
    padding: 15,
    borderRadius: 10,
  },
  balanceContainer: {
    alignItems: "center",
    marginBottom: 25,
  },
  balanceLabel: {
    fontSize: 14,
    color: "#666",
    marginBottom: 5,
  },
  balance: {
    fontSize: 32,
    fontWeight: "bold",
    color: "#4A90E2",
  },
  button: {
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    marginVertical: 5,
  },
  primaryButton: {
    backgroundColor: "#4A90E2",
    padding: 15,
    borderRadius: 10,
    width: "100%",
    alignItems: "center",
  },
  secondaryButton: {
    backgroundColor: "#666",
    padding: 15,
    borderRadius: 10,
    width: "100%",
    alignItems: "center",
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  features: {
    backgroundColor: "#fff",
    margin: 20,
    padding: 20,
    borderRadius: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 20,
    color: "#333",
  },
  featureItem: {
    flexDirection: "row",
    alignItems: "center",
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: "#f1f3f5",
  },
  featureIcon: {
    fontSize: 24,
    marginRight: 15,
  },
  featureText: {
    fontSize: 16,
    color: "#333",
  },
  footer: {
    fontSize: 12,
    color: "#999",
    textAlign: "center",
    marginVertical: 20,
  },
});

export default HomeScreen;
