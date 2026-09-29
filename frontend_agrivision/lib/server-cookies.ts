import { cookies } from "next/headers";

export async function getCookieHeader(): Promise<string> {
  const cookieStore = await cookies();
  const pairs = cookieStore.getAll().map((cookie) => `${cookie.name}=${cookie.value}`);
  return pairs.join("; ");
}