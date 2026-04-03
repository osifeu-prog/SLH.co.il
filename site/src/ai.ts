import OpenAI from "openai";
import { CONFIG } from "./config";

const client = new OpenAI({ apiKey: CONFIG.openaiKey });

export async function askAI(prompt: string) {
  const completion = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }]
  });

  return completion.choices[0].message.content || "No response";
}
