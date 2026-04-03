import React from "react";
import { View, Text, StyleSheet, Button } from "react-native";

export default function BackupScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>גיבוי ארנק</Text>
      <Text style={styles.warning}>⚠️ חשוב מאוד!</Text>
      <Text style={styles.instructions}>
        שמור את מפתחות הגיבוי במקום בטוח. ללא המפתחות, לא תוכל לשחזר את הארנק.
      </Text>
      <View style={styles.seedPhrase}>
        <Text style={styles.seedText}>seed phrase will appear here</Text>
      </View>
      <Button title="צור מפתחות גיבוי" color="#4A90E2" />
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
    marginBottom: 20,
  },
  warning: {
    fontSize: 18,
    color: "#dc3545",
    textAlign: "center",
    marginBottom: 20,
  },
  instructions: {
    fontSize: 16,
    textAlign: "center",
    marginBottom: 30,
    lineHeight: 24,
  },
  seedPhrase: {
    backgroundColor: "white",
    padding: 20,
    borderRadius: 10,
    marginBottom: 30,
    borderWidth: 1,
    borderColor: "#ddd",
    alignItems: "center",
  },
  seedText: {
    fontSize: 16,
    color: "#666",
  },
});
