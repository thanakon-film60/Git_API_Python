@echo off
echo.
echo ======================================================================
echo Google Ads API - Generate Refresh Token
echo ======================================================================
echo.
echo Step 1: Open this URL in your browser:
echo.
echo TODO: Replace YOUR_CLIENT_ID and YOUR_CLIENT_SECRET with your actual credentials
echo https://accounts.google.com/o/oauth2/v2/auth?access_type=offline^&scope=https://www.googleapis.com/auth/adwords^&prompt=consent^&response_type=code^&client_id=YOUR_CLIENT_ID^&redirect_uri=http://localhost:3000/oauth2callback
echo.
echo ----------------------------------------------------------------------
echo.
echo Step 2: After authorization, copy the 'code' from the URL
echo         Example: http://localhost:3000/oauth2callback?code=4/xxxxx
echo         Copy only the part after 'code='
echo.
set /p AUTH_CODE="Paste the authorization code here: "
echo.
echo Generating tokens...
echo.

node -e "const {OAuth2Client}=require('google-auth-library');const c=new OAuth2Client('YOUR_CLIENT_ID','YOUR_CLIENT_SECRET','http://localhost:3000/oauth2callback');c.getToken('%AUTH_CODE%').then(r=>{console.log('\n======================================');console.log('Refresh Token:');console.log('======================================');console.log(r.tokens.refresh_token);console.log('======================================\n');console.log('Add this to your .env file:');console.log('GOOGLE_ADS_REFRESH_TOKEN='+r.tokens.refresh_token);console.log('\n');}).catch(e=>{console.error('Error:',e.message)});"

echo.
pause
