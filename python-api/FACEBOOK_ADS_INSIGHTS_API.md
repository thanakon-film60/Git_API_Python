# Facebook Ads Insights API

## 📌 Overview

API endpoint สำหรับดึงข้อมูล Facebook Ads Insights โดยตรงจาก Graph API v24.0

## 🔗 Endpoint

```
GET /api/facebook-ads-insights
```

## ⚙️ Environment Variables ที่ต้องตั้งค่า

```env
FACEBOOK_ACCESS_TOKEN=EAAPb1ZBYCiNcBPzNxxSUntCZCT...  # Access Token จาก Facebook
FACEBOOK_AD_ACCOUNT_ID=act_1447972642723860           # Ad Account ID (ต้องมี prefix "act_")
```

## 📝 Query Parameters

| Parameter  | Type    | Default       | Description                                                                                                    |
| ---------- | ------- | ------------- | -------------------------------------------------------------------------------------------------------------- |
| `level`    | string  | `"ad"`        | ระดับของข้อมูล: `"ad"`, `"adset"`, `"campaign"`                                                                |
| `date`     | string  | `"yesterday"` | Date preset: `"today"`, `"yesterday"`, `"last_7d"`, `"last_14d"`, `"last_30d"`, `"this_month"`, `"last_month"` |
| `since`    | string  | -             | วันที่เริ่มต้น format `YYYY-MM-DD` (override date preset)                                                      |
| `until`    | string  | -             | วันที่สิ้นสุด format `YYYY-MM-DD` (ใช้คู่กับ since)                                                            |
| `fields`   | string  | -             | Fields ที่ต้องการ (comma-separated)                                                                            |
| `limit`    | integer | `500`         | จำนวน records สูงสุด                                                                                           |
| `no_cache` | string  | -             | ใส่ `"true"` เพื่อข้าม cache                                                                                   |

## 📊 Default Fields

### Level: `ad`

- `ad_id`, `ad_name`, `adset_id`, `adset_name`, `campaign_id`, `campaign_name`
- `spend`, `impressions`, `clicks`, `ctr`, `cpc`, `cpm`

### Level: `adset`

- `adset_id`, `adset_name`, `campaign_id`, `campaign_name`
- `spend`, `impressions`, `clicks`, `ctr`, `cpc`, `cpm`

### Level: `campaign`

- `campaign_id`, `campaign_name`
- `spend`, `impressions`, `clicks`, `ctr`, `cpc`, `cpm`

## 📖 Examples

### 1. ดึงข้อมูล Ad ของเมื่อวาน (Default)

```bash
curl "http://localhost:5000/api/facebook-ads-insights"
```

### 2. ดึงข้อมูล Campaign ของวันนี้

```bash
curl "http://localhost:5000/api/facebook-ads-insights?level=campaign&date=today"
```

### 3. ดึงข้อมูล Ad ของ 7 วันที่ผ่านมา

```bash
curl "http://localhost:5000/api/facebook-ads-insights?level=ad&date=last_7d"
```

### 4. ดึงข้อมูลตาม Custom Date Range

```bash
curl "http://localhost:5000/api/facebook-ads-insights?since=2025-11-01&until=2025-11-30"
```

### 5. ดึงเฉพาะ Fields ที่ต้องการ

```bash
curl "http://localhost:5000/api/facebook-ads-insights?fields=ad_id,ad_name,spend,impressions,clicks"
```

### 6. ข้าม Cache

```bash
curl "http://localhost:5000/api/facebook-ads-insights?date=today&no_cache=true"
```

## 📤 Response Format

```json
{
  "success": true,
  "api_version": "v24.0",
  "level": "ad",
  "date_type": "preset",
  "date_preset": "yesterday",
  "date_range": {
    "since": "2025-12-01",
    "until": "2025-12-01"
  },
  "fields": [
    "ad_id",
    "ad_name",
    "adset_id",
    "adset_name",
    "campaign_id",
    "campaign_name",
    "spend",
    "impressions",
    "clicks",
    "ctr",
    "cpc",
    "cpm"
  ],
  "data": [
    {
      "ad_id": "120232539320390180",
      "ad_name": "Test Ad 1",
      "adset_id": "120232539320380000",
      "adset_name": "Test Adset",
      "campaign_id": "120232539320370000",
      "campaign_name": "Test Campaign",
      "spend": "150.50",
      "impressions": "5000",
      "clicks": "250",
      "ctr": "5.00",
      "cpc": "0.60",
      "cpm": "30.10",
      "date_start": "2025-12-01",
      "date_stop": "2025-12-01"
    }
  ],
  "summary": {
    "total_spend": 150.5,
    "total_impressions": 5000,
    "total_clicks": 250,
    "average_ctr": 5.0,
    "average_cpc": 0.6,
    "average_cpm": 30.1
  },
  "total_records": 1,
  "paging": {},
  "timestamp": "2025-12-02T10:30:00.000000",
  "cached": false,
  "cache_duration": 300
}
```

## 🔑 Available Fields

| Field                        | Description                            |
| ---------------------------- | -------------------------------------- |
| `ad_id`                      | Ad ID                                  |
| `ad_name`                    | Ad Name                                |
| `adset_id`                   | Ad Set ID                              |
| `adset_name`                 | Ad Set Name                            |
| `campaign_id`                | Campaign ID                            |
| `campaign_name`              | Campaign Name                          |
| `spend`                      | Total Spend (THB)                      |
| `impressions`                | Total Impressions                      |
| `clicks`                     | Total Clicks                           |
| `ctr`                        | Click-Through Rate (%)                 |
| `cpc`                        | Cost Per Click (THB)                   |
| `cpm`                        | Cost Per 1000 Impressions (THB)        |
| `reach`                      | Unique Users Reached                   |
| `frequency`                  | Average Times Each User Saw Ad         |
| `actions`                    | Actions Taken (leads, purchases, etc.) |
| `cost_per_action_type`       | Cost Per Action Type                   |
| `conversions`                | Conversions Count                      |
| `video_p25_watched_actions`  | 25% Video Watched                      |
| `video_p50_watched_actions`  | 50% Video Watched                      |
| `video_p75_watched_actions`  | 75% Video Watched                      |
| `video_p100_watched_actions` | 100% Video Watched                     |

## ⚠️ Error Responses

### Missing Credentials

```json
{
  "success": false,
  "error": "Missing FACEBOOK_ACCESS_TOKEN environment variable",
  "data": [],
  "timestamp": "2025-12-02T10:30:00.000000"
}
```

### Invalid Level

```json
{
  "success": false,
  "error": "Invalid level. Must be one of: ['ad', 'adset', 'campaign']",
  "data": [],
  "timestamp": "2025-12-02T10:30:00.000000"
}
```

### Facebook API Error

```json
{
  "success": false,
  "error": "Error validating access token...",
  "error_code": 190,
  "data": [],
  "timestamp": "2025-12-02T10:30:00.000000"
}
```

## 🔄 Caching

- **Cache Duration**: 5 นาที (300 วินาที) - ปรับได้ใน `FB_ADS_CACHE_DURATION`
- **Cache Key**: ประกอบด้วย level, date range, fields, limit
- **Bypass Cache**: ใช้ `no_cache=true`

## 📱 Integration Example (JavaScript/React)

```javascript
// Fetch Facebook Ads Insights
async function fetchFacebookAdsInsights() {
  try {
    const response = await fetch(
      "/api/facebook-ads-insights?level=ad&date=yesterday"
    );
    const data = await response.json();

    if (data.success) {
      console.log("Total Spend:", data.summary.total_spend);
      console.log("Total Clicks:", data.summary.total_clicks);
      console.log("Ads:", data.data);
    } else {
      console.error("Error:", data.error);
    }
  } catch (error) {
    console.error("Fetch error:", error);
  }
}
```

## 🔗 Related Endpoints

| Endpoint                       | Description                              |
| ------------------------------ | ---------------------------------------- |
| `/api/facebook-ads-campaigns`  | Full Facebook Ads API with more features |
| `/api/facebook-graph-insights` | Graph API with video thumbnails          |
| `/api/facebook-videos-direct`  | Get video download URLs                  |

## 📋 Changelog

- **v1.0.0** (2025-12-02): Initial release
  - Basic insights fetching with Graph API v24.0
  - Support for ad, adset, campaign levels
  - Date presets and custom date ranges
  - Caching support
  - Summary calculations
