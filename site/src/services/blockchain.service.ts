import { ethers } from "ethers";
import { CONFIG } from "../config";
import { logger } from "../core/logger";
import { ValidationError, AppError } from "../core/error";
import { prisma } from "../db";

const provider = new ethers.JsonRpcProvider(CONFIG.rpcUrl);

export function validateAddress(address: string) {
  if (!ethers.isAddress(address)) {
    throw new ValidationError("כתובת ארנק לא תקינה.");
  }
}

export async function getBalance(address: string): Promise<string> {
  try {
    validateAddress(address);
    const balance = await provider.getBalance(address);
    return ethers.formatEther(balance);
  } catch (err) {
    logger.error({ err, address }, "Failed to fetch balance");
    if (err instanceof ValidationError) throw err;
    throw new AppError("שגיאה בקריאת היתרה מהבלוקצ'יין.", 502);
  }
}

export async function snapshotWalletBalance(walletId: number, address: string) {
  const balance = await getBalance(address);

  await prisma.walletBalanceSnapshot.create({
    data: {
      walletId,
      balance
    }
  });

  return balance;
}
