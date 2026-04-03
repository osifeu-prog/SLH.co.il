# SQL Files

All DB changes must be stored here as files.

Run pattern
.\ops\db-run.ps1 .\ops\sql\<file>.sql

Never do
- Do not commit DB passwords
- Do not commit full DATABASE_URL
- Do not trust console glyph rendering alone for Hebrew UTF-8 validation
- Do not rely on one-off pasted SQL with no saved file

Required verification for user-facing text
SELECT key, value_text
FROM system_settings
WHERE key IN (
  'purchase_manual_payment_title',
  'purchase_manual_payment_body',
  'purchase_receipt_footer'
);

SELECT key, encode(convert_to(value_text, 'UTF8'), 'hex')
FROM system_settings
WHERE key IN (
  'purchase_manual_payment_title',
  'purchase_manual_payment_body',
  'purchase_receipt_footer'
);