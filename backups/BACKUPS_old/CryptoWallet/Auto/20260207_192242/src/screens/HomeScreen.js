import React from "react";
import { View, Text, StyleSheet, Button } from "react-native";

export default function HomeScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>ברוך הבא לארנק הקריפטו</Text>
      <Text style={styles.subtitle}>ניהול מאובטח של המטבעות שלך</Text>
      
      <View style={styles.card}>
        <Text style={styles.cardTitle}>יתרה נוכחית</Text>
        <Text style={styles.balance}>0.00 </Text>
      </View>

      <View style={styles.buttonContainer}>
        <Button
          title="צפה בארנק"
          onPress={() => navigation.navigate("Wallet")}
          color="#4A90E2"
        />
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
    marginTop: 40,
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    textAlign: "center",
    color: "#666",
    marginBottom: 30,
  },
  card: {
    backgroundColor: "white",
    borderRadius: 10,
    padding: 20,
    marginVertical: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 16,
    color: "#666",
    marginBottom: 10,
  },
  balance: {
    fontSize: 32,
    fontWeight: "bold",
    color: "#333",
  },
  buttonContainer: {
    marginTop: 20,
    paddingHorizontal: 20,
  },
});
