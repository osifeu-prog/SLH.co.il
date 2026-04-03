import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ScrollView,
  ActivityIndicator,
  SafeAreaView,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { WalletService } from "../services/walletService";
import { ReferralService } from "../services/referralService";
import { SLH_CONTRACT_ADDRESS } from "../utils/constants";

const WalletScreen = () => {
  const navigation = useNavigation();
  const [step, setStep] = useState<"choice" | "import" | "view">("choice");
  const [privateKey, setPrivateKey] = useState("");
  const [address, setAddress] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleImportWallet = async () => {
    if (!privateKey.trim()) {
      Alert.alert("שגיאה", "נא להזין מפתח פרטי או seed phrase");
      return;
    }

    setIsLoading(true);
    try {
      const wallet = await WalletService.importWallet(privateKey);
      
      // אתחל מערכת הפניות
      await ReferralService.initializeReferralSystem(wallet.address);
      
      Alert.alert(
        "הצלחה! 🎉",
        "הארנק יובא בהצלחה!",
        [
          {
            text: "הבנתי",
            onPress: () => {
              navigation.navigate("Home" as never);
            },
          },
        ]
      );
    } catch (error: any) {
      Alert.alert("שגיאה", "מפתח פרטי לא תקין");
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewOnlyWallet = async () => {
    const walletAddress = address.trim() || SLH_CONTRACT_ADDRESS;

    if (!WalletService.isValidAddress(walletAddress)) {
      Alert.alert("שגיאה", "כתובת ארנק לא תקינה");
      return;
    }

    setIsLoading(true);
    try {
      const slhBalance = await WalletService.getSLHBalance(walletAddress);
      const bnbBalance = await WalletService.getBNBBalance(walletAddress);
      
      const walletData = {
        address: walletAddress,
        isImported: false,
        isSLHWallet: true,
        balance: bnbBalance,
        slhBalance: slhBalance,
        createdAt: new Date().toISOString(),
        lastSync: new Date().toISOString(),
      };
      
      await WalletService.saveWallet(walletData);
      
      Alert.alert(
        "הצלחה! 👁️",
        "ארנק לצפייה בלבד נוסף בהצלחה",
        [
          {
            text: "הבנתי",
            onPress: () => {
              navigation.navigate("Home" as never);
            },
          },
        ]
      );
    } catch (error) {
      Alert.alert("שגיאה", "לא ניתן לטעון את הארנק");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNewWallet = async () => {
    Alert.alert(
      "אזהרה ⚠️",
      "אתה עומד ליצור ארנק חדש. הקפד לשמור את המפתח הפרטי והמילים במקום בטוח!",
      [
        { text: "ביטול", style: "cancel" },
        {
          text: "ממשיך",
          onPress: async () => {
            setIsLoading(true);
            try {
              const wallet = await WalletService.createNewWallet();
              
              // אתחל מערכת הפניות
              await ReferralService.initializeReferralSystem(wallet.address);
              
              Alert.alert(
                "🎉 ארנק נוצר בהצלחה!",
                `כתובת הארנק שלך:\n${wallet.address}`,
                [
                  {
                    text: "למסך הבית",
                    onPress: () => {
                      navigation.navigate("Home" as never);
                    },
                  },
                ]
              );
            } catch (error) {
              Alert.alert("שגיאה", "לא ניתן ליצור ארנק");
            } finally {
              setIsLoading(false);
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.title}>חבר ארנק ל-Selha</Text>
        
        {step === "choice" && (
          <View style={styles.choiceContainer}>
            <TouchableOpacity
              style={[styles.card, styles.createCard]}
              onPress={handleCreateNewWallet}
              disabled={isLoading}
            >
              <Text style={styles.cardIcon}>🆕</Text>
              <Text style={styles.cardTitle}>ארנק חדש</Text>
              <Text style={styles.cardDescription}>
                יצירת ארנק חדש עם 12 מילים
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.card, styles.importCard]}
              onPress={() => setStep("import")}
            >
              <Text style={styles.cardIcon}>📥</Text>
              <Text style={styles.cardTitle}>ייבוא ארנק</Text>
              <Text style={styles.cardDescription}>
                ייבוא ארנק קיים עם מפתח פרטי
              </Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.card, styles.viewCard]}
              onPress={() => setStep("view")}
            >
              <Text style={styles.cardIcon}>👁️</Text>
              <Text style={styles.cardTitle}>צפייה בלבד</Text>
              <Text style={styles.cardDescription}>
                הוספת כתובת לצפייה ביתרות
              </Text>
            </TouchableOpacity>
          </View>
        )}

        {step === "import" && (
          <View style={styles.importContainer}>
            <Text style={styles.sectionTitle}>ייבוא ארנק קיים</Text>
            <Text style={styles.warning}>
              ⚠️ הזן את המפתח הפרטי או 12 המילים
            </Text>
            
            <TextInput
              style={styles.textInput}
              placeholder="מפתח פרטי או seed phrase"
              placeholderTextColor="#999"
              value={privateKey}
              onChangeText={setPrivateKey}
              multiline
              numberOfLines={4}
              secureTextEntry
            />
            
            <TouchableOpacity
              style={[styles.button, styles.primaryButton]}
              onPress={handleImportWallet}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>ייבוא ארנק</Text>
              )}
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={() => setStep("choice")}
            >
              <Text style={styles.buttonText}>חזרה</Text>
            </TouchableOpacity>
          </View>
        )}

        {step === "view" && (
          <View style={styles.viewContainer}>
            <Text style={styles.sectionTitle}>צפייה בכתובת ארנק</Text>
            <Text style={styles.info}>
              הזן כתובת ארנק לצפייה ביתרות (או השאר ריק עבור החוזה הרשמי)
            </Text>
            
            <TextInput
              style={styles.textInput}
              placeholder="0x..."
              placeholderTextColor="#999"
              value={address}
              onChangeText={setAddress}
            />
            
            <Text style={styles.contractInfo}>
              חוזה SLH הרשמי: {SLH_CONTRACT_ADDRESS}
            </Text>
            
            <TouchableOpacity
              style={[styles.button, styles.slhButton]}
              onPress={() => setAddress(SLH_CONTRACT_ADDRESS)}
            >
              <Text style={styles.buttonText}>השתמש בחוזה הרשמי</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.button, styles.primaryButton]}
              onPress={handleViewOnlyWallet}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.buttonText}>הוסף לצפייה</Text>
              )}
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton]}
              onPress={() => setStep("choice")}
            >
              <Text style={styles.buttonText}>חזרה</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8f9fa",
  },
  scrollContent: {
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 30,
    color: "#333",
  },
  choiceContainer: {
    flex: 1,
  },
  card: {
    backgroundColor: "#fff",
    padding: 25,
    borderRadius: 15,
    marginBottom: 20,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  createCard: {
    borderTopWidth: 5,
    borderTopColor: "#4A90E2",
  },
  importCard: {
    borderTopWidth: 5,
    borderTopColor: "#34C759",
  },
  viewCard: {
    borderTopWidth: 5,
    borderTopColor: "#8B4513",
  },
  cardIcon: {
    fontSize: 40,
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 22,
    fontWeight: "bold",
    marginBottom: 10,
    color: "#333",
  },
  cardDescription: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
    lineHeight: 22,
  },
  importContainer: {
    flex: 1,
  },
  viewContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: "bold",
    marginBottom: 15,
    color: "#333",
  },
  warning: {
    fontSize: 16,
    color: "#E74C3C",
    marginBottom: 20,
    textAlign: "center",
  },
  info: {
    fontSize: 16,
    color: "#666",
    marginBottom: 20,
    textAlign: "center",
    lineHeight: 22,
  },
  textInput: {
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    marginBottom: 20,
    minHeight: 60,
  },
  contractInfo: {
    fontSize: 12,
    color: "#666",
    fontFamily: "monospace",
    textAlign: "center",
    marginBottom: 20,
    backgroundColor: "#f8f9fa",
    padding: 10,
    borderRadius: 8,
  },
  button: {
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    marginBottom: 10,
  },
  primaryButton: {
    backgroundColor: "#4A90E2",
  },
  secondaryButton: {
    backgroundColor: "#666",
  },
  slhButton: {
    backgroundColor: "#8B4513",
    marginBottom: 20,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
});

export default WalletScreen;
