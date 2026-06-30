# orders/emails.py

from accounts.emails import send_html_email

# ─────────────────────────────────────────────────────────────────────────────
# Status display helpers (mirror Order model colours/icons)
# ─────────────────────────────────────────────────────────────────────────────

STATUS_META = {
    'pending':    {'color': '#ffc107', 'icon': '⏳', 'label': 'Pending',                 'message': 'We have received your order and are waiting for payment confirmation.'},
    'confirmed':  {'color': '#17a2b8', 'icon': '✅', 'label': 'Confirmed',               'message': 'Your order has been confirmed and will soon go into production.'},
    'processing': {'color': '#007bff', 'icon': '👨‍🍳', 'label': 'Being Prepared',         'message': 'Our bakers have started working on your order — fresh from the oven soon!'},
    'ready':      {'color': '#28a745', 'icon': '🎂', 'label': 'Ready for Pickup/Delivery','message': 'Your order is freshly baked and ready to go!'},
    'completed':  {'color': '#6c757d', 'icon': '🎉', 'label': 'Completed',               'message': 'Your order has been completed. Thank you for choosing M&C Cakes!'},
    'cancelled':  {'color': '#dc3545', 'icon': '❌', 'label': 'Cancelled',               'message': 'Your order has been cancelled. See below for details.'},
}


def _recipient(order) -> str:
    """Always send to customer_email which is a snapshot taken at order time."""
    return order.customer_email


# ─────────────────────────────────────────────────────────────────────────────
# Public email functions
# ─────────────────────────────────────────────────────────────────────────────

def send_order_confirmation(order):
    """
    Sent immediately after order is created (CreateOrderView).
    Replaces the plain send_mail() block in that view.
    """
    send_html_email(
        subject=f"Order Confirmed – {order.order_number} 🎂",
        template_name="emails/order_confirmation.html",
        context={"order": order},
        recipient_email=_recipient(order),
    )


def send_payment_confirmed(order):
    """
    Sent after Paystack confirms payment (payment webhook/callback view).
    Call this from your payment views when payment_status becomes 'paid'.
    """
    send_html_email(
        subject=f"Payment Received – {order.order_number} ✅",
        template_name="emails/payment_confirmed.html",
        context={"order": order},
        recipient_email=_recipient(order),
    )


def send_order_status_update(order):
    """
    Sent when admin updates order status (AdminOrderUpdateView).
    Replaces the plain send_mail() block in that view.
    Automatically selects the right template for 'ready' and 'cancelled',
    falls back to the generic status-update template for all other statuses.
    """
    meta = STATUS_META.get(order.status, STATUS_META['pending'])

    # 'ready' and 'cancelled' get their own richer templates
    if order.status == 'ready':
        send_order_ready(order)
        return

    if order.status == 'cancelled':
        send_order_cancelled(order)
        return

    send_html_email(
        subject=f"Order Update – {order.order_number}: {meta['label']}",
        template_name="emails/order_status_update.html",
        context={
            "order": order,
            "status_color":   meta['color'],
            "status_icon":    meta['icon'],
            "status_label":   meta['label'],
            "status_message": meta['message'],
        },
        recipient_email=_recipient(order),
    )


def send_order_ready(order):
    """Sent when order status becomes 'ready'."""
    has_delivery = hasattr(order, 'delivery') and order.delivery
    delivery_type = "Delivery" if has_delivery else "Pickup"

    send_html_email(
        subject=f"Your Order is Ready! – {order.order_number} 🎉",
        template_name="emails/order_ready.html",
        context={"order": order, "delivery_type": delivery_type},
        recipient_email=_recipient(order),
    )


def send_order_cancelled(order):
    """Sent when order status becomes 'cancelled'."""
    send_html_email(
        subject=f"Order Cancelled – {order.order_number}",
        template_name="emails/order_cancelled.html",
        context={"order": order},
        recipient_email=_recipient(order),
    )