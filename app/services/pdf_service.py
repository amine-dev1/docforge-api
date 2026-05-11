"""
PDF Generation Service (ReportLab) — Multi-Template
─────────────────────────────────────────────────────
5 templates disponibles :
  - minimal    : Épuré, fond blanc, accent gris clair
  - corporate  : Bleu institutionnel professionnel
  - creative   : Violet créatif, design asymétrique
  - dark       : En-tête sombre, accent cyan
  - swiss      : Typographie forte, noir & blanc, grille
"""
import io
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image as RLImage
)
from reportlab.lib.utils import ImageReader
import urllib.request



# ── Helpers ───────────────────────────────────────────────────────────────────

def _doc_type_label(doc_type: str) -> str:
    return {
        "invoice": "FACTURE", "quote": "DEVIS", "credit_note": "AVOIR",
        "delivery_note": "BON DE LIVRAISON", "purchase_order": "BON DE COMMANDE",
    }.get(doc_type, doc_type.upper())


def _get_logo(url, max_width=45*mm, max_height=25*mm):
    if not url: return None
    try:
        import os
        if url.startswith("http://") or url.startswith("https://"):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                img_data = io.BytesIO(response.read())
        else:
            if not os.path.exists(url):
                print(f"Local logo file not found: {url}")
                return None
            with open(url, 'rb') as f:
                img_data = io.BytesIO(f.read())
        
        img = ImageReader(img_data)
        iw, ih = img.getSize()
        aspect = ih / float(iw)
        width = max_width
        height = width * aspect
        if height > max_height:
            height = max_height
            width = height / aspect
        logo = RLImage(img_data, width=width, height=height)
        logo.hAlign = 'LEFT'
        return logo
    except Exception as e:
        print(f"Error loading logo from {url}: {e}")
        return None


def _fmt(value) -> str:
    if value is None:
        return "0.00"
    return f"{Decimal(str(value)):,.2f}"


def _hex(h: str):
    h = (h or "#1a1a1a").lstrip("#")
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    return colors.Color(r, g, b)


def _dates(document):
    issued = (document.issued_at or document.created_at)
    issued = issued.strftime("%d/%m/%Y") if issued else "—"
    due = document.due_at.strftime("%d/%m/%Y") if document.due_at else ""
    return issued, due


def _party_lines(ent, client):
    emt = [f"<b>{ent.legal_name}</b>"]
    for v in [ent.address_street,
              " ".join(filter(None, [getattr(ent,"address_city",""), getattr(ent,"address_zip","")])),
              (f"ICE : {ent.ice}" if ent.ice else None),
              (f"RC : {ent.rc}" if ent.rc else None),
              (f"Tél : {ent.phone_main}" if ent.phone_main else None),
              ent.email_general]:
        if v and v.strip():
            emt.append(v)

    cli = ["—"]
    if client:
        cli = [f"<b>{client.legal_name}</b>"]
        for v in [client.address_street,
                  " ".join(filter(None, [getattr(client,"address_city",""), getattr(client,"address_zip","")])),
                  (f"ICE : {client.ice}" if client.ice else None),
                  (f"Tél : {client.phone}" if client.phone else None),
                  client.email]:
            if v and v.strip():
                cli.append(v)
    return "<br/>".join(emt), "<br/>".join(cli)


def _legal_info(ent) -> str:
    """Bloc infos légales / fiscales du tenant."""
    parts = [f"<b>{ent.legal_name}</b>"]
    if getattr(ent, "legal_form", None):  parts.append(ent.legal_form)
    if getattr(ent, "ice", None):         parts.append(f"ICE : {ent.ice}")
    if getattr(ent, "rc", None):          parts.append(f"RC : {ent.rc}")
    if getattr(ent, "if_number", None):   parts.append(f"IF : {ent.if_number}")
    if getattr(ent, "taxe_professionnelle", None): parts.append(f"TP : {ent.taxe_professionnelle}")
    if getattr(ent, "cnss", None):        parts.append(f"CNSS : {ent.cnss}")
    if getattr(ent, "tva_regime", None):  parts.append(f"TVA : {ent.tva_regime}")
    if getattr(ent, "address_street", None):
        addr = ent.address_street
        city = " ".join(filter(None, [getattr(ent,"address_city",""), getattr(ent,"address_zip","")]))
        if city: addr += f", {city}"
        parts.append(addr)
    return "<br/>".join(parts)


def _bank_info(ent) -> str:
    """Bloc coordonnées bancaires du tenant."""
    parts = ["<b>Coordonnees bancaires</b>"]
    if getattr(ent, "bank_name", None):  parts.append(f"Banque : {ent.bank_name}")
    if getattr(ent, "bank_rib", None):   parts.append(f"RIB : {ent.bank_rib}")
    if getattr(ent, "bank_iban", None):  parts.append(f"IBAN : {ent.bank_iban}")
    if getattr(ent, "bank_swift", None): parts.append(f"SWIFT : {ent.bank_swift}")
    if getattr(ent, "bank_branch", None):parts.append(f"Agence : {ent.bank_branch}")
    return "<br/>".join(parts)


# ── TEMPLATE RENDERERS ────────────────────────────────────────────────────────

def _render_minimal(story, document, enterprise, client, lines, styles, W):
    """Template 1 — Minimaliste : blanc, accents gris, typographie fine."""
    primary = colors.Color(0.15, 0.15, 0.15)
    issued, due = _dates(document)
    emt_html, cli_html = _party_lines(enterprise, client)

    logo = _get_logo(getattr(enterprise, "logo_url", None))
    if logo:
        story.append(logo)
        story.append(Spacer(1, 4*mm))

    # Header
    hdr = Table([[
        Paragraph(f"<font size=22><b>{_doc_type_label(document.type)}</b></font>", styles["Normal"]),
        Paragraph(f"<font size=10 color='grey'>N° {document.number}<br/>Date : {issued}" +
                  (f"<br/>Échéance : {due}" if due else "") + "</font>", styles["RightAligned"]),
    ]], colWidths=[W*0.6, W*0.4])
    hdr.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LINEBELOW", (0,0), (-1,0), 1.5, colors.Color(0.85,0.85,0.85)),
    ]))
    story.append(hdr); story.append(Spacer(1, 10*mm))

    # Parties
    p = Table([
        [Paragraph("<font size=8 color='grey'>ÉMETTEUR</font>", styles["Normal"]),
         Paragraph("<font size=8 color='grey'>CLIENT</font>", styles["Normal"])],
        [Paragraph(emt_html, styles["PartyDetail"]),
         Paragraph(cli_html, styles["PartyDetail"])],
    ], colWidths=[W*0.5, W*0.5])
    story.append(p); story.append(Spacer(1, 8*mm))

    # Table items
    data = [["#", "Désignation", "Qté", "P.U. HT", "TVA", "Total HT"]]
    for i, ln in enumerate(lines, 1):
        data.append([str(i), ln.description or "—", str(ln.quantity),
                     _fmt(ln.unit_price_ht), f"{ln.tax_rate_value or 0}%", _fmt(ln.line_total_ht)])
    t = Table(data, colWidths=[W*.05, W*.38, W*.10, W*.16, W*.10, W*.21])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.Color(0.96,0.96,0.96)),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ALIGN",(2,0),(-1,-1),"RIGHT"),
        ("LINEBELOW",(0,0),(-1,-1),0.4,colors.Color(0.9,0.9,0.9)),
        ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(t); story.append(Spacer(1, 8*mm))

    # Totals
    _append_totals(story, document, styles, W, primary)
    _append_footer(story, document, enterprise, styles)


def _render_corporate(story, document, enterprise, client, lines, styles, W):
    """Template 2 — Corporate : bleu navy, colonnes structurées."""
    navy = colors.Color(0.17, 0.24, 0.31)
    issued, due = _dates(document)
    emt_html, cli_html = _party_lines(enterprise, client)

    logo = _get_logo(getattr(enterprise, "logo_url", None))
    if logo:
        story.append(logo)
        story.append(Spacer(1, 4*mm))

    # Header band
    hdr = Table([[
        Paragraph(f"<font color='white' size=20><b>{_doc_type_label(document.type)}</b></font>",
                  styles["Normal"]),
        Paragraph(f"<font color='white' size=10>N° {document.number}<br/>Date : {issued}" +
                  (f"<br/>Échéance : {due}" if due else "") + "</font>", styles["RightAligned"]),
    ]], colWidths=[W*0.6, W*0.4])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), navy),
        ("TOPPADDING",(0,0),(-1,-1),14), ("BOTTOMPADDING",(0,0),(-1,-1),14),
        ("LEFTPADDING",(0,0),(-1,-1),12), ("RIGHTPADDING",(0,0),(-1,-1),12),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(hdr); story.append(Spacer(1, 8*mm))

    # Parties
    p = Table([
        [Paragraph("<font size=8 color='grey'>ÉMETTEUR</font>",styles["Normal"]),
         Paragraph("<font size=8 color='grey'>CLIENT</font>",styles["Normal"])],
        [Paragraph(emt_html, styles["PartyDetail"]),
         Paragraph(cli_html, styles["PartyDetail"])],
    ], colWidths=[W*0.5, W*0.5])
    story.append(p); story.append(Spacer(1, 8*mm))

    # Items
    data = [["#", "Désignation", "Qté", "P.U. HT", "TVA %", "Total HT"]]
    for i, ln in enumerate(lines, 1):
        data.append([str(i), ln.description or "—", str(ln.quantity),
                     _fmt(ln.unit_price_ht), f"{ln.tax_rate_value or 0}%", _fmt(ln.line_total_ht)])
    t = Table(data, colWidths=[W*.05, W*.38, W*.10, W*.16, W*.10, W*.21])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), navy),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ALIGN",(2,0),(-1,-1),"RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.Color(0.94,0.96,0.98)]),
        ("LINEBELOW",(0,0),(-1,-1),0.5,colors.Color(0.85,0.88,0.92)),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story.append(t); story.append(Spacer(1, 8*mm))
    _append_totals(story, document, styles, W, navy)
    _append_footer(story, document, enterprise, styles)


def _render_creative(story, document, enterprise, client, lines, styles, W):
    """Template 3 — Créatif : violet, accents modernes."""
    purple = colors.Color(0.42, 0.36, 0.91)
    light_purple = colors.Color(0.94, 0.92, 1.0)
    issued, due = _dates(document)
    emt_html, cli_html = _party_lines(enterprise, client)

    logo = _get_logo(getattr(enterprise, "logo_url", None))
    if logo:
        story.append(logo)
        story.append(Spacer(1, 4*mm))

    # Colored hero bar
    hdr = Table([[
        Paragraph(f"<font color='white' size=22><b>{_doc_type_label(document.type)}</b></font>",
                  styles["Normal"]),
        Paragraph(f"<font color='white' size=10>N° {document.number}<br/>Date : {issued}" +
                  (f"<br/>Échéance : {due}" if due else "") + "</font>", styles["RightAligned"]),
    ]], colWidths=[W*0.6, W*0.4])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), purple),
        ("TOPPADDING",(0,0),(-1,-1),16), ("BOTTOMPADDING",(0,0),(-1,-1),16),
        ("LEFTPADDING",(0,0),(-1,-1),14), ("RIGHTPADDING",(0,0),(-1,-1),14),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(hdr); story.append(Spacer(1, 6*mm))

    # Client card
    cli_card = Table([[
        Paragraph("<font size=8 color='grey'>CLIENT FACTURÉ</font><br/>" + cli_html, styles["PartyDetail"]),
        Paragraph("<font size=8 color='grey'>ÉMETTEUR</font><br/>" + emt_html, styles["PartyDetail"]),
    ]], colWidths=[W*0.5, W*0.5])
    cli_card.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), light_purple),
        ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),10), ("RIGHTPADDING",(0,0),(-1,-1),10),
        ("LINEAFTER",(0,0),(0,-1),1, purple),
    ]))
    story.append(cli_card); story.append(Spacer(1, 8*mm))

    # Items
    data = [["", "Désignation", "Qté", "P.U. HT", "TVA", "Total HT"]]
    for i, ln in enumerate(lines, 1):
        data.append([str(i), ln.description or "—", str(ln.quantity),
                     _fmt(ln.unit_price_ht), f"{ln.tax_rate_value or 0}%", _fmt(ln.line_total_ht)])
    t = Table(data, colWidths=[W*.05, W*.38, W*.10, W*.16, W*.10, W*.21])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), light_purple),
        ("TEXTCOLOR",(0,0),(-1,0), purple),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ALIGN",(2,0),(-1,-1),"RIGHT"),
        ("LINEBELOW",(0,0),(-1,-1),0.5,light_purple),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story.append(t); story.append(Spacer(1, 8*mm))
    _append_totals(story, document, styles, W, purple)
    _append_footer(story, document, enterprise, styles)


def _render_dark(story, document, enterprise, client, lines, styles, W):
    """Template 4 — Dark : en-tête sombre, accent cyan."""
    dark = colors.Color(0.10, 0.13, 0.18)
    cyan = colors.Color(0.0, 0.82, 0.83)
    mid = colors.Color(0.19, 0.24, 0.31)
    issued, due = _dates(document)
    emt_html, cli_html = _party_lines(enterprise, client)

    logo = _get_logo(getattr(enterprise, "logo_url", None))
    if logo:
        story.append(logo)
        story.append(Spacer(1, 4*mm))

    # Dark header
    hdr = Table([[
        [Paragraph(f"<font color='#00d2d3' size=22><b>{_doc_type_label(document.type)}</b></font>",
                   styles["Normal"]),
         Paragraph(f"<font color='grey' size=9>{enterprise.legal_name}</font>", styles["Normal"])],
        Paragraph(f"<font color='white' size=10>N° {document.number}<br/>Date : {issued}" +
                  (f"<br/>Échéance : {due}" if due else "") + "</font>", styles["RightAligned"]),
    ]], colWidths=[W*0.6, W*0.4])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), dark),
        ("TOPPADDING",(0,0),(-1,-1),16), ("BOTTOMPADDING",(0,0),(-1,-1),16),
        ("LEFTPADDING",(0,0),(-1,-1),14), ("RIGHTPADDING",(0,0),(-1,-1),14),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(hdr)

    # Mid band client
    cli_band = Table([[
        Paragraph("<font size=8 color='grey'>FACTURÉ À</font><br/>" +
                  f"<font color='white'>{cli_html}</font>", styles["PartyDetail"]),
        Paragraph("<font size=8 color='grey'>ÉMETTEUR</font><br/>" +
                  f"<font color='white'>{emt_html}</font>", styles["PartyDetail"]),
    ]], colWidths=[W*0.5, W*0.5])
    cli_band.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), mid),
        ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),14), ("RIGHTPADDING",(0,0),(-1,-1),14),
    ]))
    story.append(cli_band); story.append(Spacer(1, 8*mm))

    # Items
    data = [["#", "Désignation", "Qté", "P.U. HT", "TVA", "Total HT"]]
    for i, ln in enumerate(lines, 1):
        data.append([str(i), ln.description or "—", str(ln.quantity),
                     _fmt(ln.unit_price_ht), f"{ln.tax_rate_value or 0}%", _fmt(ln.line_total_ht)])
    t = Table(data, colWidths=[W*.05, W*.38, W*.10, W*.16, W*.10, W*.21])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), dark),
        ("TEXTCOLOR",(0,0),(-1,0), cyan),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ALIGN",(2,0),(-1,-1),"RIGHT"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.Color(0.95,0.97,0.99)]),
        ("LINEBELOW",(0,0),(-1,-1),0.5, colors.Color(0.88,0.90,0.93)),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story.append(t); story.append(Spacer(1, 8*mm))
    _append_totals(story, document, styles, W, cyan)
    _append_footer(story, document, enterprise, styles)


def _render_swiss(story, document, enterprise, client, lines, styles, W):
    """Template 5 — Classique Suisse : typographie forte, noir et blanc."""
    black = colors.black
    issued, due = _dates(document)
    emt_html, cli_html = _party_lines(enterprise, client)

    logo = _get_logo(getattr(enterprise, "logo_url", None))
    if logo:
        story.append(logo)
        story.append(Spacer(1, 6*mm))

    # Big date stamp
    story.append(Paragraph(
        f"<font size=36><b>{issued}</b></font>", styles["Normal"]))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=3, color=black))
    story.append(Spacer(1, 4*mm))

    # Doc type + number
    story.append(Paragraph(
        f"<font size=18><b>{_doc_type_label(document.type)}</b></font>  "
        f"<font size=12 color='grey'>N° {document.number}</font>", styles["Normal"]))
    story.append(Spacer(1, 8*mm))

    # Parties grid
    p = Table([[
        Paragraph("<font size=8><b>DE</b></font><br/>" + emt_html, styles["PartyDetail"]),
        Paragraph("<font size=8><b>À</b></font><br/>" + cli_html, styles["PartyDetail"]),
        Paragraph(f"<font size=8><b>ÉCHÉANCE</b></font><br/>"
                  f"<font size=11><b>{due or '—'}</b></font>", styles["PartyDetail"]),
    ]], colWidths=[W*0.38, W*0.38, W*0.24])
    story.append(p); story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.Color(0.7,0.7,0.7)))
    story.append(Spacer(1, 4*mm))

    # Items — minimal, no background
    data = [["N°", "DÉSIGNATION", "QTÉ", "P.U. HT", "TVA", "TOTAL HT"]]
    for i, ln in enumerate(lines, 1):
        data.append([str(i), ln.description or "—", str(ln.quantity),
                     _fmt(ln.unit_price_ht), f"{ln.tax_rate_value or 0}%", _fmt(ln.line_total_ht)])
    t = Table(data, colWidths=[W*.05, W*.38, W*.10, W*.16, W*.10, W*.21])
    t.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,0),8),
        ("FONTSIZE",(0,1),(-1,-1),9),
        ("ALIGN",(2,0),(-1,-1),"RIGHT"),
        ("LINEBELOW",(0,0),(-1,0),1.5, black),
        ("LINEBELOW",(0,1),(-1,-1),0.4, colors.Color(0.85,0.85,0.85)),
        ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7),
    ]))
    story.append(t); story.append(Spacer(1, 8*mm))
    _append_totals(story, document, styles, W, black)
    _append_footer(story, document, enterprise, styles)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _append_totals(story, document, styles, W, primary_color):
    rows = [["Sous-total HT", f"{_fmt(document.subtotal_ht)} {document.currency}"]]
    if document.total_discount and document.total_discount > 0:
        rows.append(["Remise", f"-{_fmt(document.total_discount)} {document.currency}"])
    rows.append(["TVA", f"{_fmt(document.total_tax)} {document.currency}"])
    rows.append(["", ""])
    rows.append(["Total TTC", f"{_fmt(document.total_ttc)} {document.currency}"])

    t = Table(rows, colWidths=[W*0.55, W*0.45])
    t.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-2),"Helvetica"),
        ("FONTSIZE",(0,0),(-1,-2),9),
        ("TEXTCOLOR",(0,0),(0,-1), colors.Color(0.45,0.45,0.45)),
        ("ALIGN",(0,0),(-1,-1),"RIGHT"),
        ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,-1),(-1,-1),14),
        ("TEXTCOLOR",(0,-1),(-1,-1), primary_color),
        ("LINEABOVE",(0,-1),(-1,-1),2, primary_color),
        ("TOPPADDING",(0,-1),(-1,-1),8),
    ]))
    story.append(t)


def _append_footer(story, document, ent, styles):
    """
    Ajoute uniquement les notes et conditions dans le flux du document.
    Le bloc légal/bancaire est dessiné en bas de page via onPage callback.
    """
    story.append(Spacer(1, 8*mm))

    if document.notes:
        story.append(Paragraph(
            f"<b>Notes :</b> {document.notes}", styles["FooterNote"]))
        story.append(Spacer(1, 2*mm))
    if getattr(ent, "payment_conditions", None):
        story.append(Paragraph(
            f"<b>Conditions de paiement :</b> {ent.payment_conditions}",
            styles["FooterNote"]))
        story.append(Spacer(1, 2*mm))
    if getattr(ent, "invoice_footer", None):
        story.append(Paragraph(
            f"<i>{ent.invoice_footer}</i>", styles["FooterNote"]))


def _draw_page_footer(canvas, doc_template, enterprise):
    """
    Dessine 2 lignes de texte collées en bas de chaque page A4.
    Ligne 1 : infos légales (raison sociale, ICE, RC, IF, etc.)
    Ligne 2 : coordonnées bancaires (Banque, RIB, IBAN, SWIFT)
    """
    canvas.saveState()

    page_w, page_h = A4
    margin_x = 20 * mm
    center_x = page_w / 2

    # Construire ligne 1 : infos légales
    legal_parts = [enterprise.legal_name]
    if getattr(enterprise, "ice", None):    legal_parts.append(f"ICE : {enterprise.ice}")
    if getattr(enterprise, "rc", None):     legal_parts.append(f"RC : {enterprise.rc}")
    if getattr(enterprise, "if_number", None): legal_parts.append(f"IF : {enterprise.if_number}")
    if getattr(enterprise, "taxe_professionnelle", None): legal_parts.append(f"TP : {enterprise.taxe_professionnelle}")
    if getattr(enterprise, "cnss", None):   legal_parts.append(f"CNSS : {enterprise.cnss}")
    if getattr(enterprise, "tva_regime", None): legal_parts.append(f"TVA : {enterprise.tva_regime}")
    addr = getattr(enterprise, "address_street", "") or ""
    city = " ".join(filter(None, [getattr(enterprise,"address_city",""), getattr(enterprise,"address_zip","")]))
    if addr:
        legal_parts.append(f"{addr}, {city}" if city else addr)
    line1 = "  |  ".join(legal_parts)

    # Construire ligne 2 : coordonnées bancaires
    bank_parts = []
    if getattr(enterprise, "bank_name", None):   bank_parts.append(f"Banque : {enterprise.bank_name}")
    if getattr(enterprise, "bank_rib", None):    bank_parts.append(f"RIB : {enterprise.bank_rib}")
    if getattr(enterprise, "bank_iban", None):   bank_parts.append(f"IBAN : {enterprise.bank_iban}")
    if getattr(enterprise, "bank_swift", None):  bank_parts.append(f"SWIFT : {enterprise.bank_swift}")
    if getattr(enterprise, "bank_branch", None): bank_parts.append(f"Agence : {enterprise.bank_branch}")
    line2 = "  |  ".join(bank_parts) if bank_parts else ""

    # Ligne de séparation
    line_y = 18 * mm
    canvas.setStrokeColor(colors.Color(0.75, 0.75, 0.75))
    canvas.setLineWidth(0.5)
    canvas.line(margin_x, line_y, page_w - margin_x, line_y)

    # Dessiner les 2 lignes de texte
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))

    canvas.drawCentredString(center_x, 12 * mm, line1)
    if line2:
        canvas.drawCentredString(center_x, 8 * mm, line2)

    canvas.restoreState()


# ── PUBLIC API ────────────────────────────────────────────────────────────────

TEMPLATES = {
    "minimal":   _render_minimal,
    "corporate": _render_corporate,
    "creative":  _render_creative,
    "dark":      _render_dark,
    "swiss":     _render_swiss,
}


def generate_pdf(document, enterprise, client, lines, template_name: str = "minimal") -> bytes:
    """
    Génère un PDF en mémoire.

    Parameters
    ----------
    document       : Document ORM
    enterprise     : Enterprise ORM
    client         : Client ORM | None
    lines          : list[DocumentLine]
    template_name  : 'minimal' | 'corporate' | 'creative' | 'dark' | 'swiss'

    Returns
    -------
    bytes – contenu PDF brut
    """
    buf = io.BytesIO()

    # bottomMargin plus grand pour laisser de la place au footer fixe
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=25*mm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("RightAligned", fontName="Helvetica", fontSize=9,
                              alignment=TA_RIGHT, leading=13))
    styles.add(ParagraphStyle("PartyDetail", fontName="Helvetica", fontSize=9,
                              textColor=colors.Color(0.35,0.35,0.35), leading=13))
    styles.add(ParagraphStyle("FooterNote", fontName="Helvetica", fontSize=8,
                              textColor=colors.grey, leading=11))

    story = []
    renderer = TEMPLATES.get(template_name, _render_minimal)
    renderer(story, document, enterprise, client, lines, styles, doc.width)

    # Callback pour dessiner le footer fixe en bas de chaque page
    def on_page(canvas, doc_template):
        _draw_page_footer(canvas, doc_template, enterprise)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

