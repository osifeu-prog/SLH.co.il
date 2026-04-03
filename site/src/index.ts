import { connectDb } from "./db";
import { initBot } from "./bot";
import { createServer } from "./server";
import { CONFIG } from "./config";
import { logger } from "./core/logger";

async function main() {
  await connectDb();
  initBot();

  const app = createServer();
  app.listen(CONFIG.port, () => {
    logger.info(`Server running on port ${CONFIG.port}`);
  });
}

main().catch((err) => {
  logger.error({ err }, "Fatal error on startup");
  process.exit(1);
});
