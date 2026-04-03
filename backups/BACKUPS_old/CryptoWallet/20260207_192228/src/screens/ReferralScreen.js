import React from "react";
import { View, Text, StyleSheet, Button, Share } from "react-native";

export default function ReferralScreen() {
  const shareReferral = async () => {
    try {
      await Share.share({
        message: "הצטרפו לארנק הקריפטו שלי! קוד ההזמנה שלי: WALLET123",
      });
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>הזמנת חברים</Text>
      <View style={styles.card}>
        <Text style={styles.cardTitle">קוד ההזמנה שלך</Text>
        <Text style={styles.referralCode">WALLET123</Text>
        <Text style={styles.cardSubtitle">קבל 10% מעמלת החבר שהזמנת</Text>
      </View>
      
      <View style={styles.stats}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber">0</Text>
          <Text style={styles.statLabel">מוזמנים</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statNumber">0.00</Text>
          <Text style={styles.statLabel">רווח מצטבר</Text>
        </View>
      </View>

      <Button
        title="שתף קוד הזמנה"
        onPress={shareReferral}
        color="#4A90E2"
      />
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
    marginBottom: 30,
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    color: "#666",
    marginBottom: 10,
  },
  referralCode: {
    fontSize: 32,
    fontWeight: "bold",
    color: "#4A90E2",
    marginBottom: 10,
  },
  cardSubtitle: {
    fontSize: 14,
    color: "#888",
  },
  stats: {
    flexDirection: "row",
    justifyContent: "space-around",
    marginBottom: 30,
  },
  statItem: {
    alignItems: "center",
  },
  statNumber: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
  },
  statLabel: {
    fontSize: 14,
    color: "#666",
    marginTop: 5,
  },
});
