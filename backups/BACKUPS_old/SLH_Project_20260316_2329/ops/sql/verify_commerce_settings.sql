SET client_encoding TO 'UTF8';

SELECT key, value_text
FROM system_settings
WHERE key IN (
  'purchase_manual_payment_title',
  'purchase_manual_payment_body',
  'purchase_receipt_footer',
  'purchase_manual_payment_contact',
  'friends_support_invite_link'
)
ORDER BY key;

SELECT key, encode(convert_to(value_text, 'UTF8'), 'hex') AS value_hex
FROM system_settings
WHERE key IN (
  'purchase_manual_payment_title',
  'purchase_manual_payment_body',
  'purchase_receipt_footer'
)
ORDER BY key;