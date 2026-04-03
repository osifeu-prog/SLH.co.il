SET client_encoding TO 'UTF8';

UPDATE system_settings
SET value_text = 'תודה שרכשת דרך מערכת SLH. אישור זה נשלח לאחר סימון paid/fulfilled במערכת.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'purchase_receipt_footer';