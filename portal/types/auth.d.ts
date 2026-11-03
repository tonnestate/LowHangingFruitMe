import "next-auth/jwt";

declare module "next-auth/jwt" {
  interface JWT {
    apiAccessToken?: string;
    apiExpiresAt?: number;
  }
}
