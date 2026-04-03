import TelegramBot from "node-telegram-bot-api";
import { CONFIG } from "./config";
import { askAI } from "./ai";
import { getBalance } from "./blockchain";
import { prisma } from "./db";

let bot: TelegramBot | null = null;

export function initBot() {
  if (!CONFIG.telegramBotToken) {
    console.log("Telegram bot token missing — bot disabled");
    return;
  }

  bot = new TelegramBot(CONFIG.telegramBotToken, { polling: true });
  console.log("Telegram bot initialized");

  bot.onText(/\/start/, async (msg) => {
    bot?.sendMessage(
      msg.chat.id,
      "ברוך הבא! הנה הפקודות הזמינות:\n" +
      "/ask <שאלה> — לשאול את ה-AI\n" +
      "/balance <address> — לבדוק יתרה בארנק\n" +
      "/link <address> — לקשר ארנק לחשבון\n" +
      "/mybalance — לבדוק יתרה בארנק המקושר"
    );
  });

  bot.onText(/\/ask (.+)/, async (msg, match) => {
    const prompt = match?.[1];
    if (!prompt) {
      bot?.sendMessage(msg.chat.id, "לא התקבלה שאלה.");
      return;
    }

    const answer = await askAI(prompt);
    bot?.sendMessage(msg.chat.id, answer);
  });

  bot.onText(/\/balance (.+)/, async (msg, match) => {
    const address = match?.[1];
    if (!address) {
      bot?.sendMessage(msg.chat.id, "לא התקבל כתובת.");
      return;
    }

    const balance = await getBalance(address);
    bot?.sendMessage(msg.chat.id, `היתרה של ${address} היא: ${balance}`);
  });

  bot.onText(/\/link (.+)/, async (msg, match) => {
    const address = match?.[1];
    if (!address) {
      bot?.sendMessage(msg.chat.id, "לא התקבל כתובת.");
      return;
    }

    const telegramId = msg.from?.id.toString();
    if (!telegramId) return;

    let user = await prisma.user.findUnique({
      where: { telegramUserId: telegramId }
    });

    if (!user) {
      user = await prisma.user.create({
        data: { telegramUserId: telegramId }
      });
    }

    await prisma.wallet.create({
      data: {
        userId: user.id,
        address,
        verified: true
      }
    });

    bot?.sendMessage(msg.chat.id, `הארנק ${address} קושר בהצלחה!`);
  });

  bot.onText(/\/mybalance/, async (msg) => {
    const telegramId = msg.from?.id.toString();
    if (!telegramId) return;

    const user = await prisma.user.findUnique({
      where: { telegramUserId: telegramId },
      include: { wallets: true }
    });

    if (!user || user.wallets.length === 0) {
      bot?.sendMessage(msg.chat.id, "לא נמצא ארנק מקושר.");
      return;
    }

    const address = user.wallets[0].address;
    const balance = await getBalance(address);

    bot?.sendMessage(
      msg.chat.id,
      `היתרה בארנק המקושר (${address}): ${balance}`
    );
  });
}
