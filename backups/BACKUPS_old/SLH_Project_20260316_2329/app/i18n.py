STRINGS = {
    "he": {
        "store.title": "חנות",
        "store.empty": "כרגע אין מוצרים זמינים.",
        "store.featured_title": "מומלצים",
        "store.page_label": "עמוד {current}/{total}",
        "store.catalog_hint": "בחר מוצר מהרשימה כדי לראות פרטים ולהמשיך לרכישה.",
        "store.list_title": "מוצרים",
        "store.product_line": "- {title} ({code}) | {amount} {currency}",
        "store.select_product": "פתח מוצר כדי לראות פרטים מלאים וליצור הזמנה.",
        "store.commands": "פקודות שימושיות:",
        "store.cmd.buy": "/buy <PRODUCT_CODE>",
        "store.cmd.my_orders": "/my_orders",
        "store.cmd.submit_payment": "/submit_payment <ORDER_ID> <PAYMENT_REF>",
        "store.cmd.cancel_order": "/cancel_order <ORDER_ID>",

        "button.open_product": "פתח {code}",
        "button.prev": "הקודם",
        "button.next": "הבא",
        "button.refresh": "רענון",
        "button.confirm_purchase": "צור הזמנה",
        "button.back_to_store": "חזרה לחנות",

        "detail.title": "פרטי מוצר",
        "detail.not_found": "המוצר לא נמצא.",
        "detail.success_template": "הודעת הצלחה לאחר אספקה: {text}",

        "store.group.other": "אחר",
        "store.product_group": "קבוצה: {group}",
        "store.product_type": "סוג: {ptype}",
        "store.product_price": "מחיר: {amount} {currency}",
        "store.stock.limited": "מלאי זמין: {count}",
        "store.stock.unlimited": "מלאי: ללא הגבלה",
        "store.limit.user": "מגבלה למשתמש: {count}",
        "store.badge.featured": "מוצר מומלץ",
        "store.product_desc": "תיאור: {text}",

        "order.created.title": "ההזמנה נוצרה",
        "order.id": "מספר הזמנה: {id}",
        "order.product": "מוצר: {title} ({code})",
        "order.quantity": "כמות: {quantity}",
        "order.total": "סכום לתשלום: {amount} {currency}",
        "order.payment_method": "אמצעי תשלום: {method}",
        "order.status": "סטטוס: {status}",
        "order.submit_hint": "לאחר ביצוע ההעברה יש לשלוח אסמכתא או אישור העברה לבדיקה.",
        "order.submit_cmd": "שלח כך: /submit_payment {id} <PAYMENT_REF>",

        "orders.title": "ההזמנות שלי",
        "orders.empty": "עדיין אין לך הזמנות.",
        "orders.row": "#{id} | {title} ({code}) | כמות {quantity} | {amount} {currency} | {status} | אסמכתא {ref}",
        "orders.cancel_format": "לביטול הזמנה:",
        "orders.payment_waiting": "ממתין לתשלום",
        "orders.payment_submitted": "אסמכתא נשלחה",
        "orders.paid": "שולם",
        "orders.fulfilled": "סופק",
        "orders.cancelled": "בוטל",

        "submit_payment.usage": "שימוש: /submit_payment <ORDER_ID> <PAYMENT_REF>",
        "submit_payment.ok.title": "אסמכתא התקבלה לבדיקה",
        "submit_payment.ref": "אסמכתא: {ref}",
        "submit_payment.review_note": "ההזמנה סומנה לבדיקה על ידי מנהל. נעדכן אותך לאחר אישור.",

        "cancel_order.usage": "שימוש: /cancel_order <ORDER_ID>",
        "cancel_order.ok.title": "ההזמנה בוטלה",
        "cancel_order.note": "הערה: {note}",

        "payment.instructions.title": "הוראות תשלום",
        "payment.instructions.line_amount": "סכום להעברה: {amount} {currency}",
        "payment.instructions.line_order": "מספר הזמנה: {id}",
        "payment.instructions.line_product": "מוצר: {title} ({code})",
        "payment.instructions.line_ref": "נא לשלוח אסמכתא / צילום אישור העברה לאחר התשלום.",
        "payment.instructions.line_contact": "איש קשר: {contact}",
        "payment.instructions.line_body": "{body}",
        "payment.instructions.line_after": "אחרי ההעברה שלח: /submit_payment {id} <PAYMENT_REF>",

        "receipt.title": "קבלה / אישור הזמנה",
        "receipt.line_status": "סטטוס סופי: {status}",
        "receipt.line_paid_at": "שולם בתאריך: {paid_at}",
        "receipt.line_fulfilled_at": "סופק בתאריך: {fulfilled_at}",
        "receipt.line_ref": "אסמכתא: {ref}",
        "receipt.line_note": "הערת מנהל: {note}",
        "receipt.line_footer": "תודה שרכשת דרך מערכת SLH.",

        "delivery.friends.title": "הגישה שלך אושרה",
        "delivery.friends.body": "ברוך הבא לקבוצת החברים והתמיכה של SLH.",
        "delivery.friends.join": "קישור הצטרפות:",
        "delivery.success.title": "ההזמנה הושלמה בהצלחה",

        "status.pending_payment": "ממתין לתשלום",
        "status.payment_submitted": "אסמכתא נשלחה",
        "status.paid": "שולם",
        "status.fulfilled": "סופק",
        "status.cancelled": "בוטל",
        "status.unknown": "לא ידוע",
    },
    "en": {
        "store.title": "Store",
        "store.empty": "No products are currently available.",
        "store.featured_title": "Featured",
        "store.page_label": "Page {current}/{total}",
        "store.catalog_hint": "Choose a product from the catalog below.",
        "store.list_title": "Products",
        "store.product_line": "- {title} ({code}) | {amount} {currency}",
        "store.select_product": "Open a product to view details and continue.",
        "store.commands": "Useful commands:",
        "store.cmd.buy": "/buy <PRODUCT_CODE>",
        "store.cmd.my_orders": "/my_orders",
        "store.cmd.submit_payment": "/submit_payment <ORDER_ID> <PAYMENT_REF>",
        "store.cmd.cancel_order": "/cancel_order <ORDER_ID>",

        "button.open_product": "Open {code}",
        "button.prev": "Previous",
        "button.next": "Next",
        "button.refresh": "Refresh",
        "button.confirm_purchase": "Create Order",
        "button.back_to_store": "Back to Store",

        "detail.title": "Product Details",
        "detail.not_found": "Product not found.",
        "detail.success_template": "Success note after fulfillment: {text}",

        "store.group.other": "Other",
        "store.product_group": "Group: {group}",
        "store.product_type": "Type: {ptype}",
        "store.product_price": "Price: {amount} {currency}",
        "store.stock.limited": "Stock: {count}",
        "store.stock.unlimited": "Stock: Unlimited",
        "store.limit.user": "Limit per user: {count}",
        "store.badge.featured": "Featured product",
        "store.product_desc": "Description: {text}",

        "order.created.title": "Order Created",
        "order.id": "Order ID: {id}",
        "order.product": "Product: {title} ({code})",
        "order.quantity": "Quantity: {quantity}",
        "order.total": "Total: {amount} {currency}",
        "order.payment_method": "Payment Method: {method}",
        "order.status": "Status: {status}",
        "order.submit_hint": "After payment, send your transfer confirmation or payment proof.",
        "order.submit_cmd": "Use: /submit_payment {id} <PAYMENT_REF>",

        "orders.title": "My Orders",
        "orders.empty": "You do not have any orders yet.",
        "orders.row": "#{id} | {title} ({code}) | Qty {quantity} | {amount} {currency} | {status} | Ref {ref}",
        "orders.cancel_format": "To cancel an order:",
        "orders.payment_waiting": "Waiting for payment",
        "orders.payment_submitted": "Payment proof submitted",
        "orders.paid": "Paid",
        "orders.fulfilled": "Fulfilled",
        "orders.cancelled": "Cancelled",

        "submit_payment.usage": "Usage: /submit_payment <ORDER_ID> <PAYMENT_REF>",
        "submit_payment.ok.title": "Payment proof received for review",
        "submit_payment.ref": "Reference: {ref}",
        "submit_payment.review_note": "Your order is now under admin review. You will be updated after approval.",

        "cancel_order.usage": "Usage: /cancel_order <ORDER_ID>",
        "cancel_order.ok.title": "Order Cancelled",
        "cancel_order.note": "Note: {note}",

        "payment.instructions.title": "Payment Instructions",
        "payment.instructions.line_amount": "Amount to transfer: {amount} {currency}",
        "payment.instructions.line_order": "Order ID: {id}",
        "payment.instructions.line_product": "Product: {title} ({code})",
        "payment.instructions.line_ref": "Please send your transfer confirmation / payment proof after payment.",
        "payment.instructions.line_contact": "Contact: {contact}",
        "payment.instructions.line_body": "{body}",
        "payment.instructions.line_after": "After payment send: /submit_payment {id} <PAYMENT_REF>",

        "receipt.title": "Receipt / Order Confirmation",
        "receipt.line_status": "Final status: {status}",
        "receipt.line_paid_at": "Paid at: {paid_at}",
        "receipt.line_fulfilled_at": "Fulfilled at: {fulfilled_at}",
        "receipt.line_ref": "Reference: {ref}",
        "receipt.line_note": "Admin note: {note}",
        "receipt.line_footer": "Thank you for purchasing through SLH.",

        "delivery.friends.title": "Your access was approved",
        "delivery.friends.body": "Welcome to the SLH friends and support group.",
        "delivery.friends.join": "Join link:",
        "delivery.success.title": "Your order was completed successfully",

        "status.pending_payment": "pending_payment",
        "status.payment_submitted": "payment_submitted",
        "status.paid": "paid",
        "status.fulfilled": "fulfilled",
        "status.cancelled": "cancelled",
        "status.unknown": "unknown",
    },
}


def get_user_language(obj) -> str:
    try:
        from_user = getattr(obj, "from_user", None)
        if from_user is not None:
            language_code = getattr(from_user, "language_code", None)
            if language_code:
                lang = str(language_code).strip().lower()
                if lang.startswith("he"):
                    return "he"
                return "en"
    except Exception:
        pass
    return "he"


def t(lang: str, key: str, **kwargs) -> str:
    selected = str(lang or "he").strip().lower()
    if selected not in STRINGS:
        selected = "he"
    template = (
        STRINGS.get(selected, {}).get(key)
        or STRINGS.get("he", {}).get(key)
        or STRINGS.get("en", {}).get(key)
        or key
    )
    try:
        return str(template).format(**kwargs)
    except Exception:
        return str(template)


def status_label(lang: str, status: str) -> str:
    key = f"status.{str(status or '').strip()}"
    value = t(lang, key)
    if value == key:
        return t(lang, "status.unknown")
    return value