import NextAuth from "next-auth";

export const oidcConfigured = Boolean(
  process.env.AUTH_SECRET &&
  process.env.AUTH_OIDC_ISSUER &&
  process.env.AUTH_OIDC_CLIENT_ID &&
  process.env.AUTH_OIDC_CLIENT_SECRET &&
  process.env.AUTH_OIDC_SCOPES &&
  process.env.AUTH_OIDC_TOKEN_ENDPOINT &&
  process.env.AUTH_URL &&
  process.env.AUTH_URL.startsWith("https://")
);

const providers = oidcConfigured ? [{
  id: "lhfm-oidc",
  name: "Unternehmenskonto",
  type: "oidc" as const,
  issuer: process.env.AUTH_OIDC_ISSUER!,
  clientId: process.env.AUTH_OIDC_CLIENT_ID!,
  clientSecret: process.env.AUTH_OIDC_CLIENT_SECRET!,
  authorization: { params: { scope: process.env.AUTH_OIDC_SCOPES! } },
  checks: ["pkce", "state"] as ("pkce" | "state")[],
}] : [];

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers,
  session: { strategy: "jwt", maxAge: 3600 },
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        // A real, renewable confidential-client credential is mandatory.
        if (!account.access_token || !account.expires_at || !account.refresh_token) {
          throw new TypeError("OIDC provider must return renewable API credentials");
        }
        // All three values stay inside the encrypted HttpOnly Auth.js cookie.
        // Never include them in the browser-visible session callback.
        token.apiAccessToken = account.access_token;
        token.apiExpiresAt = account.expires_at;
        token.apiRefreshToken = account.refresh_token;
      }
      return token;
    },
    async session({ session }) {
      // Deliberately NOT adding the access token or backend scope to client session.
      return session;
    },
  },
});
