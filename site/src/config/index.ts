import { config as loadEnv } from "dotenv";
import { z } from "zod";

loadEnv();

const EnvSchema = z.object({
  TELEGRAM_BOT_TOKEN: z.string().min(1, "TELEGRAM_BOT_TOKEN is required"),
  OPENAI_API_KEY: z.string().min(1, "OPENAI_API_KEY is required"),
  RPC_URL: z.string().min(1, "RPC_URL is required"),
  DATABASE_URL: z.string().min(1, "DATABASE_URL is required"),
  NODE_ENV: z.enum(["development", "production"]).default("development"),
  PORT: z
    .string()
    .default("3000")
    .transform((v) => parseInt(v, 10))
});

const parsed = EnvSchema.safeParse(process.env);

if (!parsed.success) {
  console.error("Invalid environment configuration:", parsed.error.format());
  process.exit(1);
}

export const CONFIG = {
  telegramBotToken: parsed.data.TELEGRAM_BOT_TOKEN,
  openaiKey: parsed.data.OPENAI_API_KEY,
  rpcUrl: parsed.data.RPC_URL,
  databaseUrl: parsed.data.DATABASE_URL,
  nodeEnv: parsed.data.NODE_ENV,
  port: parsed.data.PORT
};
