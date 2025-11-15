/**
 * Generate Google Ads API Refresh Token
 *
 * This script helps you generate a refresh token for Google Ads API access.
 *
 * Prerequisites:
 * 1. Google Cloud Project with Google Ads API enabled
 * 2. OAuth 2.0 Client ID credentials
 *
 * Usage:
 *   node scripts/generate-google-ads-refresh-token.js
 */

const readline = require("readline");
const { OAuth2Client } = require("google-auth-library");

// Configuration - Replace with your OAuth credentials
// TODO: Replace with your own credentials from Google Cloud Console
const CLIENT_ID = "YOUR_CLIENT_ID_HERE";
const CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE";
const REDIRECT_URI = "http://localhost:3000/oauth2callback";

// Scopes for Google Ads API
const SCOPES = ["https://www.googleapis.com/auth/adwords"];

const oauth2Client = new OAuth2Client(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);

// Step 1: Generate authorization URL
const authUrl = oauth2Client.generateAuthUrl({
  access_type: "offline",
  scope: SCOPES,
  prompt: "consent",
});

console.log("\n" + "=".repeat(70));
console.log("📊 Google Ads API - Refresh Token Generator");
console.log("=".repeat(70));
console.log("\n🔹 Step 1: Authorize this app");
console.log("\nOpen this URL in your browser:\n");
console.log(authUrl);
console.log("\n" + "-".repeat(70));

// Step 2: Get authorization code from user
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

rl.question(
  "\n🔹 Step 2: Enter the authorization code from the redirect URL: ",
  async (code) => {
    try {
      // Exchange authorization code for tokens
      const { tokens } = await oauth2Client.getToken(code);

      console.log("\n" + "=".repeat(70));
      console.log("✅ Success! Your tokens:");
      console.log("=".repeat(70));
      console.log("\n📝 Refresh Token (save this in your .env file):");
      console.log("-".repeat(70));
      console.log(tokens.refresh_token);
      console.log("-".repeat(70));

      if (tokens.access_token) {
        console.log("\n📝 Access Token (temporary, expires in 1 hour):");
        console.log("-".repeat(70));
        console.log(tokens.access_token);
        console.log("-".repeat(70));
      }

      console.log("\n💡 Add this to your .env file:");
      console.log("=".repeat(70));
      console.log(`GOOGLE_ADS_REFRESH_TOKEN=${tokens.refresh_token}`);
      console.log("=".repeat(70));
      console.log("\n✅ Done!\n");
    } catch (error) {
      console.error("\n❌ Error getting tokens:", error.message);
    } finally {
      rl.close();
    }
  }
);
