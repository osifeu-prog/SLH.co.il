import React, { useEffect, useState } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createStackNavigator } from "@react-navigation/stack";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { View, ActivityIndicator } from "react-native";
import Icon from "react-native-vector-icons/Ionicons";

// ייבוא מסכים
import HomeScreen from "./src/screens/HomeScreen";
import WalletScreen from "./src/screens/WalletScreen";
import BackupScreen from "./src/screens/BackupScreen";
import ReferralScreen from "./src/screens/ReferralScreen";
import ConvertStakeScreen from "./src/screens/ConvertStakeScreen";
import WalletSetupScreen from "./src/screens/WalletSetupScreen";

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;

          if (route.name === "Home") {
            iconName = focused ? "home" : "home-outline";
          } else if (route.name === "Convert") {
            iconName = focused ? "swap-horizontal" : "swap-horizontal-outline";
          } else if (route.name === "Referral") {
            iconName = focused ? "people" : "people-outline";
          } else if (route.name === "Backup") {
            iconName = focused ? "shield" : "shield-outline";
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: "#4A90E2",
        tabBarInactiveTintColor: "gray",
        tabBarStyle: {
          backgroundColor: "#fff",
          borderTopWidth: 1,
          borderTopColor: "#e9ecef",
        },
        headerStyle: {
          backgroundColor: "#fff",
        },
        headerTitleStyle: {
          color: "#333",
          fontWeight: "bold",
        },
        headerTintColor: "#333",
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{ title: "בית" }}
      />
      <Tab.Screen
        name="Convert"
        component={ConvertStakeScreen}
        options={{ title: "המרה וסטייקינג" }}
      />
      <Tab.Screen
        name="Referral"
        component={ReferralScreen}
        options={{ title: "הזמנות" }}
      />
      <Tab.Screen
        name="Backup"
        component={BackupScreen}
        options={{ title: "גיבוי" }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [hasWallet, setHasWallet] = useState(false);

  useEffect(() => {
    checkWallet();
  }, []);

  const checkWallet = async () => {
    try {
      const wallet = await AsyncStorage.getItem("wallet_data");
      setHasWallet(!!wallet);
    } catch (error) {
      console.error("Error checking wallet:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#4A90E2" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {hasWallet ? (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen name="Wallet" component={WalletScreen} />
          </>
        ) : (
          <Stack.Screen name="WalletSetup" component={WalletSetupScreen} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
