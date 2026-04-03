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
import * as Clipboard from "expo-clipboard";
import { WalletService } from "../services/walletService";

const BackupScreen = () => {
  const navigation = useNavigation();
  const [wallet, setWallet] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  const [showMnemonic, setShowMnemonic] = useState(false);
  const [hasSavedBackup, setHasSavedBackup] = useState(false);

  useEffect(() => {
    loadWallet();
  }, []);

  const loadWallet = async () => {
    setIsLoading(true);
    try {
      const walletData = await WalletService.getWallet();
      setWallet(walletData);
    } catch (error) {
      console.error("Error loading wallet:", error);
      Alert.alert("שגיאה", "לא ניתן לטעון את פרטי הארנק");
    } finally {
      setIsLoading(false);
    }
  };

  const copyPrivateKey = async () => {
    if (wallet?.privateKey) {
      await Clipboard.setStringAsync(wallet.privateKey);
      Alert.alert("✅", "מפתח פרטי הועתק ללוח");
    }
  };

  const copyMnemonic = async () => {
    if (wallet?.mnemonic) {
      await Clipboard.setStringAsync(wallet.mnemonic);
      Alert.alert("✅", "Seed phrase הועתק ללוח");
    }
  };

  const copyAddress = async () => {
    if (wallet?.address) {
      await Clipboard.setStringAsync(wallet.address);
      Alert.alert("✅", "כתובת הארנק הועתקה");
    }
  };

  const saveBackupAsFile = async () => {
    if (!wallet) return;

    const backupData = {
      address: wallet.address,
      privateKey: wallet.privateKey,
      mnemonic: wallet.mnemonic,
      createdAt: wallet.createdAt,
      network: "Binance Smart Chain",
    };

    const jsonString = JSON.stringify(backupData, null, 2);
    
    await Clipboard.setStringAsync(jsonString);
    Alert.alert("✅", "גיבוי הועתק ללוח - שמור אותו!");
  };

  const confirmBackupSaved = () => {
    setHasSavedBackup(true);
    Alert.alert(
      "חשוב!",
      "וודא שהעתקת ושמרת את פרטי הגיבוי במקום בטוח.\nאם תאבד אותם, תאבד את הגישה לארנק לנצח!",
      [{ text: "הבנתי" }]
    );
  };

  const deleteWallet = () => {
    Alert.alert(
      "אזהרה! ⚠️",
      "פעולה זו תמחק את הארנק מהמכשיר.\nוודא שיש לך גיבוי לפני ההמשך!",
      [
        { text: "ביטול", style: "cancel" },
        {
          text: "מחק",
          style: "destructive",
          onPress: async () => {
            try {
              await WalletService.deleteWallet();
              Alert.alert("✅", "הארנק נמחק בהצלחה");
              navigation.navigate("Home" as never);
            } catch (error) {
              Alert.alert("שגיאה", "לא ניתן למחוק את הארנק");
            }
          },
        },
      ]
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4A90E2" />
        <Text style={styles.loadingText}>טוען פרטי ארנק...</Text>
      </View>
    );
  }

  if (!wallet) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>אין ארנק פעיל</Text>
        <Text style={styles.message}>
          יש לחבר ארנק כדי לראות אפשרויות גיבוי
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
          <Text style={styles.title}>גיבוי ארנק</Text>
          <Text style={styles.subtitle}>
            שמור את הפרטים הבאים במקום בטוח!
          </Text>
        </View>

        <View style={styles.warningBox}>
          <Text style={styles.warningTitle}>⚠️ אזהרה קריטית</Text>
          <Text style={styles.warningText}>
            אם תאבד את פרטי הגיבוי, תאבד את הגישה לארנק לנצח!
          </Text>
          <Text style={styles.warningText}>
            אף אחד לא יכול לשחזר עבורך את הגישה.
          </Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>כתובת הארנק</Text>
          <TouchableOpacity onPress={copyAddress}>
            <Text style={styles.address}>{wallet.address}</Text>
          </TouchableOpacity>
          <Text style={styles.cardNote}>
            לחץ להעתקה - ניתן לשתף זאת בבטחה
          </Text>
        </View>

        {wallet.privateKey && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>מפתח פרטי</Text>
              <TouchableOpacity onPress={() => setShowPrivateKey(!showPrivateKey)}>
                <Text style={styles.toggleButton}>
                  {showPrivateKey ? "הסתר" : "הצג"}
                </Text>
              </TouchableOpacity>
            </View>
            
            {showPrivateKey ? (
              <TouchableOpacity onPress={copyPrivateKey}>
                <Text style={styles.privateKey}>{wallet.privateKey}</Text>
              </TouchableOpacity>
            ) : (
              <Text style={styles.hiddenText}>••••••••••••••••••••••••</Text>
            )}
            
            <Text style={styles.cardNote}>
              ⚠️ לעולם אל תשתף את המפתח הפרטי שלך!
            </Text>
          </View>
        )}

        {wallet.mnemonic && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.cardTitle}>Seed Phrase (12 מילים)</Text>
              <TouchableOpacity onPress={() => setShowMnemonic(!showMnemonic)}>
                <Text style={styles.toggleButton}>
                  {showMnemonic ? "הסתר" : "הצג"}
                </Text>
              </TouchableOpacity>
            </View>
            
            {showMnemonic && (
              <TouchableOpacity onPress={copyMnemonic}>
                <View style={styles.mnemonicContainer}>
                  <Text style={styles.mnemonic}>{wallet.mnemonic}</Text>
                </View>
              </TouchableOpacity>
            )}
            
            <Text style={styles.cardNote}>
              רשום מילים אלו על דף נייר ושמור במקום בטוח
            </Text>
          </View>
        )}

        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>הוראות גיבוי בטוח:</Text>
          <Text style={styles.infoText}>1. רשמו את ה-Seed Phrase על דף נייר</Text>
          <Text style={styles.infoText}>2. שמרו במקום בטוח ואטום ללחות</Text>
          <Text style={styles.infoText}>3. לעולם אל תשמרו בצילום/מייל</Text>
          <Text style={styles.infoText}>4. לא לשתף עם אף אחד</Text>
        </View>

        <View style={styles.checkboxContainer}>
          <TouchableOpacity
            style={[styles.checkbox, hasSavedBackup && styles.checkboxChecked]}
            onPress={() => setHasSavedBackup(!hasSavedBackup)}
          >
            {hasSavedBackup && <Text style={styles.checkboxText}>✓</Text>}
          </TouchableOpacity>
          <Text style={styles.checkboxLabel}>
            אישרתי ששמרתי את פרטי הגיבוי במקום בטוח
          </Text>
        </View>

        <TouchableOpacity
          style={[styles.actionButton, styles.primaryButton]}
          onPress={saveBackupAsFile}
          disabled={!hasSavedBackup}
        >
          <Text style={styles.actionButtonText}>שמור גיבוי כקובץ</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.secondaryButton]}
          onPress={confirmBackupSaved}
        >
          <Text style={styles.actionButtonText}>אישרתי גיבוי</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionButton, styles.dangerButton]}
          onPress={deleteWallet}
        >
          <Text style={styles.actionButtonText}>מחק ארנק מהמכשיר</Text>
        </TouchableOpacity>
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
  warningBox: {
    backgroundColor: "#fff3cd",
    margin: 15,
    padding: 20,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#ffeaa7",
  },
  warningTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#856404",
    marginBottom: 10,
  },
  warningText: {
    fontSize: 14,
    color: "#856404",
    lineHeight: 20,
  },
  card: {
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
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "bold",
    color: "#333",
  },
  toggleButton: {
    fontSize: 14,
    color: "#4A90E2",
    fontWeight: "600",
  },
  address: {
    fontSize: 16,
    color: "#333",
    fontFamily: "monospace",
    textAlign: "center",
    marginBottom: 10,
    backgroundColor: "#f8f9fa",
    padding: 15,
    borderRadius: 10,
  },
  privateKey: {
    fontSize: 14,
    color: "#333",
    fontFamily: "monospace",
    textAlign: "center",
    marginBottom: 10,
    backgroundColor: "#f8f9fa",
    padding: 15,
    borderRadius: 10,
    lineHeight: 20,
  },
  hiddenText: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    marginBottom: 10,
    backgroundColor: "#f8f9fa",
    padding: 15,
    borderRadius: 10,
    letterSpacing: 4,
  },
  mnemonicContainer: {
    backgroundColor: "#f8f9fa",
    padding: 20,
    borderRadius: 10,
    marginBottom: 10,
  },
  mnemonic: {
    fontSize: 18,
    color: "#333",
    lineHeight: 32,
    textAlign: "center",
    fontFamily: "monospace",
  },
  cardNote: {
    fontSize: 14,
    color: "#666",
    textAlign: "center",
    lineHeight: 20,
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
  checkboxContainer: {
    flexDirection: "row",
    alignItems: "center",
    margin: 15,
    padding: 15,
    backgroundColor: "#fff",
    borderRadius: 10,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: "#4A90E2",
    borderRadius: 4,
    marginRight: 15,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxChecked: {
    backgroundColor: "#4A90E2",
  },
  checkboxText: {
    color: "#fff",
    fontSize: 16,
  },
  checkboxLabel: {
    fontSize: 16,
    flex: 1,
    color: "#333",
  },
  actionButton: {
    padding: 16,
    borderRadius: 10,
    alignItems: "center",
    marginHorizontal: 15,
    marginVertical: 8,
  },
  primaryButton: {
    backgroundColor: "#4A90E2",
  },
  secondaryButton: {
    backgroundColor: "#666",
  },
  dangerButton: {
    backgroundColor: "#dc3545",
  },
  actionButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  button: {
    padding: 15,
    borderRadius: 10,
    backgroundColor: "#4A90E2",
    alignItems: "center",
    margin: 20,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
});

export default BackupScreen;
