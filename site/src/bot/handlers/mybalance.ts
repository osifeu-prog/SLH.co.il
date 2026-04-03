import TelegramBot from "node-telegram-bot-api";
import { getPrimaryWalletByTelegramId } from "../../services/user.service";
import { getBalance } from "../../services/blockchain.service";
import { ValidationError } from "../../core/error";

export function registerMyBalanceHandler(bot: TelegramBot) {
  bot.onText(/\/mybalance/, async (msg) => {
    const chatId = msg.chat.id;
    const telegramId = msg.from?.id.toString();
    if (!telegramId) return;

    try {
      const wallet = await getPrimaryWalletByTelegramId(telegramId);
      const balance = await getBalance(wallet.address);

      bot.sendMessage(
        chatId,
        `היתרה בארנק המקושר (${wallet.address}): ${balance} ETH`
      );
    } catch (err: any) {
      if (err instanceof ValidationError) {
        bot.sendMessage(chatId, err.message);
      } else {
        bot.sendMessage(chatId, "שגיאה בקריאת היתרה מהארנק המקושר.");
      }
    }
  });
}
