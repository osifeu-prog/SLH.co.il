SET client_encoding TO 'UTF8';

INSERT INTO system_settings (key, value_text, updated_at) VALUES
('purchase_manual_payment_title', 'תשלום ידני', CURRENT_TIMESTAMP),
('purchase_manual_payment_body', 'יש לבצע את ההעברה לפי פרטי התשלום שנמסרו על ידי המנהל. לאחר ביצוע ההעברה יש לשלוח אסמכתא או צילום אישור העברה כדי שנוכל לאשר את ההזמנה.', CURRENT_TIMESTAMP),
('purchase_manual_payment_contact', '@osifeu_prog', CURRENT_TIMESTAMP),
('purchase_receipt_footer', 'תודה שרכשת דרך מערכת SLH. אישור זה נשלח לאחר סימון paid/fulfilled במערכת.', CURRENT_TIMESTAMP),
('friends_support_invite_link', 'https://t.me/+KLKB9-JdO85kNWJk', CURRENT_TIMESTAMP)
ON CONFLICT (key)
DO UPDATE SET
  value_text = EXCLUDED.value_text,
  updated_at = CURRENT_TIMESTAMP;