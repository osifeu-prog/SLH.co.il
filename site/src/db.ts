import { PrismaClient } from "@prisma/client";
import { logger } from "./core/logger";

export const prisma = new PrismaClient();

export async function connectDb() {
  try {
    await prisma.$connect();
    logger.info("Connected to database");
  } catch (err) {
    logger.error({ err }, "Failed to connect to database");
    process.exit(1);
  }
}
