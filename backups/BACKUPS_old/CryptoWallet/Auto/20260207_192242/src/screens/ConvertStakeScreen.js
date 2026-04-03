import React, { useState } from "react";
import { View, Text, StyleSheet, TextInput, Button, Picker } from "react-native";

export default function ConvertStakeScreen() {
  const [amount, setAmount] = useState("");
  const [fromCurrency, setFromCurrency] = useState("BTC");
  const [toCurrency, setToCurrency] = useState("ETH");

  return (
    <View style={styles.container}>
      <Text style={styles.title}>המרה וסטייקינג</Text>
      
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>המרת מטבע</Text>
        
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="כמות"
            value={amount}
            onChangeText={setAmount}
            keyboardType="numeric"
          />
          <Picker
            selectedValue={fromCurrency}
            style={styles.picker}
            onValueChange={setFromCurrency}
          >
            <Picker.Item label="BTC" value="BTC" />
            <Picker.Item label="ETH" value="ETH" />
            <Picker.Item label="SOL" value="SOL" />
          </Picker>
        </View>

        <View style={styles.arrowContainer}>
          <Text style={styles.arrow}>↓</Text>
        </View>

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="כמות"
            value={(parseFloat(amount) || 0).toString()}
            editable={false}
          />
          <Picker
            selectedValue={toCurrency}
            style={styles.picker}
            onValueChange={setToCurrency}
          >
            <Picker.Item label="ETH" value="ETH" />
            <Picker.Item label="BTC" value="BTC" />
            <Picker.Item label="SOL" value="SOL" />
          </Picker>
        </View>

        <Button title="המר" color="#4A90E2" />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle">סטייקינג</Text>
        <Text style={styles.infoText">נעילה לטווח ארוך לריבית משתלמת</Text>
        <Button title="התחל סטייקינג" color="#28a745" />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: "#f8f9fa",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
    marginTop: 20,
    marginBottom: 30,
  },
  card: {
    backgroundColor: "white",
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 15,
  },
  inputRow: {
    flexDirection: "row",
    marginBottom: 10,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 5,
    padding: 10,
    marginRight: 10,
  },
  picker: {
    width: 100,
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 5,
  },
  arrowContainer: {
    alignItems: "center",
    marginVertical: 10,
  },
  arrow: {
    fontSize: 24,
    color: "#4A90E2",
  },
  infoText: {
    fontSize: 14,
    color: "#666",
    marginBottom: 15,
  },
});
