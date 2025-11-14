"""
Example usage of Facebook Ads Manager API

This script demonstrates how to use all three API endpoints:
1. Facebook Ads Campaigns API
2. Google Sheets Data API
3. Google Ads API
"""

import requests
import json
from datetime import datetime, timedelta


class AdsManagerClient:
    """Client for Facebook Ads Manager API"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def fetch_facebook_ads(self, level="ad", date_preset="today", time_range=None, time_increment=None):
        """
        Fetch Facebook Ads data
        
        Args:
            level: "campaign" | "adset" | "ad"
            date_preset: "today" | "yesterday" | "last_7d" | "last_30d" | "this_month" | "last_month"
            time_range: {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
            time_increment: "1" for daily breakdown
        """
        url = f"{self.base_url}/api/facebook-ads-campaigns"
        
        params = {
            "level": level,
            "action_breakdowns": "action_type"
        }
        
        if time_range:
            params["time_range"] = json.dumps(time_range)
        else:
            params["date_preset"] = date_preset
        
        if time_increment:
            params["time_increment"] = time_increment
        
        # Add filtering for specific actions
        filtering = [
            {
                "field": "action_type",
                "operator": "IN",
                "value": [
                    "onsite_conversion.messaging_first_reply",
                    "onsite_conversion.total_messaging_connection"
                ]
            }
        ]
        params["filtering"] = json.dumps(filtering)
        
        response = requests.get(url, params=params)
        return response.json()
    
    def fetch_google_sheets(self, date_preset="today", time_range=None, daily=False):
        """
        Fetch Google Sheets data
        
        Args:
            date_preset: "today" | "yesterday" | "last_7d" | "last_30d" | "this_month" | "last_month"
            time_range: {"since": "YYYY-MM-DD", "until": "YYYY-MM-DD"}
            daily: True for daily breakdown
        """
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
        """
        Fetch Google Ads data
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            daily: True for daily breakdown
        """
        url = f"{self.base_url}/api/google-ads"
        
        params = {
            "startDate": start_date,
            "endDate": end_date
        }
        
        if daily:
            params["daily"] = "true"
        
        response = requests.get(url, params=params)
        return response.json()
    
    def get_daily_report(self, days=30):
        """Get daily report for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        since = start_date.strftime("%Y-%m-%d")
        until = end_date.strftime("%Y-%m-%d")
        
        print(f"🔍 Fetching data from {since} to {until}...")
        
        # Fetch data from all 3 sources
        fb_result = self.fetch_facebook_ads(
            level="campaign",
            time_range={"since": since, "until": until},
            time_increment="1"
        )
        
        sheets_result = self.fetch_google_sheets(
            time_range={"since": since, "until": until},
            daily=True
        )
        
        ads_result = self.fetch_google_ads(
            start_date=since,
            end_date=until,
            daily=True
        )
        
        # Combine data by date
        daily_data = {}
        
        # Process Facebook Ads data
        if fb_result.get('success'):
            for item in fb_result.get('data', []):
                date = item['date_start']
                if date not in daily_data:
                    daily_data[date] = {
                        'date': date,
                        'spend': 0,
                        'clicks': 0,
                        'impressions': 0,
                        'messaging_first_reply': 0,
                        'messaging_connection': 0,
                        'google_sheets': 0,
                        'google_ads': 0
                    }
                
                daily_data[date]['spend'] += float(item.get('spend', 0))
                daily_data[date]['clicks'] += int(item.get('clicks', 0))
                daily_data[date]['impressions'] += int(item.get('impressions', 0))
                
                if item.get('actions'):
                    for action in item['actions']:
                        if action['action_type'] == 'onsite_conversion.messaging_first_reply':
                            daily_data[date]['messaging_first_reply'] += int(action['value'])
                        elif action['action_type'] == 'onsite_conversion.total_messaging_connection':
                            daily_data[date]['messaging_connection'] += int(action['value'])
        
        # Process Google Sheets data
        if sheets_result.get('success'):
            for item in sheets_result.get('dailyData', []):
                date = item['date']
                if date in daily_data:
                    daily_data[date]['google_sheets'] = item['count']
        
        # Process Google Ads data
        if ads_result.get('success'):
            for item in ads_result.get('dailyData', []):
                date = item['date']
                if date in daily_data:
                    daily_data[date]['google_ads'] = item['clicks']
        
        # Convert to sorted list
        daily_list = sorted(daily_data.values(), key=lambda x: x['date'], reverse=True)
        
        return daily_list
    
    def get_summary(self, date_preset="today"):
        """Get summary for a specific date preset"""
        print(f"📊 Fetching summary for {date_preset}...")
        
        # Fetch Facebook Ads
        fb_result = self.fetch_facebook_ads(level="ad", date_preset=date_preset)
        
        # Calculate summary
        total_spend = fb_result.get('summary', {}).get('total_spend', 0)
        total_messaging_first_reply = 0
        total_messaging_connection = 0
        
        for item in fb_result.get('data', []):
            if item.get('actions'):
                for action in item['actions']:
                    if action['action_type'] == 'onsite_conversion.messaging_first_reply':
                        total_messaging_first_reply += int(action['value'])
                    elif action['action_type'] == 'onsite_conversion.total_messaging_connection':
                        total_messaging_connection += int(action['value'])
        
        # Fetch Google Sheets
        sheets_result = self.fetch_google_sheets(date_preset=date_preset)
        google_sheets_total = sheets_result.get('total', 0)
        
        # Fetch Google Ads
        today = datetime.now().strftime("%Y-%m-%d")
        ads_result = self.fetch_google_ads(start_date=today, end_date=today)
        google_ads_clicks = ads_result.get('summary', {}).get('totalClicks', 0)
        
        return {
            'total_spend': total_spend,
            'messaging_first_reply': total_messaging_first_reply,
            'messaging_connection': total_messaging_connection,
            'google_sheets': google_sheets_total,
            'google_ads_clicks': google_ads_clicks
        }


def main():
    """Main function to demonstrate API usage"""
    
    # Initialize client (change base_url for production)
    client = AdsManagerClient(base_url="http://localhost:5000")
    # For production: client = AdsManagerClient(base_url="https://believable-ambition-production.up.railway.app")
    
    print("\n" + "="*70)
    print("📊 Facebook Ads Manager API - Example Usage")
    print("="*70)
    
    # Example 1: Get today's summary
    print("\n1️⃣  Today's Summary")
    print("-" * 70)
    try:
        summary = client.get_summary(date_preset="today")
        print(f"💰 Total Spend: ฿{summary['total_spend']:,.2f}")
        print(f"💬 Messaging First Reply: {summary['messaging_first_reply']}")
        print(f"📨 Messaging Connection: {summary['messaging_connection']}")
        print(f"📊 Google Sheets Leads: {summary['google_sheets']}")
        print(f"🎯 Google Ads Clicks: {summary['google_ads_clicks']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 2: Get Facebook Ads data
    print("\n2️⃣  Facebook Ads (Campaign Level - Today)")
    print("-" * 70)
    try:
        fb_data = client.fetch_facebook_ads(level="campaign", date_preset="today")
        if fb_data.get('success'):
            print(f"Found {len(fb_data.get('data', []))} campaigns")
            for campaign in fb_data.get('data', [])[:3]:  # Show first 3
                print(f"  📢 {campaign.get('campaign_name')}")
                print(f"     Spend: ฿{float(campaign.get('spend', 0)):,.2f}")
                print(f"     Clicks: {campaign.get('clicks')}")
        else:
            print(f"❌ Error: {fb_data.get('error')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 3: Get Google Sheets data
    print("\n3️⃣  Google Sheets Data (Today)")
    print("-" * 70)
    try:
        sheets_data = client.fetch_google_sheets(date_preset="today")
        if sheets_data.get('success'):
            print(f"Total leads: {sheets_data.get('total', 0)}")
            print(f"Date range: {sheets_data.get('dateRange')}")
        else:
            print(f"❌ Error: {sheets_data.get('error')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 4: Get Google Ads data
    print("\n4️⃣  Google Ads Data (Today)")
    print("-" * 70)
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        ads_data = client.fetch_google_ads(start_date=today, end_date=today)
        if 'campaigns' in ads_data:
            print(f"Found {len(ads_data.get('campaigns', []))} campaigns")
            summary = ads_data.get('summary', {})
            print(f"Total Clicks: {summary.get('totalClicks', 0)}")
            print(f"Total Cost: ฿{summary.get('totalCost', 0):,.2f}")
        else:
            print(f"❌ Error: {ads_data.get('error')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 5: Get daily report (last 7 days)
    print("\n5️⃣  Daily Report (Last 7 Days)")
    print("-" * 70)
    try:
        daily_report = client.get_daily_report(days=7)
        print(f"Found data for {len(daily_report)} days\n")
        
        for day in daily_report[:5]:  # Show first 5 days
            print(f"📅 {day['date']}")
            print(f"   💰 Spend: ฿{day['spend']:,.2f}")
            print(f"   💬 First Reply: {day['messaging_first_reply']}")
            print(f"   📨 Connection: {day['messaging_connection']}")
            print(f"   📊 Sheets: {day['google_sheets']}")
            print(f"   🎯 Ads: {day['google_ads']}")
            print()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("="*70)
    print("✅ Example completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
