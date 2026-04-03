import TelegramBot from "node-telegram-bot-api";
import { CONFIG } from "../config";
import { logger } from "../core/logger";
import { registerStartHandler } from "./handlers/start";
import { registerAskHandler } from "./handlers/ask";
import { registerBalanceHandler } from "./handlers/balance";
import { registerLinkHandler } from "./handlers/link";
import { registerMyBalanceHandler } from "./handlers/mybalance";

let bot: TelegramBot | null = null;

export function getBot() {
  if (!bot) {
    throw new Error("Bot not initialized");
  }
  return bot;
}

export function initBot() {
  if (!CONFIG.telegramBotToken) {
    logger.warn("Telegram bot token missing — bot disabled");
    return;
  }

  bot = new TelegramBot(CONFIG.telegramBotToken, { polling: true });
  logger.info("Telegram bot initialized");

  registerStartHandler(bot);
  registerAskHandler(bot);
  registerBalanceHandler(bot);
  registerLinkHandler(bot);
  registerMyBalanceHandler(bot);
}
