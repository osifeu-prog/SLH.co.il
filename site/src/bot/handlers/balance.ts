import TelegramBot from "node-telegram-bot-api";
import { getBalance } from "../../services/blockchain.service";
import { ValidationError } from "../../core/error";

export function registerBalanceHandler(bot: TelegramBot) {
  bot.onText(/\/balance (.+)/, async (msg, match) => {
    const chatId = msg.chat.id;
    const address = match?.[1];

    if (!address) {
      bot.sendMessage(chatId, "לא התקבלה כתובת.");
      return;
    }

    try {
      const balance = await getBalance(address);
      bot.sendMessage(chatId, `היתרה של ${address} היא: ${balance} ETH`);
    } catch (err: any) {
      if (err instanceof ValidationError) {
        bot.sendMessage(chatId, err.message);
      } else {
        bot.sendMessage(chatId, "שגיאה בקריאת היתרה, נסה שוב מאוחר יותר.");
      }
    }
  });
}
