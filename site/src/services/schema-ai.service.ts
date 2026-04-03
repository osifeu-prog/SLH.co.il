import OpenAI from "openai";
import { CONFIG } from "../config";
import { prisma } from "../db";

const client = new OpenAI({ apiKey: CONFIG.openaiKey });

export async function suggestSchemaChange(description: string) {
  const prompt = `
אתה מומחה Prisma. אני אתאר שינוי סכימה שאני רוצה.
תחזיר רק קטע Prisma schema מוצע, בלי טקסט חיצוני, בלי הסברים, רק את הבלוק(ים) הרלוונטיים.

תיאור השינוי:
${description}
`;

  const completion = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: prompt }]
  });

  const prismaDiff = completion.choices[0].message.content || "";

  const proposal = await prisma.migrationProposal.create({
    data: {
      title: description.slice(0, 100),
      description,
      prismaDiff
    }
  });

  return proposal;
}
