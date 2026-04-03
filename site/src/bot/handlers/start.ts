import TelegramBot from "node-telegram-bot-api";

export function registerStartHandler(bot: TelegramBot) {
  bot.onText(/\/start/, async (msg) => {
    bot.sendMessage(
      msg.chat.id,
      "ברוך הבא! הנה הפקודות הזמינות:\n" +
      "/ask <שאלה> — לשאול את ה-AI\n" +
      "/balance <address> — לבדוק יתרה בארנק\n" +
      "/link <address> — לקשר ארנק לחשבון\n" +
      "/mybalance — לבדוק יתרה בארנק המקושר"
    );
  });
}
