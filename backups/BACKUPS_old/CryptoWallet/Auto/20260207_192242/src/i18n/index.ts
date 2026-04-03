import AsyncStorage from "@react-native-async-storage/async-storage";
import en from "./en";
import he from "./he";
import ru from "./ru";
import ar from "./ar";

export const translations = {
  en,
  he,
  ru,
  ar,
};

export type LanguageCode = keyof typeof translations;
export type TranslationKey = keyof typeof en;

class I18nService {
  currentLanguage: LanguageCode = "en";

  async setLanguage(lang: LanguageCode): Promise<void> {
    this.currentLanguage = lang;
    try {
      await AsyncStorage.setItem("selha_wallet_language", lang);
    } catch (error) {
      console.error("Error saving language:", error);
    }
  }

  async getLanguage(): Promise<LanguageCode> {
    try {
      const savedLang = await AsyncStorage.getItem("selha_wallet_language") as LanguageCode;
      if (savedLang && translations[savedLang]) {
        this.currentLanguage = savedLang;
        return savedLang;
      }
    } catch (error) {
      console.error("Error loading language:", error);
    }
    return this.currentLanguage;
  }

  t(key: TranslationKey, lang?: LanguageCode): string {
    const language = lang || this.currentLanguage;
    return translations[language]?.[key] || translations.en[key] || key;
  }

  getAvailableLanguages(): { code: LanguageCode; name: string; flag: string }[] {
    return [
      { code: "he", name: "עברית", flag: "🇮🇱" },
      { code: "en", name: "English", flag: "🇺🇸" },
      { code: "ru", name: "Русский", flag: "🇷🇺" },
      { code: "ar", name: "العربية", flag: "🇸🇦" },
    ];
  }

  isRTL(lang?: LanguageCode): boolean {
    const language = lang || this.currentLanguage;
    return language === "he" || language === "ar";
  }
}

export const i18n = new I18nService();
