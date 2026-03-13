"""
recommendation_engine.py
Generates insights in the exact format from the problem statement:
  "38% of negative reviews say the color doesn't match the listing photo.
   Update your product images with natural lighting."
"""

from typing import List, Dict, Any

INSIGHT_TEMPLATES = {
    "Sizing / Fit Issue": (
        "{pct}% of negative reviews report a sizing problem — customers say the "
        "product does not fit as expected or the size chart is inaccurate."
    ),
    "Product Quality": (
        "{pct}% of negative reviews complain about product quality — customers report "
        "the item broke, felt cheap, or stopped working shortly after purchase."
    ),
    "Misleading Listing": (
        "{pct}% of negative reviews say the product doesn't match the listing — "
        "customers report the color, image, or description was inaccurate."
    ),
    "Packaging Issue": (
        "{pct}% of negative reviews mention damaged or inadequate packaging — "
        "customers received the product in a broken or poorly protected box."
    ),
    "Delivery / Logistics": (
        "{pct}% of negative reviews are about late or incorrect delivery — "
        "customers report delays or receiving the wrong item."
    ),
    "Customer Service": (
        "{pct}% of negative reviews mention poor customer service — "
        "customers couldn't get timely help with returns or refunds."
    ),
    "Price / Value": (
        "{pct}% of negative reviews say the product is overpriced — "
        "customers feel the quality does not justify the price paid."
    ),
    "Missing Parts": (
        "{pct}% of negative reviews report missing accessories — "
        "customers received a product with parts not included as shown."
    ),
}

RECOMMENDATIONS = {
    "Sizing / Fit Issue": [
        "Add a detailed size chart with exact measurements (chest, waist, length in cm/inches).",
        "Include a size guide image in your product photos.",
        "Update the product description: 'Runs small — we recommend sizing up'.",
        "Add a FAQ section: 'Should I size up or down?'",
    ],
    "Product Quality": [
        "Source better quality materials from certified suppliers.",
        "Implement pre-dispatch quality control checks.",
        "Add a quality guarantee or warranty mention in your listing.",
        "Show close-up product photos to set accurate expectations.",
    ],
    "Misleading Listing": [
        "Reshoot product photos in natural lighting to show accurate colors.",
        "Add a disclaimer: 'Color may slightly vary due to monitor settings'.",
        "Show all color variants clearly in listing images.",
        "Audit every claim in your description against the actual product.",
    ],
    "Packaging Issue": [
        "Switch to sturdier packaging — double-walled boxes or bubble wrap.",
        "Add 'Fragile' labels for delicate items.",
        "Show the packaging in your listing so buyers know what to expect.",
        "Partner with a logistics provider who handles packages carefully.",
    ],
    "Delivery / Logistics": [
        "Switch to a faster, more reliable courier service.",
        "Enable real-time order tracking notifications via SMS/email.",
        "Update estimated delivery times to be realistic.",
        "Investigate high-return pin codes and prioritize better logistics there.",
    ],
    "Customer Service": [
        "Set up a dedicated support channel (WhatsApp Business / email).",
        "Respond to all queries within 24 hours.",
        "Make the return and refund process simpler and faster.",
        "Display a clear return policy prominently in your listing.",
    ],
    "Price / Value": [
        "Compare your price with top competitors and adjust accordingly.",
        "Bundle accessories or extras to increase perceived value.",
        "Highlight unique selling points clearly in your description.",
        "Showcase positive reviews prominently to justify the price.",
    ],
    "Missing Parts": [
        "Create a pre-packing checklist verified before every dispatch.",
        "Show all included items in product photos with clear labels.",
        "List all included accessories explicitly in your product description.",
        "Add a quality check step specifically for completeness.",
    ],
}


def generate_top_insight(themes: List[Dict[str, Any]], product_name: str = "your product") -> str:
    """
    Returns the headline insight in exact problem-statement format:
    '38% of negative reviews say X. → Fix Y.'
    """
    if not themes:
        return f"No major complaint patterns detected for {product_name}."
    top = themes[0]
    theme = top.get("theme", "")
    pct = top.get("pct", 0)
    template = INSIGHT_TEMPLATES.get(theme, "{pct}% of reviews mention {theme}.")
    sentence = template.format(pct=pct, theme=theme)
    fix = RECOMMENDATIONS.get(theme, ["Review your product listing."])[0]
    return f"{sentence} → {fix}"


def generate_recommendations(themes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Structured recommendations per theme with insight sentence + fix actions.
    """
    recommendations = []
    for d in themes:
        theme = d.get("theme", "")
        pct = d.get("pct", 0)
        count = d.get("count", 0)
        if count == 0:
            continue
        template = INSIGHT_TEMPLATES.get(theme, "{pct}% of reviews mention {theme}.")
        insight = template.format(pct=pct, theme=theme)
        actions = RECOMMENDATIONS.get(theme, [])
        if pct >= 30:
            priority, priority_label = "HIGH", "🔴 HIGH"
        elif pct >= 15:
            priority, priority_label = "MEDIUM", "🟡 MEDIUM"
        else:
            priority, priority_label = "LOW", "🟢 LOW"

        recommendations.append({
            "theme": theme,
            "pct": pct,
            "count": count,
            "priority": priority,
            "priority_label": priority_label,
            "insight": insight,
            "actions": actions,
            "examples": d.get("examples", []),
        })
    return recommendations


def generate_health_score(sentiment_summary: Dict[str, Any]) -> Dict[str, Any]:
    pos_pct = sentiment_summary.get("positive_pct", 0)
    neg_pct = sentiment_summary.get("negative_pct", 0)
    score = max(0, min(100, int(pos_pct - (neg_pct * 0.5))))
    if score >= 70:
        status, color = "GOOD", "#22c55e"
    elif score >= 40:
        status, color = "NEEDS ATTENTION", "#f59e0b"
    else:
        status, color = "CRITICAL", "#ef4444"
    return {"score": score, "status": status, "color": color}
