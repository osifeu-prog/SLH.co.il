# -*- coding: utf-8 -*-
STRINGS = {
    "he": {
        "store.title": "????",
        "store.empty": "???? ??? ?????? ??????.",
        "store.featured_title": "???????",
        "store.page_label": "???? {current}/{total}",
        "store.catalog_hint": "??? ???? ??????? ??? ????? ????? ??????? ??????.",
        "store.list_title": "??????",
        "store.product_line": "- {title} ({code}) | {amount} {currency}",
        "store.select_product": "??? ???? ??? ????? ????? ????? ?????? ?????.",
        "store.commands": "?????? ????????:",
        "store.cmd.buy": "/buy <PRODUCT_CODE>",
        "store.cmd.my_orders": "/my_orders",
        "store.cmd.submit_payment": "/submit_payment <ORDER_ID> <PAYMENT_REF>",
        "store.cmd.cancel_order": "/cancel_order <ORDER_ID>",

        "button.open_product": "??? {code}",
        "button.prev": "?????",
        "button.next": "???",
        "button.refresh": "?????",
        "button.confirm_purchase": "??? ?????",
        "button.back_to_store": "???? ?????",

        "detail.title": "???? ????",
        "detail.not_found": "????? ?? ????.",
        "detail.success_template": "????? ????? ???? ?????: {text}",

        "store.group.other": "???",
        "store.product_group": "?????: {group}",
        "store.product_type": "???: {ptype}",
        "store.product_price": "????: {amount} {currency}",
        "store.stock.limited": "???? ????: {count}",
        "store.stock.unlimited": "????: ??? ?????",
        "store.limit.user": "????? ??????: {count}",
        "store.badge.featured": "???? ?????",
        "store.product_desc": "?????: {text}",

        "order.created.title": "?????? ?????",
        "order.id": "???? ?????: {id}",
        "order.product": "????: {title} ({code})",
        "order.quantity": "????: {quantity}",
        "order.total": "???? ??????: {amount} {currency}",
        "order.payment_method": "????? ?????: {method}",
        "order.status": "?????: {status}",
        "order.submit_hint": "???? ????? ?????? ?? ????? ?????? ?? ????? ????? ??????.",
        "order.submit_cmd": "??? ??: /submit_payment {id} <PAYMENT_REF>",

        "orders.title": "??????? ???",
        "orders.empty": "????? ??? ?? ??????.",
        "orders.row": "#{id} | {title} ({code}) | ???? {quantity} | {amount} {currency} | {status} | ?????? {ref}",
        "orders.cancel_format": "?????? ?????:",
        "orders.payment_waiting": "????? ??????",
        "orders.payment_submitted": "?????? ?????",
        "orders.paid": "????",
        "orders.fulfilled": "????",
        "orders.cancelled": "????",

        "submit_payment.usage": "?????: /submit_payment <ORDER_ID> <PAYMENT_REF>",
        "submit_payment.ok.title": "?????? ?????? ??????",
        "submit_payment.ref": "??????: {ref}",
        "submit_payment.review_note": "?????? ????? ?????? ?? ??? ????. ????? ???? ???? ?????.",

        "cancel_order.usage": "?????: /cancel_order <ORDER_ID>",
        "cancel_order.ok.title": "?????? ?????",
        "cancel_order.note": "????: {note}",

        "payment.instructions.title": "?????? ?????",
        "payment.instructions.line_amount": "???? ??????: {amount} {currency}",
        "payment.instructions.line_order": "???? ?????: {id}",
        "payment.instructions.line_product": "????: {title} ({code})",
        "payment.instructions.line_ref": "?? ????? ?????? / ????? ????? ????? ???? ??????.",
        "payment.instructions.line_contact": "??? ???: {contact}",
        "payment.instructions.line_body": "{body}",
        "payment.instructions.line_after": "???? ?????? ???: /submit_payment {id} <PAYMENT_REF>",

        "receipt.title": "???? / ????? ?????",
        "receipt.line_status": "????? ????: {status}",
        "receipt.line_paid_at": "???? ??????: {paid_at}",
        "receipt.line_fulfilled_at": "???? ??????: {fulfilled_at}",
        "receipt.line_ref": "??????: {ref}",
        "receipt.line_note": "???? ????: {note}",
        "receipt.line_footer": "???? ????? ??? ????? SLH.",

        "delivery.friends.title": "????? ??? ?????",
        "delivery.friends.body": "???? ??? ?????? ?????? ??????? ?? SLH.",
        "delivery.friends.join": "????? ???????:",
        "delivery.success.title": "?????? ?????? ??????",

        "status.pending_payment": "????? ??????",
        "status.payment_submitted": "?????? ?????",
        "status.paid": "????",
        "status.fulfilled": "????",
        "status.cancelled": "????",
        "status.unknown": "?? ????",
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


