import React, { useState } from "react";
import { View, Text, StyleSheet, TextInput, Button, Alert } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";

export default function WalletSetupScreen({ navigation }) {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const setupWallet = async () => {
    if (password !== confirmPassword) {
      Alert.alert("שגיאה", "הסיסמאות לא תואמות");
      return;
    }

    if (password.length < 6) {
      Alert.alert("שגיאה", "סיסמה חייבת להיות לפחות 6 תווים");
      return;
    }

    try {
      // סימולציה של יצירת ארנק
      const walletData = {
        address: "0x" + Math.random().toString(16).slice(2),
        created: new Date().toISOString(),
        balance: 0,
      };

      await AsyncStorage.setItem("wallet_data", JSON.stringify(walletData));
      Alert.alert("הצלחה", "הארנק נוצר בהצלחה!");
      navigation.replace("Main");
    } catch (error) {
      Alert.alert("שגיאה", "לא ניתן ליצור ארנק");
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>הקמת ארנק חדש</Text>
      <Text style={styles.subtitle}>צור ארנק קריפטו מאובטח</Text>

      <View style={styles.form}>
        <Text style={styles.label}>סיסמה</Text>
        <TextInput
          style={styles.input}
          placeholder="הכנס סיסמה"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
        />

        <Text style={styles.label}>אימות סיסמה</Text>
        <TextInput
          style={styles.input}
          placeholder="הכנס סיסמה שוב"
          secureTextEntry
          value={confirmPassword}
          onChangeText={setConfirmPassword}
        />

        <View style={styles.terms}>
          <Text style={styles.termsText}>
            בהמשך, תקבל מפתחות גיבוי. שמור אותם במקום בטוח!
          </Text>
        </View>

        <Button title="צור ארנק" onPress={setupWallet} color="#4A90E2" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: "#f8f9fa",
    justifyContent: "center",
  },
  title: {
    fontSize: 28,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    textAlign: "center",
    color: "#666",
    marginBottom: 40,
  },
  form: {
    backgroundColor: "white",
    borderRadius: 10,
    padding: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  label: {
    fontSize: 16,
    marginBottom: 5,
    color: "#333",
  },
  input: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 5,
    padding: 10,
    marginBottom: 20,
    fontSize: 16,
  },
  terms: {
    backgroundColor: "#fff3cd",
    padding: 10,
    borderRadius: 5,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: "#ffeaa7",
  },
  termsText: {
    color: "#856404",
    fontSize: 14,
    textAlign: "center",
  },
});
