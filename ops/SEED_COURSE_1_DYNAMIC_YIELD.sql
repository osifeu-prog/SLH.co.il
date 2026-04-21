-- =============================================================
-- SEED: Course #1 — Dynamic Yield Economics
-- Target: academy_instructors + academy_courses
-- Prereq: routes/academia_ugc.py init_academia_ugc_tables() has run
--         (tables: academy_instructors, academy_courses with added columns)
-- Date: 2026-04-20
-- =============================================================

BEGIN;

-- 1) Register Osif as official instructor (founder role)
-- user_id 224223270 = Osif Kaufman Ungar (from CLAUDE.md)
INSERT INTO academy_instructors
    (user_id, display_name, bio_he, payout_wallet, approved, created_at)
VALUES (
    224223270,
    'Osif Kaufman Ungar',
    'מייסד SLH Spark. סולו-דב שבנה את כל האקוסיסטם: 25 בוטים, 113 API endpoints, 43 דפי web, 5 טוקנים. הקורס הזה הוא התמצית של מה שלמדתי בדרך הקשה — איך לא לבנות עוד מערכת קריפטו שקורסת.',
    '0xD0617B54FB4b6b66307846f217b4D685800E3dA4',
    TRUE,
    NOW()
)
ON CONFLICT (user_id) DO UPDATE SET
    display_name   = EXCLUDED.display_name,
    bio_he         = EXCLUDED.bio_he,
    payout_wallet  = EXCLUDED.payout_wallet,
    approved       = TRUE;

-- 2) Create the course itself — 3 pricing tiers = 3 rows with same slug prefix
-- Slug convention: course-1-{tier}
-- Course #1 is officially approved (instructor is founder, no review needed)

-- Tier: Free (modules 1-2 only)
INSERT INTO academy_courses
    (instructor_id, slug, title_he, description_he, price_ils, price_slh,
     materials_url, preview_url, language, approval_status)
VALUES (
    (SELECT id FROM academy_instructors WHERE user_id = 224223270),
    'course-1-dynamic-yield-free',
    'כלכלת תשואה דינמית — Free Tier',
    'מודולים 1-2 מתוך 6. Ponzi Detection Framework + Revenue vs Reward Engine. צ''קליסט של 7 דגלים אדומים לזיהוי פרוטוקולים לא יציבים + Decision Tree לסיווג מערכות. מבוא למתמטיקה של Dynamic Yield.',
    0,
    0,
    '/academy/course-1-dynamic-yield/module-1.html',
    '/academy/course-1-dynamic-yield.html',
    'he',
    'approved'
)
ON CONFLICT (slug) DO UPDATE SET
    title_he         = EXCLUDED.title_he,
    description_he   = EXCLUDED.description_he,
    materials_url    = EXCLUDED.materials_url,
    preview_url      = EXCLUDED.preview_url,
    approval_status  = 'approved';

-- Tier: Pro (all 6 modules + calculator + simulator)
INSERT INTO academy_courses
    (instructor_id, slug, title_he, description_he, price_ils, price_slh,
     materials_url, preview_url, language, approval_status)
VALUES (
    (SELECT id FROM academy_instructors WHERE user_id = 224223270),
    'course-1-dynamic-yield-pro',
    'כלכלת תשואה דינמית — Pro',
    'כל 6 המודולים (8 שעות תוכן). נוסחאות ליבה P_t/CR_t/Run Threshold. מחשבון Dynamic Yield אינטראקטיבי. סימולטור Python מלא (4 תרחישים: Bear/Base/Bull/Crisis). Case studies של 5 פרוטוקולים שקרסו. Certificate NFT על BSC בסיום. גישה לעדכוני תוכן 12 חודש. קהילת בוגרים בטלגרם.',
    179.00,
    0.4,
    '/academy/course-1-dynamic-yield/module-1.html',
    '/academy/course-1-dynamic-yield.html',
    'he',
    'approved'
)
ON CONFLICT (slug) DO UPDATE SET
    title_he         = EXCLUDED.title_he,
    description_he   = EXCLUDED.description_he,
    price_ils        = EXCLUDED.price_ils,
    price_slh        = EXCLUDED.price_slh,
    materials_url    = EXCLUDED.materials_url,
    preview_url      = EXCLUDED.preview_url,
    approval_status  = 'approved';

-- Tier: VIP (Pro + 3 Q&A sessions with Osif + model review + early access)
INSERT INTO academy_courses
    (instructor_id, slug, title_he, description_he, price_ils, price_slh,
     materials_url, preview_url, language, approval_status)
VALUES (
    (SELECT id FROM academy_instructors WHERE user_id = 224223270),
    'course-1-dynamic-yield-vip',
    'כלכלת תשואה דינמית — VIP',
    'כל מה שב-Pro + 3 מפגשי Q&A חיים עם Osif (60 דק'' כל אחד) + Review אישי של המודל הכלכלי שלך (עד שעה) + Early access למודולים 7+ (Governance, On-chain oracles) + תג מיוחד בדשבורד SLH + 24 חודשי עדכונים (במקום 12).',
    549.00,
    1.2,
    '/academy/course-1-dynamic-yield/module-1.html',
    '/academy/course-1-dynamic-yield.html',
    'he',
    'approved'
)
ON CONFLICT (slug) DO UPDATE SET
    title_he         = EXCLUDED.title_he,
    description_he   = EXCLUDED.description_he,
    price_ils        = EXCLUDED.price_ils,
    price_slh        = EXCLUDED.price_slh,
    materials_url    = EXCLUDED.materials_url,
    preview_url      = EXCLUDED.preview_url,
    approval_status  = 'approved';

-- 3) Update instructor counters manually (normally done on license purchase,
-- but we want the catalog to show instructor with 3 courses immediately)
UPDATE academy_instructors
SET total_courses = 3
WHERE user_id = 224223270;

COMMIT;

-- Verification queries (run after seed):
-- SELECT id, slug, title_he, price_ils, approval_status
--   FROM academy_courses
--   WHERE slug LIKE 'course-1-dynamic-yield%'
--   ORDER BY price_ils;
--
-- SELECT i.display_name, i.total_courses, COUNT(c.id) AS actual_courses
--   FROM academy_instructors i
--   LEFT JOIN academy_courses c ON c.instructor_id = i.id
--   WHERE i.user_id = 224223270
--   GROUP BY i.display_name, i.total_courses;
