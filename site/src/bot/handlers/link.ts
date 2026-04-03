import TelegramBot from "node-telegram-bot-api";
import { linkWalletToUser } from "../../services/user.service";
import { validateAddress } from "../../services/blockchain.service";
import { ValidationError } from "../../core/error";

export function registerLinkHandler(bot: TelegramBot) {
  bot.onText(/\/link (.+)/, async (msg, match) => {
    const chatId = msg.chat.id;
    const address = match?.[1];

    if (!address) {
      bot.sendMessage(chatId, "לא התקבלה כתובת.");
      return;
    }

    const telegramId = msg.from?.id.toString();
    if (!telegramId) return;

    try {
      validateAddress(address);
      await linkWalletToUser(telegramId, address);

      bot.sendMessage(
        chatId,
        `הארנק ${address} קושר בהצלחה!`
      );
    } catch (err: any) {
      if (err instanceof ValidationError) {
        bot.sendMessage(chatId, err.message);
      } else {
        bot.sendMessage(chatId, "אירעה שגיאה בקישור הארנק.");
      }
    }
  });
}
