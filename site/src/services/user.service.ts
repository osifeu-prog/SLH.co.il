import { prisma } from "../db";
import { ValidationError } from "../core/error";
import { snapshotWalletBalance } from "./blockchain.service";

export async function getOrCreateUserByTelegramId(telegramUserId: string) {
  let user = await prisma.user.findUnique({
    where: { telegramUserId }
  });

  if (!user) {
    user = await prisma.user.create({
      data: { telegramUserId }
    });
  }

  return user;
}

export async function linkWalletToUser(telegramUserId: string, address: string) {
  const user = await getOrCreateUserByTelegramId(telegramUserId);

  const existing = await prisma.wallet.findFirst({
    where: { address }
  });

  if (existing && existing.userId !== user.id) {
    throw new ValidationError("הארנק הזה כבר מקושר למשתמש אחר.");
  }

  const wallet = await prisma.wallet.create({
    data: {
      userId: user.id,
      address,
      verified: true
    }
  });

  await snapshotWalletBalance(wallet.id, wallet.address);

  return { user, wallet };
}

export async function getPrimaryWalletByTelegramId(telegramUserId: string) {
  const user = await prisma.user.findUnique({
    where: { telegramUserId },
    include: { wallets: true }
  });

  if (!user || user.wallets.length === 0) {
    throw new ValidationError("לא נמצא ארנק מקושר למשתמש.");
  }

  return user.wallets[0];
}
