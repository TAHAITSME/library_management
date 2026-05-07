from decimal import Decimal
from textwrap import wrap


PAGE_WIDTH = 595
PAGE_HEIGHT = 842
LEFT = 42
RIGHT = 42
TOP = 802
BOTTOM = 46
NAVY = "0.102 0.180 0.290"
BLUE = "0.173 0.290 0.431"
ACCENT = "0.310 0.596 0.639"
MUTED = "0.420 0.447 0.502"
LIGHT = "0.965 0.973 0.984"
BORDER = "0.835 0.859 0.902"
WHITE = "1 1 1"


def _pdf_escape(value):
    text = str(value or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("cp1252", errors="replace")


def _money(value):
    if value is None:
        value = Decimal("0.00")
    return f"{value} DH"


def _text(x, y, text, size=10, bold=False, color=NAVY):
    font = "F2" if bold else "F1"
    return (
        f"BT {color} rg /{font} {size} Tf 1 0 0 1 {x} {y} Tm ".encode("ascii")
        + b"(" + _pdf_escape(text) + b") Tj ET\n"
    )


def _rect(x, y, w, h, fill, stroke=None):
    if stroke:
        return f"q {fill} rg {stroke} RG {x} {y} {w} {h} re B Q\n".encode("ascii")
    return f"q {fill} rg {x} {y} {w} {h} re f Q\n".encode("ascii")


def _line(x1, y1, x2, y2, color=BORDER):
    return f"q {color} RG {x1} {y1} m {x2} {y2} l S Q\n".encode("ascii")


def _wrap_text(text, width):
    return wrap(str(text or "-"), width=width) or ["-"]


def _draw_header(content, order):
    content.extend(_rect(0, 682, PAGE_WIDTH, 160, NAVY))
    content.extend(_rect(0, 682, PAGE_WIDTH, 160, BLUE))
    content.extend(_text(LEFT, 790, "BiblioNUM", 22, True, WHITE))
    content.extend(_text(LEFT, 768, "Facture / recu de commande", 11, False, "0.820 0.880 0.950"))
    content.extend(_text(LEFT, 724, f"Commande {order.order_number}", 24, True, WHITE))
    content.extend(_text(LEFT, 700, order.created_at.strftime("%d/%m/%Y %H:%M"), 10, False, "0.820 0.880 0.950"))
    content.extend(_rect(395, 728, 142, 46, "0.310 0.596 0.639"))
    content.extend(_text(410, 754, "TOTAL", 9, True, WHITE))
    content.extend(_text(410, 734, _money(order.total), 17, True, WHITE))


def _draw_info_cards(content, order, y):
    user = order.user
    user_name = user.get_full_name() or user.username

    card_w = 247
    content.extend(_rect(LEFT, y - 92, card_w, 92, LIGHT, BORDER))
    content.extend(_rect(LEFT + card_w + 16, y - 92, card_w, 92, LIGHT, BORDER))
    content.extend(_text(LEFT + 14, y - 22, "CLIENT", 8, True, MUTED))
    content.extend(_text(LEFT + 14, y - 42, user_name, 11, True, NAVY))
    content.extend(_text(LEFT + 14, y - 59, user.email or "-", 9, False, MUTED))
    content.extend(_text(LEFT + 14, y - 76, getattr(user, "phone", "") or "-", 9, False, MUTED))

    x2 = LEFT + card_w + 16
    content.extend(_text(x2 + 14, y - 22, "STATUTS", 8, True, MUTED))
    content.extend(_text(x2 + 14, y - 42, f"Commande : {order.get_status_display()}", 10, True, NAVY))
    content.extend(_text(x2 + 14, y - 60, f"Paiement : {order.get_payment_status_display()}", 10, True, NAVY))
    content.extend(_text(x2 + 14, y - 78, f"Articles : {order.items.count()}", 9, False, MUTED))
    return y - 116


def _draw_address(content, order, y):
    content.extend(_text(LEFT, y, "Adresse de livraison", 13, True, NAVY))
    y -= 18
    content.extend(_rect(LEFT, y - 58, PAGE_WIDTH - LEFT - RIGHT, 66, "0.988 0.988 0.984", BORDER))
    yy = y - 12
    for line in _wrap_text(order.shipping_address or "-", 92)[:3]:
        content.extend(_text(LEFT + 14, yy, line, 9, False, MUTED))
        yy -= 14
    return y - 82


def _draw_items(content, order, y):
    content.extend(_text(LEFT, y, "Articles commandes", 13, True, NAVY))
    y -= 24

    table_x = LEFT
    table_w = PAGE_WIDTH - LEFT - RIGHT
    content.extend(_rect(table_x, y - 24, table_w, 28, NAVY))
    content.extend(_text(table_x + 12, y - 13, "Livre", 9, True, WHITE))
    content.extend(_text(table_x + 330, y - 13, "Qt", 9, True, WHITE))
    content.extend(_text(table_x + 376, y - 13, "Prix", 9, True, WHITE))
    content.extend(_text(table_x + 452, y - 13, "Total", 9, True, WHITE))
    y -= 28

    for index, item in enumerate(order.items.select_related("book", "book__author", "book__category"), start=1):
        row_h = 52
        if y - row_h < BOTTOM + 118:
            break
        fill = "1 1 1" if index % 2 else "0.984 0.988 0.992"
        content.extend(_rect(table_x, y - row_h, table_w, row_h, fill))
        book = item.book
        category = book.category.name if book.category else "Livre"
        title = _wrap_text(book.title, 44)[0]
        content.extend(_text(table_x + 12, y - 18, title, 10, True, NAVY))
        content.extend(_text(table_x + 12, y - 34, f"{book.author} | {category}", 8, False, MUTED))
        content.extend(_text(table_x + 334, y - 22, item.quantity, 10, True, NAVY))
        content.extend(_text(table_x + 376, y - 22, _money(item.price), 9, False, NAVY))
        content.extend(_text(table_x + 452, y - 22, _money(item.get_total()), 9, True, NAVY))
        content.extend(_line(table_x, y - row_h, table_x + table_w, y - row_h))
        y -= row_h
    return y - 18


def _draw_totals(content, order, y):
    x = 330
    w = 180
    content.extend(_rect(x, y - 116, w, 116, LIGHT, BORDER))
    rows = [
        ("Sous-total", _money(order.subtotal), False),
        ("Livraison", _money(order.shipping_cost), False),
        ("Remise fidelite", f"-{_money(order.discount)}", False),
        ("Total", _money(order.total), True),
    ]
    yy = y - 20
    for label, value, bold in rows:
        content.extend(_text(x + 14, yy, label, 9, bold, NAVY if bold else MUTED))
        content.extend(_text(x + 94, yy, value, 9 if not bold else 12, bold, NAVY))
        yy -= 20
    return y - 132


def build_order_pdf(order):
    content = bytearray()
    _draw_header(content, order)
    y = _draw_info_cards(content, order, 656)
    y = _draw_address(content, order, y)
    y = _draw_items(content, order, y)
    _draw_totals(content, order, y)
    content.extend(_text(LEFT, 34, "Document genere automatiquement par BiblioNUM.", 8, False, MUTED))

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [5 0 R] /Count 1 >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
        f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents 6 0 R >>".encode("ascii"),
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + bytes(content) + b"endstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)
