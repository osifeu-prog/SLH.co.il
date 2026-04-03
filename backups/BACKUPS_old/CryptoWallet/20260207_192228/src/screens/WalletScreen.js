import React, { useState } from "react";
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from "react-native";

const walletData = [
  { id: "1", name: "ביטקוין", symbol: "BTC", amount: "0.00", value: "0.00" },
  { id: "2", name: "אתריום", symbol: "ETH", amount: "0.00", value: "0.00" },
  { id: "3", name: "Solana", symbol: "SOL", amount: "0.00", value: "0.00" },
];

export default function WalletScreen() {
  const [coins] = useState(walletData);

  const renderItem = ({ item }) => (
    <TouchableOpacity style={styles.coinCard}>
      <View style={styles.coinHeader}>
        <View style={styles.coinIcon}>
          <Text style={styles.coinSymbol}>{item.symbol}</Text>
        </View>
        <View style={styles.coinInfo}>
          <Text style={styles.coinName}>{item.name}</Text>
          <Text style={styles.coinAmount}>{item.amount} {item.symbol}</Text>
        </View>
        <View style={styles.coinValue}>
          <Text style={styles.valueText}>{item.value}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>הארנק שלי</Text>
        <Text style={styles.totalValue}>סה"כ: 0.00</Text>
      </View>

      <FlatList
        data={coins}
        renderItem={renderItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
      />

      <View style={styles.actions}>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>קבל</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>שלח</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>קנה</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f8f9fa",
  },
  header: {
    backgroundColor: "white",
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#e9ecef",
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
  },
  totalValue: {
    fontSize: 18,
    textAlign: "center",
    color: "#4A90E2",
    marginTop: 5,
  },
  list: {
    padding: 10,
  },
  coinCard: {
    backgroundColor: "white",
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2,
  },
  coinHeader: {
    flexDirection: "row",
    alignItems: "center",
  },
  coinIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#4A90E2",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 15,
  },
  coinSymbol: {
    color: "white",
    fontWeight: "bold",
  },
  coinInfo: {
    flex: 1,
  },
  coinName: {
    fontSize: 16,
    fontWeight: "600",
  },
  coinAmount: {
    fontSize: 14,
    color: "#666",
  },
  coinValue: {
    alignItems: "flex-end",
  },
  valueText: {
    fontSize: 16,
    fontWeight: "bold",
  },
  actions: {
    flexDirection: "row",
    justifyContent: "space-around",
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: "#e9ecef",
    backgroundColor: "white",
  },
  actionButton: {
    backgroundColor: "#4A90E2",
    paddingHorizontal: 25,
    paddingVertical: 12,
    borderRadius: 25,
  },
  actionButtonText: {
    color: "white",
    fontWeight: "bold",
    fontSize: 16,
  },
});
