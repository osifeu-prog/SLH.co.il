import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  ScrollView,
  SafeAreaView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import AsyncStorage from "@react-native-async-storage/async-storage";

const WalletSetupScreen = () => {
  const navigation = useNavigation();
  const [step, setStep] = useState<"choice" | "import" | "create" | "backup" | "slh">("choice");
  const [privateKey, setPrivateKey] = useState("");
  const [seedPhrase, setSeedPhrase] = useState("");
  const [slhAddress, setSlhAddress] = useState("");
  const [walletAddress, setWalletAddress] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasSavedBackup, setHasSavedBackup] = useState(false);
  const [importMethod, setImportMethod] = useState<"privateKey" | "seedPhrase">("privateKey");

  // SLH contract address
  const SLH_CONTRACT_ADDRESS = "0xACb0A09414CEA1C879c67bB7A877E4e19480f022";

  const handleImportWallet = async () => {
    if (importMethod === "privateKey") {
      if (!privateKey.trim()) {
        Alert.alert("Error", "Please enter your private key");
        return;
      }
    } else {
      if (!seedPhrase.trim()) {
        Alert.alert("Error", "Please enter seed phrase (12 words)");
        return;
      }
    }

    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      Alert.alert(
        "Success",
        "Wallet imported successfully",
        [{ 
          text: "Continue", 
          onPress: () => navigation.navigate("Home" as never) 
        }]
      );
    } catch (error: any) {
      Alert.alert("Error", importMethod === "privateKey" ? "Invalid private key" : "Invalid seed phrase");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateWallet = async () => {
    setIsLoading(true);
    try {
      // Simulate wallet creation
      await new Promise(resolve => setTimeout(resolve, 1000));

      const mockSeedPhrase = "word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12";
      const mockAddress = "0x1234...5678";

      setSeedPhrase(mockSeedPhrase);
      setWalletAddress(mockAddress);
      setStep("backup");
    } catch (error) {
      Alert.alert("Error", "Failed to create wallet");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSLHWallet = async () => {
    const address = slhAddress.trim() || SLH_CONTRACT_ADDRESS;
    
    if (!address) {
      Alert.alert("Error", "Please enter wallet address");
      return;
    }

    setIsLoading(true);
    try {
      // Save SLH wallet info
      await AsyncStorage.setItem("selha_wallet", JSON.stringify({
        address: address,
        isContract: address === SLH_CONTRACT_ADDRESS,
        type: "slh_view_only",
        isSLH: true
      }));

      Alert.alert(
        "Success",
        address === SLH_CONTRACT_ADDRESS 
          ? "SLH contract added successfully" 
          : "Wallet address added successfully",
        [{ 
          text: "Continue", 
          onPress: () => navigation.navigate("Home" as never, { 
            walletAddress: address,
            isSLH: true 
          }) 
        }]
      );
    } catch (error) {
      Alert.alert("Error", "Failed to add wallet");
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackupConfirmed = async () => {
    if (!hasSavedBackup) {
      Alert.alert("Warning", "Please confirm you have saved your backup phrase");
      return;
    }

    try {
      // Simulate save operation
      await new Promise(resolve => setTimeout(resolve, 500));

      Alert.alert(
        "Success",
        "Wallet created successfully",
        [{ 
          text: "Continue", 
          onPress: () => navigation.navigate("Home" as never) 
        }]
      );
    } catch (error) {
      Alert.alert("Error", "Failed to save wallet");
    }
  };

  const renderChoiceScreen = () => (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to Selha Wallet</Text>
      <Text style={styles.subtitle}>Your gateway to Binance Smart Chain</Text>
      
      <TouchableOpacity 
        style={[styles.button, styles.primaryButton]}
        onPress={() => setStep("create")}
      >
        <Text style={styles.buttonText}>Create New Wallet (12 words)</Text>
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={[styles.button, styles.secondaryButton]}
        onPress={() => setStep("import")}
        disabled={isLoading}
      >
        <Text style={styles.buttonText}>Import Existing Wallet</Text>
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={[styles.button, styles.slhButton]}
        onPress={() => setStep("slh")}
      >
        <Text style={styles.buttonText}>View SLH Wallets</Text>
      </TouchableOpacity>
      
      <Text style={styles.securityNote}>
        Your keys, your crypto. We never store your private keys.
      </Text>
    </View>
  );

  const renderImportScreen = () => (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView>
        <Text style={styles.title}>Import Existing Wallet</Text>
        
        <View style={styles.tabContainer}>
          <TouchableOpacity 
            style={[styles.tab, importMethod === "privateKey" && styles.activeTab]}
            onPress={() => setImportMethod("privateKey")}
          >
            <Text style={[styles.tabText, importMethod === "privateKey" && styles.activeTabText]}>
              Private Key
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={[styles.tab, importMethod === "seedPhrase" && styles.activeTab]}
            onPress={() => setImportMethod("seedPhrase")}
          >
            <Text style={[styles.tabText, importMethod === "seedPhrase" && styles.activeTabText]}>
              Seed Phrase
            </Text>
          </TouchableOpacity>
        </View>
        
        {importMethod === "privateKey" ? (
          <>
            <Text style={styles.warningText}>
              ⚠️ Never share your private key with anyone!
            </Text>
            
            <TextInput
              style={styles.textInput}
              placeholder="Paste your private key here (0x...)"
              placeholderTextColor="#999"
              value={privateKey}
              onChangeText={setPrivateKey}
              multiline
              numberOfLines={4}
              textAlignVertical="top"
              secureTextEntry
            />
          </>
        ) : (
          <>
            <Text style={styles.warningText}>
              ⚠️ Enter 12 words in order, separated by spaces
            </Text>
            
            <TextInput
              style={styles.textInput}
              placeholder="Enter your seed phrase (12 words)"
              placeholderTextColor="#999"
              value={seedPhrase}
              onChangeText={setSeedPhrase}
              multiline
              numberOfLines={6}
              textAlignVertical="top"
            />
          </>
        )}
        
        <TouchableOpacity 
          style={[styles.button, styles.primaryButton]}
          onPress={handleImportWallet}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Import Wallet</Text>
          )}
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.button, styles.secondaryButton]}
          onPress={() => setStep("choice")}
        >
          <Text style={styles.buttonText}>Back</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );

  const renderCreateScreen = () => (
    <View style={styles.container}>
      <Text style={styles.title}>Create New Wallet</Text>
      <Text style={styles.infoText}>
        We will create a wallet with 12 words for maximum security
      </Text>
      
      <TouchableOpacity 
        style={[styles.button, styles.primaryButton]}
        onPress={handleCreateWallet}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Create New Wallet</Text>
        )}
      </TouchableOpacity>
      
      <TouchableOpacity 
        style={[styles.button, styles.secondaryButton]}
        onPress={() => setStep("choice")}
      >
        <Text style={styles.buttonText}>Back</Text>
      </TouchableOpacity>
    </View>
  );

  const renderBackupScreen = () => (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>📝 Save Your Seed Phrase</Text>
      <Text style={styles.warningText}>
        ⚠️ Write this down and keep it safe! This is the only key to recover your wallet.
      </Text>
      
      <View style={styles.seedPhraseContainer}>
        <Text style={styles.seedPhrase}>{seedPhrase}</Text>
      </View>
      
      <View style={styles.addressContainer}>
        <Text style={styles.addressLabel}>Generated Address:</Text>
        <Text style={styles.address}>{walletAddress}</Text>
      </View>
      
      <View style={styles.checkboxContainer}>
        <TouchableOpacity 
          style={[styles.checkbox, hasSavedBackup && styles.checkboxChecked]}
          onPress={() => setHasSavedBackup(!hasSavedBackup)}
        >
          {hasSavedBackup && <Text style={styles.checkboxText}>✓</Text>}
        </TouchableOpacity>
        <Text style={styles.checkboxLabel}>
          I confirm I have saved my seed phrase in a safe place
        </Text>
      </View>
      
      <TouchableOpacity 
        style={[styles.button, styles.primaryButton]}
        onPress={handleBackupConfirmed}
        disabled={!hasSavedBackup}
      >
        <Text style={styles.buttonText}>Continue to Wallet</Text>
      </TouchableOpacity>
    </ScrollView>
  );

  const renderSLHScreen = () => (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView>
        <Text style={styles.title}>View SLH Wallets</Text>
        <Text style={styles.infoText}>
          Enter an SLH wallet address to view balance and activity
        </Text>
        
        <View style={styles.slhInfoCard}>
          <Text style={styles.slhTitle}>Official SLH Contract:</Text>
          <Text style={styles.slhAddress}>{SLH_CONTRACT_ADDRESS}</Text>
          <Text style={styles.slhNote}>
            You can use this address to view contract balance and transactions
          </Text>
        </View>
        
        <TextInput
          style={styles.textInput}
          placeholder="Enter SLH wallet address (or leave empty to use official contract)"
          placeholderTextColor="#999"
          value={slhAddress}
          onChangeText={setSlhAddress}
        />
        
        <TouchableOpacity 
          style={[styles.button, styles.slhButton]}
          onPress={() => {
            setSlhAddress(SLH_CONTRACT_ADDRESS);
            Alert.alert("Copied", "Contract address copied");
          }}
        >
          <Text style={styles.buttonText}>Use Official Contract</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.button, styles.primaryButton]}
          onPress={handleSLHWallet}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>View Wallet</Text>
          )}
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.button, styles.secondaryButton]}
          onPress={() => setStep("choice")}
        >
          <Text style={styles.buttonText}>Back</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      {step === "choice" && renderChoiceScreen()}
      {step === "import" && renderImportScreen()}
      {step === "create" && renderCreateScreen()}
      {step === "backup" && renderBackupScreen()}
      {step === "slh" && renderSLHScreen()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#fff",
  },
  container: {
    flex: 1,
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 10,
    color: "#333",
  },
  subtitle: {
    fontSize: 16,
    textAlign: "center",
    marginBottom: 30,
    color: "#666",
  },
  infoText: {
    fontSize: 14,
    textAlign: "center",
    marginBottom: 20,
    color: "#666",
    lineHeight: 20,
  },
  button: {
    padding: 15,
    borderRadius: 10,
    alignItems: "center",
    marginVertical: 10,
  },
  primaryButton: {
    backgroundColor: "#4A90E2",
  },
  secondaryButton: {
    backgroundColor: "#666",
  },
  slhButton: {
    backgroundColor: "#8B4513",
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  securityNote: {
    fontSize: 12,
    color: "#999",
    textAlign: "center",
    marginTop: 30,
    lineHeight: 18,
  },
  warningText: {
    fontSize: 14,
    color: "#E74C3C",
    marginBottom: 20,
    textAlign: "center",
    lineHeight: 20,
  },
  textInput: {
    borderWidth: 1,
    borderColor: "#ddd",
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    minHeight: 60,
    marginBottom: 20,
  },
  seedPhraseContainer: {
    backgroundColor: "#f8f9fa",
    padding: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: "#4A90E2",
    marginBottom: 20,
  },
  seedPhrase: {
    fontSize: 18,
    lineHeight: 30,
    textAlign: "center",
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
  },
  addressContainer: {
    backgroundColor: "#f8f9fa",
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  addressLabel: {
    fontSize: 14,
    color: "#666",
    marginBottom: 5,
  },
  address: {
    fontSize: 14,
    color: "#333",
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
    textAlign: "center",
  },
  checkboxContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
    paddingHorizontal: 10,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: "#4A90E2",
    borderRadius: 4,
    marginRight: 10,
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
  },
  tabContainer: {
    flexDirection: "row",
    marginBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#ddd",
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: "#4A90E2",
  },
  tabText: {
    fontSize: 16,
    color: "#666",
  },
  activeTabText: {
    color: "#4A90E2",
    fontWeight: "600",
  },
  slhInfoCard: {
    backgroundColor: "#FFF8DC",
    padding: 15,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#DAA520",
    marginBottom: 20,
  },
  slhTitle: {
    fontSize: 16,
    fontWeight: "bold",
    color: "#8B4513",
    marginBottom: 5,
  },
  slhAddress: {
    fontSize: 12,
    color: "#333",
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
    textAlign: "center",
    marginBottom: 10,
  },
  slhNote: {
    fontSize: 12,
    color: "#666",
    lineHeight: 16,
  },
});

export default WalletSetupScreen;
