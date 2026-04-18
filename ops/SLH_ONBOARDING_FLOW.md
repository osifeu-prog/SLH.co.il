# 🚀 SLH Universe — Onboarding Flow Specification

Complete user journey from signup through first meaningful action.

---

## OVERVIEW

**Objective:** Convert a new user into an active SLH citizen in under 10 minutes
**Success Metric:** User completes first trade, stake, or tournament entry
**Duration:** 5-10 minutes total
**Screens:** 7 main screens + optional tutorials
**Conversion Goal:** 85%+ of signups complete onboarding

---

## FLOW DIAGRAM

```
START
  ↓
[Screen 1] Welcome
  ↓
[Screen 2] Choose Path (Bank/Market/Arena/Forge)
  ↓
[Screen 3] Create/Connect Wallet
  ↓
[Screen 4] Receive Welcome Airdrop (0.1 SLH, 10 ZVK, 5 MNH, 5 REP)
  ↓
[Screen 5] Path-Specific Tutorial (choose based on path)
  ↓
[Screen 6] Mini-Quests (earn bonus ZVK)
  ↓
[Screen 7] Welcome Party + Dashboard Access
  ↓
ACTIVE USER
```

---

## DETAILED SCREENS

### SCREEN 1: WELCOME

**Duration:** 3-5 seconds (can skip)
**Purpose:** Establish brand, set excitement
**Action:** Click "Start Your Journey"

#### Content

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ███████╗██╗     ██╗  ██╗    ████████╗██╗   ██╗██████╗ ███████╗   ║
║   ██╔════╝██║     ██║  ██║    ╚══██╔══╝██║   ██║██╔══██╗██╔════╝   ║
║   █████╗  ██║     ███████║       ██║   ██║   ██║██║  ██║█████╗     ║
║   ██╔══╝  ██║     ██╔══██║       ██║   ██║   ██║██║  ██║██╔══╝     ║
║   ███████╗███████╗██║  ██║       ██║   ╚██████╔╝██████╔╝███████╗   ║
║   ╚══════╝╚══════╝╚═╝  ╚═╝       ╚═╝    ╚═════╝ ╚═════╝ ╚══════╝   ║
║                                                                       ║
║                  WELCOME TO SLH UNIVERSE                              ║
║                                                                       ║
║           You're about to enter a new dimension of                   ║
║           economic freedom, fair competition, and                    ║
║           unlimited possibilities.                                   ║
║                                                                       ║
║           In SLH, there are no shortcuts.                             ║
║           Only skill, strategy, and community.                        ║
║                                                                       ║
║           Your journey starts here.                                  ║
║                                                                       ║
║                  [Start Your Journey →]                              ║
║                     [Or Continue as Guest]                           ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Design Notes:**
- Full-screen animation
- ASCII logo animation
- Background subtle glow
- Emotive messaging
- Two CTAs (primary + secondary)

---

### SCREEN 2: CHOOSE YOUR PATH

**Duration:** 2-3 minutes
**Purpose:** Personalize experience based on user interest
**Action:** Select one of 4 paths (can change later)

#### Content

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    CHOOSE YOUR PATH                                   ║
║                                                                       ║
║         What excites you most about SLH Universe?                    ║
║                                                                       ║
║   ┌────────────────────────────────────────────────────────┐          ║
║   │ 🏦 THE BANKER                                          │          ║
║   │                                                         │          ║
║   │ Earn passive income through staking and lending.      │          ║
║   │ Watch your wealth grow automatically.                 │          ║
║   │ Focus: Stability, long-term growth, safety            │          ║
║   │                                                         │          ║
║   │ Your First Step: Stake 1 ZVK for 24 hours             │          ║
║   │                                              [Select]  │          ║
║   └────────────────────────────────────────────────────────┘          ║
║                                                                       ║
║   ┌────────────────────────────────────────────────────────┐          ║
║   │ 📊 THE TRADER                                          │          ║
║   │                                                         │          ║
║   │ Trade tokens and NFTs in real-time markets.           │          ║
║   │ Discover new assets, spot opportunities, win big.     │          ║
║   │ Focus: Activity, quick wins, market mastery            │          ║
║   │                                                         │          ║
║   │ Your First Step: Buy your first NFT                    │          ║
║   │                                              [Select]  │          ║
║   └────────────────────────────────────────────────────────┘          ║
║                                                                       ║
║   ┌────────────────────────────────────────────────────────┐          ║
║   │ ⚔️  THE COMPETITOR                                     │          ║
║   │                                                         │          ║
║   │ Battle other players, win tournaments, earn glory.    │          ║
║   │ Climb the leaderboard and become a legend.            │          ║
║   │ Focus: Competition, skill, achievement                │          ║
║   │                                                         │          ║
║   │ Your First Step: Enter your first tournament          │          ║
║   │                                              [Select]  │          ║
║   └────────────────────────────────────────────────────────┘          ║
║                                                                       ║
║   ┌────────────────────────────────────────────────────────┐          ║
║   │ 🔨 THE CREATOR                                         │          ║
║   │                                                         │          ║
║   │ Build NFTs, create bots, publish to the world.        │          ║
║   │ Your ideas become real assets with real value.        │          ║
║   │ Focus: Creation, legacy, ownership                     │          ║
║   │                                                         │          ║
║   │ Your First Step: Forge your first NFT                 │          ║
║   │                                              [Select]  │          ║
║   └────────────────────────────────────────────────────────┘          ║
║                                                                       ║
║   Or explore all paths freely:  [Show All Hubs]                      ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Design Notes:**
- Each path has icon, description, focus areas
- Shows "first step" for each path
- Can choose "explore all" to skip personalization
- Clickable cards (large touch targets)
- Color-coded (cyan, magenta borders)

---

### SCREEN 3: CREATE/CONNECT WALLET

**Duration:** 2-5 minutes
**Purpose:** Establish digital identity and security
**Action:** Connect MetaMask OR create new wallet

#### Content

```
╔═══════════════════════════════════════════════════════════════════════╗
║          CREATE YOUR DIGITAL IDENTITY                                 ║
║                                                                       ║
║ Your wallet is your gateway to SLH Universe.                         ║
║ It holds your tokens, your NFTs, your reputation.                    ║
║                                                                       ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║ OPTION 1: CONNECT EXISTING WALLET                                    ║
║                                                                       ║
║ Already have MetaMask, Coinbase Wallet, or Ledger?                  ║
║ Connect instantly — takes 10 seconds.                                ║
║                                                                       ║
║ ┌─────────────────────────────────────┐                             ║
║ │ 🦊 CONNECT METAMASK                 │                             ║
║ │ (Most popular, fully supported)      │                             ║
║ └─────────────────────────────────────┘                             ║
║                                                                       ║
║ ┌─────────────────────────────────────┐                             ║
║ │ 📱 CONNECT COINBASE WALLET          │                             ║
║ │ (Mobile-friendly alternative)        │                             ║
║ └─────────────────────────────────────┘                             ║
║                                                                       ║
║ ┌─────────────────────────────────────┐                             ║
║ │ 🔐 CONNECT LEDGER                  │                             ║
║ │ (Ultimate security, hardware wallet) │                             ║
║ └─────────────────────────────────────┘                             ║
║                                                                       ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║ OPTION 2: CREATE NEW WALLET                                          ║
║                                                                       ║
║ New to crypto? We'll generate a secure wallet for you.              ║
║ Your private key is encrypted and stored securely.                  ║
║                                                                       ║
║ ┌─────────────────────────────────────────────────────────┐         ║
║ │ ┌ Email:  [________________@_____________]             │         ║
║ │ │                                                       │         ║
║ │ │ Password: [______________________] (min 12 chars)    │         ║
║ │ │                                                       │         ║
║ │ │ [✓] I understand my private key is my responsibility │         ║
║ │ │                                                       │         ║
║ │ │ [CREATE WALLET]                                      │         ║
║ │ └                                                       │         ║
║ └─────────────────────────────────────────────────────────┘         ║
║                                                                       ║
║ Why Wallet Security Matters:                                         ║
║ Your wallet = Your identity + Your money + Your reputation          ║
║ Never share your private key. Not even with admins.                 ║
║                                                                       ║
║ [Read Security Best Practices]                                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Design Notes:**
- Clear options for different user types
- Emphasize security
- Multiple providers for flexibility
- Simple form for new wallet creation
- Security education inline

---

### SCREEN 4: WELCOME AIRDROP

**Duration:** 10-20 seconds
**Purpose:** Give user funds to explore with, build excitement
**Action:** Claim airdrop (automatic, just confirm)

#### Content

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                    🎉 YOUR WELCOME GIFT 🎉                          ║
║                                                                       ║
║                Congratulations, new citizen!                          ║
║                                                                       ║
║         As a new member of SLH Universe, you receive              ║
║              your genesis airdrop worth ~50 MNH:                    ║
║                                                                       ║
║   ┌──────────────────────────────────────────────────────┐          ║
║   │  ◆ SLH Token                 0.1 units (44 ILS)    │          ║
║   │                                                      │          ║
║   │  ○ ZVK (Activity)            10   units (~44 ILS)  │          ║
║   │  - For trading, staking, and earning                │          ║
║   │                                                      │          ║
║   │  □ MNH (Stability)            5   units (5 MNH)    │          ║
║   │  - Emergency fund, stable anchor                    │          ║
║   │                                                      │          ║
║   │  ★ REP (Reputation)           5   points            │          ║
║   │  - Unlock premium features                          │          ║
║   │                                                      │          ║
║   │  ═══════════════════════════════════════════════    │          ║
║   │  TOTAL VALUE:                    ~50 MNH            │          ║
║   │                                                      │          ║
║   │          Ready to claim? [CLAIM AIRDROP]            │          ║
║   └──────────────────────────────────────────────────────┘          ║
║                                                                       ║
║                 💡 How to use your tokens:                           ║
║                                                                       ║
║                 Trade:  Buy/sell in the market                       ║
║                 Stake:  Lock up for passive income                   ║
║                 Earn:   Compete and build reputation                 ║
║                 Create: Forge new NFTs and assets                    ║
║                                                                       ║
║             This is just the beginning. Learn more: [Docs]          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**After Claim:**
```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                    ✓ AIRDROP RECEIVED!                               ║
║                                                                       ║
║              Your wallet has been funded successfully.               ║
║              Check your balance on the next screen.                  ║
║                                                                       ║
║                         [CONTINUE →]                                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Design Notes:**
- Show all tokens together
- Explain each token's purpose
- Celebrate the moment
- Clear next step

---

### SCREEN 5: PATH-SPECIFIC TUTORIAL

**Duration:** 2-5 minutes (based on path)
**Purpose:** Teach core concepts for chosen path
**Action:** Complete short interactive tutorial

#### PATH A: Banker Tutorial
```
╔═══════════════════════════════════════════════════════════════════════╗
║              🏦 WELCOME TO SLH BANK - BANKER'S GUIDE                 ║
║                                                                       ║
║  UNDERSTANDING STAKING                                               ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║  Staking = Earning by waiting                                         ║
║                                                                       ║
║  What happens:                                                        ║
║  1. You deposit tokens into a vault                                   ║
║  2. SLH locks them for a period (24h, 7d, 30d, etc)                 ║
║  3. You earn interest automatically (10% APY minimum)                ║
║  4. After period ends, you withdraw (principal + interest)           ║
║                                                                       ║
║  Example:                                                             ║
║  - Deposit: 100 ZVK                                                   ║
║  - Earning Rate: 10% APY                                             ║
║  - Lock Period: 30 days                                              ║
║  - Interest Earned: ~2.5 ZVK (pro-rated)                            ║
║  - After 30 days: 102.5 ZVK available to withdraw                  ║
║                                                                       ║
║  Ready to try?                                                        ║
║  [STAKE 1 ZVK FOR 24 HOURS] (Your first quest!)                     ║
║  (After this, [CONTINUE] to see your staking dashboard)             ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

#### PATH B: Trader Tutorial
```
╔═══════════════════════════════════════════════════════════════════════╗
║             📊 WELCOME TO SLH MARKET - TRADER'S GUIDE                ║
║                                                                       ║
║  HOW TO TRADE                                                         ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║  Trading = Buying and selling for profit                             ║
║                                                                       ║
║  Step 1: Choose a pair                                                ║
║  - ZVK/MNH (most liquid)                                             ║
║  - SLH/MNH (rare, high value)                                        ║
║  - Any NFT/NFT or Token/Token combo                                  ║
║                                                                       ║
║  Step 2: Analyze the price                                            ║
║  - Looking at the chart, is price going up or down?                 ║
║  - Buy low, sell high = profit                                       ║
║  - Sell high, buy low = profit                                       ║
║                                                                       ║
║  Step 3: Place your order                                             ║
║  - Market order: Buy/sell instantly at current price                ║
║  - Limit order: Wait for price to hit your target                   ║
║                                                                       ║
║  Your first trade:                                                    ║
║  - You have 10 ZVK                                                    ║
║  - Current rate: 1 ZVK = 1.09 MNH                                   ║
║  - You'll get: ~9.2 MNH                                              ║
║                                                                       ║
║  Ready to try?                                                        ║
║  [BUY 5 ZVK WORTH OF MNH] (Your first quest!)                       ║
║  (After this, you'll have 5 ZVK left + ~5.5 MNH)                    ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

#### PATH C: Competitor Tutorial
```
╔═══════════════════════════════════════════════════════════════════════╗
║            ⚔️  WELCOME TO SLH ARENA - COMPETITOR'S GUIDE            ║
║                                                                       ║
║  HOW TO COMPETE                                                       ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║  Competing = Battling other players for rewards                      ║
║                                                                       ║
║  Types of Competitions:                                               ║
║  - 1v1 Duels: Head-to-head battles (instant)                        ║
║  - Tournaments: Multi-round brackets (24h-30d)                      ║
║  - Seasonal Leaderboards: Month-long competitions                   ║
║                                                                       ║
║  Rewards:                                                             ║
║  - 1st place: 1000 ZVK + 10 REP + trophy                            ║
║  - 2nd place: 300 ZVK + 5 REP                                       ║
║  - 3rd place: 100 ZVK + 2 REP                                       ║
║  - Participation: 10 ZVK (just for showing up)                      ║
║                                                                       ║
║  Your advantage as a newbie:                                          ║
║  - Beginner brackets (fair matchups)                                 ║
║  - Lower entry fee (2 ZVK instead of 10)                            ║
║  - Extra rewards for new player wins                                 ║
║                                                                       ║
║  Ready to compete?                                                    ║
║  [ENTER BEGINNER TOURNAMENT] (Your first quest!)                    ║
║  (Takes 5-10 minutes, you're guaranteed compensation even if you lose)║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

#### PATH D: Creator Tutorial
```
╔═══════════════════════════════════════════════════════════════════════╗
║             🔨 WELCOME TO SLH FORGE - CREATOR'S GUIDE               ║
║                                                                       ║
║  HOW TO CREATE & PUBLISH                                              ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║  Creating = Building digital assets and publishing them              ║
║                                                                       ║
║  What you can create:                                                 ║
║  - Digital Art & Collectibles (images, animations)                  ║
║  - Bots & Autonomous Agents (AI tools)                              ║
║  - Virtual Property (land, buildings, locations)                    ║
║  - Educational Content (courses, guides)                            ║
║  - Services & Access (memberships, communities)                     ║
║                                                                       ║
║  The Process:                                                         ║
║  1. Upload your file (PNG, JPG, MP4, up to 50MB)                    ║
║  2. Fill in metadata (title, description, properties)               ║
║  3. Set price (in MNH)                                               ║
║  4. Choose quantity (1 = unique, 10+ = collection)                  ║
║  5. Publish to marketplace (instant, no approval needed)            ║
║  6. Earn royalties when others resell                               ║
║                                                                       ║
║  Your earnings:                                                       ║
║  - Initial sale: 100% (you keep it all)                             ║
║  - Resales: 5% royalty (on every future sale)                       ║
║                                                                       ║
║  Example:                                                             ║
║  - You create an NFT, sell for 100 MNH                              ║
║  - Someone buys it for 100 MNH (you get 100 MNH)                   ║
║  - Someone else buys it for 150 MNH (you get 7.5 MNH)              ║
║  - Passive income, forever                                           ║
║                                                                       ║
║  Ready to create?                                                     ║
║  [FORGE YOUR FIRST NFT] (Your first quest!)                         ║
║  (Simple template provided, just customize and publish)              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Design Notes:**
- Path-specific content
- Clear examples with numbers
- Next action highlighted
- Educational but brief
- Hands-on (user actually does something)

---

### SCREEN 6: MINI-QUESTS & REWARDS

**Duration:** 3-5 minutes
**Purpose:** Gamify onboarding, keep user engaged
**Action:** Complete 3-5 small tasks to earn bonus ZVK

#### Content

```
╔═══════════════════════════════════════════════════════════════════════╗
║                    🎯 FIRST CHALLENGES                                ║
║                                                                       ║
║ Complete these to unlock bonus rewards and features!                 ║
║                                                                       ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║ [✓] Quest 1: Created Wallet (Reward: +5 ZVK)                         ║
║     Status: COMPLETED                                                ║
║                                                                       ║
║ [✓] Quest 2: Path-Specific Action (Reward: +10 ZVK)                  ║
║     Status: COMPLETED                                                ║
║     (Staked/Traded/Competed/Created, depending on your path)        ║
║                                                                       ║
║ [ ] Quest 3: Explore 3 Hubs (Reward: +5 ZVK)                         ║
║     Status: IN PROGRESS (2/3 visited)                               ║
║     [ ] Bank          ✓ Visited                                      ║
║     [ ] Market        ✓ Visited                                      ║
║     [ ] Arena                 [Visit Now]                            ║
║     [ ] Forge                                                        ║
║                                                                       ║
║ [ ] Quest 4: View Your Portfolio (Reward: +3 ZVK)                    ║
║     Status: NOT STARTED                                              ║
║     [Take Me There]                                                  ║
║                                                                       ║
║ [ ] Quest 5: Read Community Guidelines (Reward: +2 ZVK)              ║
║     Status: NOT STARTED                                              ║
║     [Read Now]                                                       ║
║                                                                       ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║ Rewards Earned So Far: 15 ZVK                                         ║
║ Remaining Potential: 10 ZVK                                           ║
║                                                                       ║
║ Your total assets now: ~75 ZVK + 5 MNH worth                         ║
║                                                                       ║
║ Progress:  ████████░░░░░░░░░░░░░░░░░░  60%                          ║
║                                                                       ║
║ [Skip Remaining] or [Continue Quests] or [Go to Dashboard]          ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Design Notes:**
- Show progress on quests
- Each quest has clear action
- Reward amount displayed
- Gamification (badges, progress bar)
- Optional (can skip)

---

### SCREEN 7: WELCOME PARTY + DASHBOARD

**Duration:** 2-3 minutes
**Purpose:** Celebrate user activation, show dashboard
**Action:** Enter main app, explore freely

#### Content

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║                        🎉 YOU'RE IN! 🎉                              ║
║                                                                       ║
║           Welcome to SLH Universe, Citizen 8437                       ║
║                                                                       ║
║  You've successfully created your digital identity.                  ║
║  Your wallet is funded. The marketplace awaits.                      ║
║  The collective is ready to meet you.                                 ║
║                                                                       ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║  YOUR QUICK STATS:                                                    ║
║  ┌──────────────────────────────────────────────────────┐           ║
║  │ Account Age:        15 minutes                        │           ║
║  │ Assets:             ~75 ZVK + 5 MNH worth            │           ║
║  │ Reputation:         5 REP (Newcomer)                 │           ║
║  │ Active Quests:      2 remaining (optional)            │           ║
║  │ Current Path:       Banker (can change anytime)      │           ║
║  └──────────────────────────────────────────────────────┘           ║
║                                                                       ║
║  YOUR NEXT STEPS:                                                     ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║  1. [VIEW DASHBOARD]    See your assets and portfolio                ║
║  2. [EXPLORE MARKET]    Discover NFTs to trade                       ║
║  3. [JOIN TOURNAMENT]   Enter your first competition                 ║
║  4. [READ GUIDE]        Learn more about SLH                         ║
║  5. [JOIN COMMUNITY]    Connect with other users                     ║
║                                                                       ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║  IMPORTANT REMINDERS:                                                 ║
║  ✓ Your private key = Your identity. Never share it.                 ║
║  ✓ Verify every transaction before confirming.                       ║
║  ✓ No one from SLH will ask for your password.                       ║
║  ✓ Report fraud/scams immediately via [Report Button]               ║
║                                                                       ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    ║
║                                                                       ║
║           [ENTER DASHBOARD]          [Skip & Explore Freely]        ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Post-Onboarding Dashboard:**
```
╔═══════════════════════════════════════════════════════════════════════╗
║ SLH BANK                          [Notifications: 3] [Help] [⏻]    ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║ WELCOME, CITIZEN 8437!                                                ║
║                                                                       ║
║ PORTFOLIO VALUE: 80.25 MNH    ↑ Complete any 2 remaining quests    ║
║                              for +10 ZVK bonus                      ║
║                                                                       ║
║ ASSETS                                                                ║
║ ○ ZVK              75      | 75.00 MNH                               ║
║ □ MNH               5      | 5.00 MNH                                ║
║ ★ REP               5      | — (non-transferable)                    ║
║                                                                       ║
║ ONBOARDING REWARDS                                                    ║
║ [✓] Welcome Airdrop          +0.1 SLH, +10 ZVK, +5 MNH, +5 REP      ║
║ [✓] Path Completion Bonus    +10 ZVK                                 ║
║ [✓] Quest Rewards            +8 ZVK                                  ║
║                                                                       ║
║ QUICK ACTIONS                                                         ║
║ ┌──────────┬──────────┬──────────┬──────────┬──────────┐            ║
║ │ [Stake]  │[Market]  │ [Arena]  │ [Forge]  │[History] │            ║
║ └──────────┴──────────┴──────────┴──────────┴──────────┘            ║
║                                                                       ║
║ YOUR NEXT OPPORTUNITY                                                 ║
║ ┌─────────────────────────────────────────────────────┐             ║
║ │ Lightning Duel Starting in 30 minutes               │             ║
║ │ Entry: 2 ZVK | Prize: 50 ZVK (to winner)           │             ║
║ │                                      [Register Now] │             ║
║ └─────────────────────────────────────────────────────┘             ║
║                                                                       ║
║ LEARNING RESOURCES                                                    ║
║ • Getting Started Guide     • Video Tutorials                        ║
║ • Community Guidelines      • FAQ                                    ║
║ • Security Best Practices   • Trading Strategies                    ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Design Notes:**
- Celebrate completion
- Show account summary
- Provide next steps
- Security reminders
- Access to full dashboard

---

## ANALYTICS & METRICS

Track these during onboarding:

**Completion Rate:**
- Target: 85%+ complete all 7 screens
- Current: (track daily)
- Goal: Get users to active state ASAP

**Drop-off Points:**
- Where do users leave?
- Why (surveys after exit)
- Iterate to reduce friction

**Time Spent:**
- Target: 5-10 minutes total
- Screen-by-screen breakdown
- Optimize longer screens

**First Actions (after onboarding):**
- What do users do first?
- Which hub gets most traffic?
- Path-based behavior analysis

**30-Day Retention:**
- % of onboarded users active after 30 days
- Path-based retention
- Correlation with quests completed

---

## OPTIMIZATION RULES

1. **Keep It Short**
   - Max 10 minutes end-to-end
   - Most users scan, don't read
   - Use visuals, not text

2. **Make It Personal**
   - Remember their path choice
   - Tailor recommendations
   - Acknowledge achievements

3. **Reduce Friction**
   - Pre-fill where possible
   - Skip unnecessary steps
   - Make skipping easy

4. **Celebrate Progress**
   - Show completion percentage
   - Highlight achievements
   - Make rewards visible

5. **Test & Iterate**
   - A/B test variations
   - Track metrics weekly
   - Quick pivots based on data

---

## FINAL CHECKLIST

- [ ] All 7 screens designed and copywritten
- [ ] Path-specific tutorials created
- [ ] Welcome airdrop amounts locked in
- [ ] Quest system defined
- [ ] Analytics tracking implemented
- [ ] Mobile responsiveness tested
- [ ] Accessibility verified
- [ ] Security warnings clear
- [ ] Help/support links available
- [ ] A/B testing framework ready

---

**Onboarding Flow Version:** 1.0
**Last Updated:** 2026-04-18
**Target Launch:** Week 1 of public beta
**Expected Impact:** 85% completion rate, 40%+ active after 7 days
