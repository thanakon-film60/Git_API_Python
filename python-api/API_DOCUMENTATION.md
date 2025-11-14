# 📊 Facebook Ads Manager API Documentation

This API provides endpoints for fetching data from Facebook Ads, Google Sheets, and Google Ads.

## Base URL

```
https://believable-ambition-production.up.railway.app
```

---

## 🎯 API Endpoints

### 1. Facebook Ads Campaigns API

**Endpoint:** `GET /api/facebook-ads-campaigns`

**Description:** Fetch Facebook Ads Insights data with support for different levels (campaign, adset, ad) and date ranges.

**Query Parameters:**

| Parameter           | Type        | Required | Default         | Description                                                                                            |
| ------------------- | ----------- | -------- | --------------- | ------------------------------------------------------------------------------------------------------ |
| `level`             | string      | No       | `"ad"`          | Level of data: `"campaign"`, `"adset"`, or `"ad"`                                                      |
| `date_preset`       | string      | No       | `"today"`       | Preset date range: `"today"`, `"yesterday"`, `"last_7d"`, `"last_30d"`, `"this_month"`, `"last_month"` |
| `time_range`        | JSON string | No       | -               | Custom date range: `{"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}`                                    |
| `action_breakdowns` | string      | No       | `"action_type"` | Action breakdown type                                                                                  |
| `filtering`         | JSON string | No       | -               | Filter criteria for actions                                                                            |
| `time_increment`    | string      | No       | -               | Set to `"1"` for daily breakdown                                                                       |

**Example Requests:**

```bash
# Get today's ad-level data
GET /api/facebook-ads-campaigns?level=ad&date_preset=today

# Get campaign-level data for last 30 days
GET /api/facebook-ads-campaigns?level=campaign&date_preset=last_30d

# Get daily breakdown with custom date range
GET /api/facebook-ads-campaigns?level=campaign&time_range={"since":"2025-10-15","until":"2025-11-14"}&time_increment=1

# Filter specific action types
GET /api/facebook-ads-campaigns?level=ad&date_preset=today&filtering=[{"field":"action_type","operator":"IN","value":["onsite_conversion.messaging_first_reply","onsite_conversion.total_messaging_connection"]}]
```

**Response Example:**

```json
{
  "success": true,
  "level": "ad",
  "date_preset": "today",
  "time_range": {
    "since": "2025-11-14",
    "until": "2025-11-14"
  },
  "data": [
    {
      "ad_id": "123456789",
      "ad_name": "โฆษณา A",
      "adset_id": "987654321",
      "adset_name": "ชุดโฆษณา A",
      "campaign_id": "111222333",
      "campaign_name": "แคมเปญ A",
      "spend": "1500.50",
      "impressions": "50000",
      "clicks": "1250",
      "ctr": "2.5",
      "cpc": "1.20",
      "cpm": "30.01",
      "actions": [
        {
          "action_type": "onsite_conversion.messaging_first_reply",
          "value": "45"
        },
        {
          "action_type": "onsite_conversion.total_messaging_connection",
          "value": "67"
        }
      ],
      "date_start": "2025-11-14",
      "date_stop": "2025-11-14",
      "reach": "30000",
      "frequency": "1.67"
    }
  ],
  "summary": {
    "total_spend": 1500.5,
    "total_impressions": 50000,
    "total_reach": 30000,
    "total_clicks": 1250,
    "total_results": 112
  },
  "paging": null,
  "timestamp": "2025-11-14T10:30:00"
}
```

---

### 2. Google Sheets Data API

**Endpoint:** `GET /api/google-sheets-data`

**Description:** Fetch data from Google Sheets "เคสได้ชื่อเบอร์" sheet with date filtering.

**Query Parameters:**

| Parameter     | Type        | Required | Default   | Description                                                                                            |
| ------------- | ----------- | -------- | --------- | ------------------------------------------------------------------------------------------------------ |
| `date_preset` | string      | No       | `"today"` | Preset date range: `"today"`, `"yesterday"`, `"last_7d"`, `"last_30d"`, `"this_month"`, `"last_month"` |
| `time_range`  | JSON string | No       | -         | Custom date range: `{"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}`                                    |
| `daily`       | string      | No       | `"false"` | Set to `"true"` for daily breakdown                                                                    |

**Example Requests:**

```bash
# Get today's data
GET /api/google-sheets-data?date_preset=today

# Get last 30 days data
GET /api/google-sheets-data?date_preset=last_30d

# Get daily breakdown with custom date range
GET /api/google-sheets-data?time_range={"since":"2025-10-15","until":"2025-11-14"}&daily=true
```

**Response Example (Standard):**

```json
{
  "success": true,
  "total": 150,
  "dateRange": {
    "start": "2025-11-14",
    "end": "2025-11-14"
  },
  "dateColIndex": 0,
  "hasDateColumn": true,
  "totalRowsBeforeFilter": 500,
  "rowsAfterDateFilter": 150,
  "data": [
    {
      "date": "14/11/2025",
      "namePhone": "ชื่อลูกค้า + เบอร์โทร"
    }
  ],
  "timestamp": "2025-11-14T10:30:00"
}
```

**Response Example (Daily Mode):**

```json
{
  "success": true,
  "dailyData": [
    {
      "date": "2025-11-14",
      "count": 25
    },
    {
      "date": "2025-11-13",
      "count": 18
    }
  ],
  "total": 150,
  "dateRange": {
    "start": "2025-10-15",
    "end": "2025-11-14"
  },
  "timestamp": "2025-11-14T10:30:00"
}
```

---

### 3. Google Ads API

**Endpoint:** `GET /api/google-ads`

**Description:** Fetch Google Ads campaigns data with metrics like clicks, impressions, cost, etc.

**Query Parameters:**

| Parameter   | Type   | Required | Default   | Description                         |
| ----------- | ------ | -------- | --------- | ----------------------------------- |
| `startDate` | string | No       | Today     | Start date in YYYY-MM-DD format     |
| `endDate`   | string | No       | Today     | End date in YYYY-MM-DD format       |
| `daily`     | string | No       | `"false"` | Set to `"true"` for daily breakdown |

**Example Requests:**

```bash
# Get today's data
GET /api/google-ads?startDate=2025-11-14&endDate=2025-11-14

# Get last 30 days data
GET /api/google-ads?startDate=2025-10-15&endDate=2025-11-14

# Get daily breakdown
GET /api/google-ads?startDate=2025-10-15&endDate=2025-11-14&daily=true
```

**Response Example (Standard):**

```json
{
  "campaigns": [
    {
      "id": "1",
      "name": "Campaign A",
      "status": "ENABLED",
      "clicks": 1250,
      "impressions": 45000,
      "averageCpc": 8.5,
      "cost": 10625.0,
      "ctr": 2.78,
      "conversions": 45
    }
  ],
  "summary": {
    "totalClicks": 1250,
    "totalImpressions": 45000,
    "averageCpc": 8.5,
    "totalCost": 10625.0,
    "averageCtr": 2.78
  },
  "dateRange": {
    "startDate": "2025-11-14",
    "endDate": "2025-11-14"
  },
  "timestamp": "2025-11-14T10:30:00"
}
```

**Response Example (Daily Mode):**

```json
{
  "success": true,
  "dailyData": [
    {
      "date": "2025-11-14",
      "clicks": 125,
      "impressions": 5000,
      "cost": 1062.5,
      "conversions": 5
    },
    {
      "date": "2025-11-13",
      "clicks": 98,
      "impressions": 4200,
      "cost": 833.0,
      "conversions": 4
    }
  ],
  "dateRange": {
    "startDate": "2025-10-15",
    "endDate": "2025-11-14"
  },
  "timestamp": "2025-11-14T10:30:00"
}
```

---

## 🔐 Environment Variables Required

Create a `.env` file based on `.env.example` with these variables:

### Facebook Ads API

```env
FACEBOOK_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxx
FACEBOOK_AD_ACCOUNT_ID=act_1234567890
```

### Google Sheets API (Service Account)

```env
GOOGLE_SHEET_ID=1abcdefghijklmnop
GOOGLE_SA_CLIENT_EMAIL=your-service-account@project-id.iam.gserviceaccount.com
GOOGLE_SA_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\nxxxxxxx\n-----END PRIVATE KEY-----
```

### Google Ads API

```env
GOOGLE_ADS_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=GOCSPX-xxxxx
GOOGLE_ADS_DEVELOPER_TOKEN=xxxxx
GOOGLE_ADS_REFRESH_TOKEN=1//xxxxx
GOOGLE_ADS_CUSTOMER_ID=1234567890
```

---

## 🐍 Python Client Example

```python
import requests
import json
from datetime import datetime, timedelta

class AdsManagerClient:
    def __init__(self, base_url="https://believable-ambition-production.up.railway.app"):
        self.base_url = base_url

    def fetch_facebook_ads(self, level="ad", date_preset="today", time_range=None):
        """Fetch Facebook Ads data"""
        url = f"{self.base_url}/api/facebook-ads-campaigns"

        params = {
            "level": level,
            "action_breakdowns": "action_type"
        }

        if time_range:
            params["time_range"] = json.dumps(time_range)
        else:
            params["date_preset"] = date_preset

        response = requests.get(url, params=params)
        return response.json()

    def fetch_google_sheets(self, date_preset="today", time_range=None, daily=False):
        """Fetch Google Sheets data"""
        url = f"{self.base_url}/api/google-sheets-data"

        params = {}
        if daily:
            params["daily"] = "true"

        if time_range:
            params["time_range"] = json.dumps(time_range)
        else:
            params["date_preset"] = date_preset

        response = requests.get(url, params=params)
        return response.json()

    def fetch_google_ads(self, start_date, end_date, daily=False):
        """Fetch Google Ads data"""
        url = f"{self.base_url}/api/google-ads"

        params = {
            "startDate": start_date,
            "endDate": end_date
        }

        if daily:
            params["daily"] = "true"

        response = requests.get(url, params=params)
        return response.json()

# Usage example
client = AdsManagerClient()

# Get today's summary
fb_data = client.fetch_facebook_ads(level="campaign", date_preset="today")
sheets_data = client.fetch_google_sheets(date_preset="today")
ads_data = client.fetch_google_ads(
    start_date=datetime.now().strftime("%Y-%m-%d"),
    end_date=datetime.now().strftime("%Y-%m-%d")
)

print(f"Facebook Spend: {fb_data['summary']['total_spend']}")
print(f"Google Sheets Leads: {sheets_data['total']}")
print(f"Google Ads Clicks: {ads_data['summary']['totalClicks']}")
```

---

## 📝 Notes

1. **Facebook Ads API**

   - Requires Long-lived Access Token
   - Ad Account ID must start with `act_`
   - Rate limit: 200 calls/hour (Standard Access)

2. **Google Sheets API**

   - Uses Service Account authentication
   - Sheet must be shared with Service Account email
   - Sheet name must be "เคสได้ชื่อเบอร์"
   - Column A must contain dates

3. **Google Ads API**
   - Requires Developer Token (1-3 days approval)
   - Customer ID must be Client Account (not Manager Account)
   - Test Access quota: 15,000 operations/day

---

## 🚀 Deployment

The API is deployed on Railway:

```
https://believable-ambition-production.up.railway.app
```

To test if API is running:

```bash
curl https://believable-ambition-production.up.railway.app/health
```

---

## 📚 Additional Resources

- [Facebook Marketing API Documentation](https://developers.facebook.com/docs/marketing-apis)
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Ads API Documentation](https://developers.google.com/google-ads/api)
