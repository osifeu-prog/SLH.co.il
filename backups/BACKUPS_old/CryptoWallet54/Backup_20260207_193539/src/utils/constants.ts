// קריפטו-סלחה - קונפיגורציה מתקדמת
export const APP_CONFIG = {
  APP_NAME: "Selha Wallet",
  VERSION: "2.0.0",
  SUPPORT_EMAIL: "support@selha.app",
};

// רשתות
export const NETWORKS = {
  BSC_MAINNET: {
    name: "BSC Mainnet",
    rpcUrl: "https://bsc-dataseed.binance.org/",
    chainId: 56,
    symbol: "BNB",
    explorer: "https://bscscan.com",
  },
  BSC_TESTNET: {
    name: "BSC Testnet",
    rpcUrl: "https://data-seed-prebsc-1-s1.binance.org:8545/",
    chainId: 97,
    symbol: "tBNB",
    explorer: "https://testnet.bscscan.com",
  },
};

// חוזים חכמים
export const CONTRACTS = {
  SLH_MAINNET: "0xACb0A09414CEA1C879c67bB7A877E4e19480f022",
  SLH_TESTNET: "0xYourTestnetContractAddressHere", // החלף בכתובת טסט נט
  MEAH_TOKEN: "0xMeahTokenAddressHere", // החלף בכתובת MEAH
  STAKING_CONTRACT: "0xStakingContractAddressHere", // החלף בכתובת סטייקינג
};

// שיעורי המרה
export const CONVERSION_RATES = {
  SLH_TO_MEAH: 444, // 1 SLH = 444 MEAH
  STAKE_REWARD_RATE: 0.15, // 15% APY
  REFERRAL_REWARD: 100, // 100 MEAH להזמנה
};

// הגדרות אבטחה
export const SECURITY = {
  MAX_PIN_ATTEMPTS: 5,
  SESSION_TIMEOUT: 15 * 60 * 1000, // 15 דקות
  ENCRYPTION_KEY: "selha-wallet-secure-key-2024",
};

export default {
  APP_CONFIG,
  NETWORKS,
  CONTRACTS,
  CONVERSION_RATES,
  SECURITY,
};
