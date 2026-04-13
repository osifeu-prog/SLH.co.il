"""
SLH API Health Check — Automated endpoint testing
Run: python ops/api-health-check.py
Output: ops/API_STATUS_{date}.md
"""
import urllib.request, json, time, datetime, os

API = 'https://slh-api-production.up.railway.app'
USER_ID = '224223270'
ADMIN_KEY = 'slh2026admin'
DATE = datetime.datetime.now().strftime('%Y%m%d')
OUT = f'ops/API_STATUS_{DATE}.md'

def test(method, path, auth=False, expect=200):
    url = API + path
    try:
        headers = {'X-Admin-Key': ADMIN_KEY} if auth else {}
        req = urllib.request.Request(url, headers=headers)
        t0 = time.time()
        resp = urllib.request.urlopen(req, timeout=10)
        ms = int((time.time()-t0)*1000)
        body = resp.read().decode('utf-8','replace')[:100]
        return {'status': resp.getcode(), 'ms': ms, 'ok': True, 'preview': body.encode('ascii','replace').decode('ascii')[:60]}
    except urllib.error.HTTPError as e:
        return {'status': e.code, 'ms': 0, 'ok': False, 'preview': ''}
    except Exception as e:
        return {'status': 0, 'ms': 0, 'ok': False, 'preview': str(e)[:60]}

# Define all testable endpoints
tests = [
    # Core
    ('GET', '/api/health', False, 'System health'),
    ('GET', '/api/stats', False, 'Global stats'),
    ('GET', '/api/prices', False, 'Live crypto prices'),
    # Admin
    ('GET', '/api/admin/dashboard', True, 'Admin dashboard'),
    ('GET', '/api/admin/all-users', True, 'All users + balances'),
    ('GET', '/api/admin/activity', True, 'Recent activity'),
    # User-specific
    ('GET', f'/api/user/{USER_ID}', False, 'User profile'),
    ('GET', f'/api/wallet/{USER_ID}', False, 'Wallet info'),
    ('GET', f'/api/wallet/{USER_ID}/balances', False, 'Token balances'),
    ('GET', f'/api/referral/stats/{USER_ID}', False, 'Referral stats'),
    ('GET', f'/api/staking/positions/{USER_ID}', False, 'Staking positions'),
    ('GET', f'/api/member-card/{USER_ID}', False, 'Member card'),
    ('GET', f'/api/guardian/check/{USER_ID}', False, 'Guardian check'),
    # Launch
    ('GET', '/api/launch/status', False, 'Genesis launch status'),
    ('GET', '/api/beta/status', False, 'Beta/coupon status'),
    # Community
    ('GET', '/api/community/posts', False, 'Community posts'),
    ('GET', '/api/community/stats', False, 'Community stats'),
    ('GET', '/api/community/health', False, 'Community health'),
    # Guardian
    ('GET', '/api/guardian/stats', False, 'Guardian ZUZ stats'),
    ('GET', '/api/guardian/blacklist', True, 'Blacklist'),
    # Tokenomics
    ('GET', '/api/tokenomics/stats', False, 'Token supply/burns'),
    ('GET', '/api/wallet/price', False, 'SLH price'),
    ('GET', '/api/staking/plans', False, 'Staking APY plans'),
    # Marketplace
    ('GET', '/api/marketplace/items', False, 'Marketplace listings'),
    ('GET', '/api/marketplace/stats', False, 'Marketplace overview'),
    ('GET', '/api/p2p/orders', False, 'P2P orders v1'),
    ('GET', '/api/p2p/v2/orders', False, 'P2P orders v2'),
    # Network
    ('GET', '/api/network/slh-holders', False, 'Token holders'),
    ('GET', '/api/leaderboard', False, 'XP leaderboard'),
    ('GET', '/api/referral/leaderboard', False, 'Referral leaderboard'),
    ('GET', '/api/shares/stats', False, 'Share tracking'),
    ('GET', '/api/member-cards/all', False, 'All member cards'),
    # Audit
    ('GET', '/api/audit/verify-chain', False, 'Audit chain verify'),
    ('GET', '/api/audit/recent', False, 'Recent audit entries'),
    ('GET', '/api/analytics/stats', False, 'Analytics'),
    ('GET', '/api/broadcast/history', False, 'Broadcast history'),
    # AI
    ('GET', '/api/ai/providers', False, 'AI providers'),
    ('GET', '/api/strategy/list', False, 'Trading strategies'),
    # Previously broken
    ('GET', '/api/registration/pending', False, 'Pending registrations'),
    ('GET', '/api/rep/leaderboard', False, 'REP leaderboard'),
    ('GET', '/api/marketplace/admin/pending', True, 'Admin pending items'),
]

print(f'Testing {len(tests)} endpoints...')
results = []
ok_count = 0
for method, path, auth, desc in tests:
    r = test(method, path, auth)
    icon = 'OK' if r['ok'] else str(r['status'])
    if r['ok']: ok_count += 1
    results.append((method, path, auth, desc, r))
    print(f"  {'OK' if r['ok'] else 'XX':3} {r['status']:3} {r['ms']:4}ms {path}")

# Write report
ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(f'# API Status Report — {ts}\n\n')
    f.write(f'**Total: {len(tests)} endpoints tested | {ok_count} OK | {len(tests)-ok_count} errors**\n\n')
    f.write('| # | Status | ms | Endpoint | Description |\n')
    f.write('|---|--------|-----|----------|-------------|\n')
    for i, (method, path, auth, desc, r) in enumerate(results, 1):
        s = 'OK' if r['ok'] else str(r['status'])
        lock = ' [AUTH]' if auth else ''
        f.write(f"| {i} | {s} | {r['ms']} | {path}{lock} | {desc} |\n")
    f.write(f'\n---\nGenerated: {ts}\n')

print(f'\nDone: {ok_count}/{len(tests)} OK. Report: {OUT}')
