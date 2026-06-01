# Facebook Wall → SLH Community Feed Integration Plan

## Goal
Pull posts from Osif's Facebook wall (https://www.facebook.com/osif.e.ungar/)
and display them in the SLH community feed on slh-nft.com/community.html.

## Prerequisites (User Action Required)
1. Go to https://developers.facebook.com/
2. Create a new App (type: Business)
3. Get the App ID and App Secret
4. Generate a **Page Access Token** (long-lived, 60-day)
5. Or use **User Access Token** with `user_posts` permission

## Technical Implementation

### Option A: Server-Side (Recommended - via API)
```
API endpoint: GET /api/facebook/feed
- Fetches from Graph API: https://graph.facebook.com/v19.0/me/posts
- Params: access_token, fields=message,created_time,full_picture,permalink_url
- Caches results in Redis (5-minute TTL)
- Returns formatted posts for frontend
```

### Option B: Client-Side (Simpler but limited)
```
Use Facebook Page Plugin (iframe embed):
<div class="fb-page" 
     data-href="https://www.facebook.com/osif.e.ungar/"
     data-tabs="timeline"
     data-width="500">
</div>
```

### API Implementation (main.py)
```python
@app.get("/api/facebook/feed")
async def get_facebook_feed(limit: int = 10):
    # Check Redis cache first
    cached = await redis.get("fb_feed_cache")
    if cached:
        return json.loads(cached)
    
    # Fetch from Graph API
    url = f"https://graph.facebook.com/v19.0/me/posts"
    params = {
        "access_token": FB_ACCESS_TOKEN,
        "fields": "message,created_time,full_picture,permalink_url,type",
        "limit": limit
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
    
    # Cache for 5 minutes
    await redis.set("fb_feed_cache", json.dumps(data), ex=300)
    return data
```

### Frontend (community.html)
```
Community page gets new tab: "Facebook Feed"
- Shows posts in card layout matching existing design
- Each card: image, text preview, date, "Read on Facebook" link
- Auto-refreshes every 5 minutes
- Hebrew RTL layout
```

### Files to Modify
- `api/main.py` - Add /api/facebook/feed endpoint
- `website/community.html` - Add Facebook feed tab
- `website/js/shared.js` - Add Facebook feed fetch function
- `.env` - Add FB_APP_ID, FB_APP_SECRET, FB_ACCESS_TOKEN

### Security Notes
- NEVER store Facebook password in code or .env
- Use OAuth tokens only (expire, can be revoked)
- Token refresh: Long-lived tokens last 60 days, set up auto-refresh
- Rate limit: 200 calls/hour for User tokens
