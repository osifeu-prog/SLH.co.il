import { ethers } from "ethers";
import { CONFIG } from "./config";

const provider = new ethers.JsonRpcProvider(CONFIG.rpcUrl);

export async function getBalance(address: string) {
  const balance = await provider.getBalance(address);
  return ethers.formatEther(balance);
}
