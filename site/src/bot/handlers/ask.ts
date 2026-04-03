import TelegramBot from "node-telegram-bot-api";
import { askAI } from "../../services/ai.service";

export function registerAskHandler(bot: TelegramBot) {
  bot.onText(/\/ask (.+)/, async (msg, match) => {
    const chatId = msg.chat.id;
    const prompt = match?.[1];
    const telegramId = msg.from?.id?.toString();

    if (!prompt) {
      bot.sendMessage(chatId, "לא התקבלה שאלה.");
      return;
    }

    try {
      const answer = await askAI(prompt, { telegramId });
      bot.sendMessage(chatId, answer);
    } catch (err: any) {
      bot.sendMessage(chatId, err.message || "אירעה שגיאה בשאילת ה-AI.");
    }
  });
}
