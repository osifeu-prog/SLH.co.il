import re

with open('D:/SLH_ECOSYSTEM/website/admin.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Verify base
assert 'checkAuth' in c
assert '</script>' in c
print(f'Base OK: {len(c)} chars')

# 1. Nav: Finance + Trust
c = c.replace(
    "onclick=\"refreshAll()\">",
    "onclick=\"showPage('finance')\">💰 Finance</a>\n        <a href=\"#\" onclick=\"showPage('trust')\">🌐 Trust Network</a>\n        <a href=\"#\" onclick=\"refreshAll()\">"
)

# 2. Page triggers
c = c.replace(
    "if (name === 'sitemap') checkAllPages();",
    "if (name === 'sitemap') checkAllPages();\n    if (name === 'finance') loadFinanceDashboard();\n    if (name === 'trust') loadTrustEntities();\n    if (name === 'users') loadFullUsers();"
)

# 3. Finance + Trust HTML
pages_html = '\n        <div id="page-finance" style="display:none"><div style="background:linear-gradient(135deg,rgba(255,215,0,.08),rgba(0,232,135,.04));border:1px solid var(--gold);padding:20px;margin-bottom:24px"><h2 style="color:var(--gold);font-size:18px">💰 Financial Dashboard</h2></div><div class="kpi-grid"><div class="kpi gold"><div class="kpi-label">Genesis</div><div class="kpi-value" id="fin-raised">--</div></div><div class="kpi green"><div class="kpi-label">Pool BNB</div><div class="kpi-value" id="fin-pool-bnb">--</div></div><div class="kpi cyan"><div class="kpi-label">SLH</div><div class="kpi-value" id="fin-slh-db">--</div></div><div class="kpi purple"><div class="kpi-label">ZVK</div><div class="kpi-value" id="fin-zvk">--</div></div></div></div>\n        <div id="page-trust" style="display:none"><div style="background:linear-gradient(135deg,rgba(0,229,255,.08),rgba(168,85,247,.04));border:1px solid var(--cyan);padding:20px;margin-bottom:24px"><h2 style="color:var(--cyan);font-size:18px">🌐 Trust Network</h2></div><div class="kpi-grid"><div class="kpi green"><div class="kpi-label">Trust</div><div class="kpi-value" id="gtn-trust">100</div></div><div class="kpi red"><div class="kpi-label">Flagged</div><div class="kpi-value" id="gtn-flagged">0</div></div></div></div>\n'
c = c.replace('        <!-- INFRA PAGE -->', pages_html + '        <!-- INFRA PAGE -->')

# 4. Users table upgrade
c = c.replace(
    '<tbody id="users-table"></tbody>',
    '<tbody id="full-users-body"><tr><td colspan="6" style="text-align:center">Click LOAD ALL USERS</td></tr></tbody>'
)

# 5. Add JS + Logout
js = '\nfunction adminLogout(){localStorage.removeItem("slh_admin_auth");localStorage.removeItem("slh_admin_password");location.reload();}\nasync function loadFinanceDashboard(){try{var r=await fetch(SLH_API+"/api/launch/status");var d=await r.json();document.getElementById("fin-raised").textContent=(d.raised_bnb_verified||0).toFixed(4)+" BNB";}catch(e){}}\nasync function loadTrustEntities(){try{var r=await fetch(SLH_API+"/api/guardian/stats");var d=await r.json();document.getElementById("gtn-flagged").textContent=d.total_flagged_users||0;}catch(e){}}\nasync function loadFullUsers(){var t=document.getElementById("full-users-body");t.innerHTML="<tr><td colspan=6>Loading...</td></tr>";try{var r=await fetch(SLH_API+"/api/admin/all-users",{headers:{"X-Admin-Key":getAdminKey()}});var d=await r.json();if(!d.ok)return;t.innerHTML=d.users.map(function(u){var b=u.balances||{};return "<tr><td><code>"+u.telegram_id+"</code></td><td>"+(u.username||"--")+"</td><td>"+(u.first_name||"--")+"</td><td>"+(b.SLH||0)+"</td><td>"+(b.ZVK||0)+"</td><td><a href=/member.html?user_id="+u.telegram_id+" target=_blank>Card</a></td></tr>";}).join("");document.getElementById("usr-total").textContent=d.count;}catch(e){t.innerHTML="<tr><td colspan=6>"+e.message+"</td></tr>";}}\n'
c = c.replace('</script>\n\n<div id="bottomnav-root">', js + '</script>\n\n<div id="bottomnav-root">')

# 6. Logout in nav
c = c.replace('<a href="/" style="color:var(--text2)">Website</a>', '<a href="/" style="color:var(--text2)">Website</a>\n        <a href="javascript:void(0)" onclick="adminLogout()" style="color:var(--red)">Logout</a>')

# Verify
scripts = re.findall(r'<script>(.*?)</script>', c, re.DOTALL)
for i, s in enumerate(scripts):
    o, cl = s.count('{'), s.count('}')
    print(f'Script {i}: {o}/{cl} {"OK" if o==cl else "MISMATCH!"}')
    assert o == cl, f'Brace mismatch in script {i}!'

with open('D:/SLH_ECOSYSTEM/website/admin.html', 'w', encoding='utf-8') as f:
    f.write(c)
print(f'Done! {len(c)} chars, all checks passed')
