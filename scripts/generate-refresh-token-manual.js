const { google } = require("googleapis");
const readline = require("readline");

// OAuth 2.0 Credentials
// TODO: Replace with your own credentials from Google Cloud Console
const CLIENT_ID = "YOUR_CLIENT_ID_HERE";
const CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE";
const REDIRECT_URI = "http://localhost:3000"; // ใช้ redirect URI ที่ตั้งค่าไว้

// Google Ads API scope
const SCOPES = ["https://www.googleapis.com/auth/adwords"];

// สร้าง OAuth2 client
const oauth2Client = new google.auth.OAuth2(
  CLIENT_ID,
  CLIENT_SECRET,
  REDIRECT_URI
);

// สร้าง authorization URL
const authUrl = oauth2Client.generateAuthUrl({
  access_type: "offline",
  scope: SCOPES,
  prompt: "consent",
});

console.log("\n🔐 Google Ads API - Generate Refresh Token\n");
console.log("\n📋 ขั้นตอนที่ 1: เปิด URL นี้ในเบราว์เซอร์:\n");
console.log("\x1b[36m%s\x1b[0m", authUrl);
console.log("\n" + "-".repeat(70));
console.log("\n📋 ขั้นตอนที่ 2: Login และอนุญาตการเข้าถึง");
console.log(
  "📋 ขั้นตอนที่ 3: Browser จะ redirect ไป http://localhost:3000/?code=..."
);
console.log(
  "📋 ขั้นตอนที่ 4: คัดลอก 'code' จาก URL มาวางด้านล่าง (ตัวอย่าง: 4/0AanRRrt...)\n"
);
console.log("=".repeat(70));

// รับ authorization code จากผู้ใช้
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

rl.question("\n📝 วาง Authorization Code จาก URL ที่นี่: ", async (code) => {
  rl.close();

  // ลบช่องว่างและ newline ออก
  code = code.trim();

  try {
    console.log("\n⏳ กำลังแลก authorization code เป็น refresh token...\n");

    // แลก authorization code เป็น tokens
    const { tokens } = await oauth2Client.getToken(code);

    console.log("\n✅ สำเร็จ! ได้ Refresh Token แล้ว:\n");
    console.log("=".repeat(70));
    console.log("\n🔑 REFRESH TOKEN:");
    console.log("\x1b[32m%s\x1b[0m", tokens.refresh_token);
    console.log("\n" + "=".repeat(70));

    console.log("\n📋 นำค่าเหล่านี้ไปเพิ่มใน Environment Variables:\n");
    console.log("GOOGLE_ADS_CLIENT_ID=" + CLIENT_ID);
    console.log("GOOGLE_ADS_CLIENT_SECRET=" + CLIENT_SECRET);
    console.log("GOOGLE_ADS_REFRESH_TOKEN=" + tokens.refresh_token);
    console.log("\n✅ เสร็จสิ้น! คุณสามารถใช้ Refresh Token นี้ได้แล้ว\n");
  } catch (error) {
    console.error("\n❌ เกิดข้อผิดพลาด:", error.message);
    console.error("\n💡 ตรวจสอบว่า:");
    console.error("   1. Authorization code ถูกต้องหรือไม่");
    console.error("   2. Code ยังไม่หมดอายุ (ใช้ได้แค่ครั้งเดียว)");
    console.error("   3. CLIENT_ID และ CLIENT_SECRET ถูกต้องหรือไม่");
    console.error("\n   ลองสร้าง code ใหม่แล้วรันอีกครั้ง\n");
  }
});
