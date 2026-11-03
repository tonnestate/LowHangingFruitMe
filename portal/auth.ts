import NextAuth from "next-auth";

export const oidcConfigured = Boolean(
  process.env.AUTH_SECRET &&
  process.env.AUTH_OIDC_ISSUER &&
  process.env.AUTH_OIDC_CLIENT_ID &&
  process.env.AUTH_OIDC_CLIENT_SECRET &&
  process.env.AUTH_OIDC_SCOPES
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
        // Stored ONLY in Auth.js encrypted JWT cookie, never in session JSON.
        token.apiAccessToken = account.access_token ?? undefined;
        token.apiExpiresAt = account.expires_at ?? 0;
      }
      return token;
    },
    async session({ session }) {
      // Deliberately NOT adding the access token or backend scope to client session.
      return session;
    },
  },
});
