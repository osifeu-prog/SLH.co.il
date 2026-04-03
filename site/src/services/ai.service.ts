import OpenAI from "openai";
import { CONFIG } from "../config";
import { logger } from "../core/logger";
import { AppError } from "../core/error";
import { prisma } from "../db";

const client = new OpenAI({ apiKey: CONFIG.openaiKey });

export async function askAI(prompt: string, opts?: { telegramId?: string; userId?: number }) {
  try {
    const completion = await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: prompt }]
    });

    const content = completion.choices[0].message.content || "";

    await prisma.aiRequestLog.create({
      data: {
        prompt,
        response: content,
        telegramId: opts?.telegramId,
        userId: opts?.userId
      }
    });

    if (!content) {
      throw new AppError("Empty response from AI", 502);
    }
    return content;
  } catch (err) {
    logger.error({ err }, "AI request failed");
    throw new AppError("שגיאה מול שירות ה-AI, נסה שוב מאוחר יותר.", 502);
  }
}
