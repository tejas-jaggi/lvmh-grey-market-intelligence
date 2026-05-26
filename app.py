"""
app.py — LVMH Grey Market Diversion Intelligence Prototype
Flask backend with REST API endpoints for dashboard data.
Phase 1: Foundation + Marketplace Monitoring Dashboard
"""

from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc
from database import (
    db,
    Product,
    Distributor,
    MarketplaceListing,
    PriceAnomaly,
    DiversionAlert,
    ScanRun,
    DiversionScoreHistory,
)
from data_generator import seed_all
from datetime import datetime
import os
import time

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lvmh_grey_market.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ── Setup: Seed on first run ─────────────────────────────────────────────────
def initialize_db():
    """Create and seed DB if it doesn't exist."""
    db_path = os.path.join(app.instance_path, "lvmh_grey_market.db")
    os.makedirs(app.instance_path, exist_ok=True)
    if not os.path.exists(db_path):
        with app.app_context():
            seed_all()
    else:
        # Add newly introduced tables without disturbing existing demo data.
        with app.app_context():
            db.create_all()
            count = Product.query.count()
            if count == 0:
                seed_all()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/listings")
def listings_page():
    return render_template("listings.html")


@app.route("/distributors")
def distributors_page():
    return render_template("distributors.html")


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


def _avg(values):
    return round(sum(values) / len(values), 1) if values else 0.0


def _score_color_bucket(score):
    if score >= 86:
        return "Critical"
    if score >= 66:
        return "High"
    if score >= 41:
        return "Medium"
    return "Low"


def _dis_band(score):
    if score >= 81:
        return "Critical", "Immediate Action Required"
    if score >= 61:
        return "High", "Elevated Diversion Risk"
    if score >= 31:
        return "Elevated", "Monitoring Advised"
    return "Controlled", "Within Acceptable Range"


def _calculate_dis_snapshot():
    """
    Calculate the Diversion Intelligence Score from the current database state.
    The same helper powers the live gauge and the persisted scan snapshots.
    """
    total = MarketplaceListing.query.count() or 1
    flagged = MarketplaceListing.query.filter_by(is_flagged=True).count()
    flagged_rate = (flagged / total) * 100

    avg_dist_risk = db.session.query(func.avg(Distributor.risk_score)).scalar() or 0
    avg_price_gap = db.session.query(func.avg(PriceAnomaly.gap_pct)).scalar() or 0

    flagged_norm = min(100, flagged_rate * 1.8)
    dist_norm = min(100, float(avg_dist_risk))
    gap_norm = min(100, float(avg_price_gap) * 2.5)

    score = round(
        flagged_norm * 0.35 +
        dist_norm * 0.35 +
        gap_norm * 0.30,
        1
    )
    band, label = _dis_band(score)

    return {
        "score": score,
        "band": band,
        "label": label,
        "drivers": {
            "flagged_listing_rate": round(flagged_norm, 1),
            "avg_distributor_risk": round(dist_norm, 1),
            "avg_price_gap": round(gap_norm, 1),
        },
        "raw": {
            "flagged_pct": round(flagged_rate, 1),
            "avg_dist_risk": round(float(avg_dist_risk), 1),
            "avg_gap_pct": round(float(avg_price_gap), 1),
        },
        "total_listings": total,
        "flagged_listings": flagged,
    }


def _history_from_snapshot(snapshot, scan_id=None):
    return DiversionScoreHistory(
        scan_id=scan_id,
        score=snapshot["score"],
        band=snapshot["band"],
        label=snapshot["label"],
        flagged_listing_rate=snapshot["drivers"]["flagged_listing_rate"],
        avg_distributor_risk=snapshot["drivers"]["avg_distributor_risk"],
        avg_price_gap=snapshot["drivers"]["avg_price_gap"],
        flagged_pct=snapshot["raw"]["flagged_pct"],
        avg_dist_risk_raw=snapshot["raw"]["avg_dist_risk"],
        avg_gap_pct_raw=snapshot["raw"]["avg_gap_pct"],
        total_listings=snapshot["total_listings"],
        flagged_listings=snapshot["flagged_listings"],
    )


def _build_driver_breakdown(distributor):
    """Explain distributor score using transparent synthetic drivers."""
    order_pressure = min(100.0, max(0.0, (distributor.order_to_sales_ratio - 1.0) * 70))
    price_pressure = min(100.0, max(0.0, distributor.price_gap_exposure * 2.2))
    compliance_pressure = min(100.0, distributor.compliance_flags * 22.0)
    allocation_pressure = min(100.0, distributor.allocation_volume / 35.0)

    drivers = [
        {
            "label": "Order-to-sales pressure",
            "value": round(order_pressure, 1),
            "detail": f"{distributor.order_to_sales_ratio:.2f}x order-to-sales ratio",
            "note": "Elevated ordering versus sell-through suggests diversion inventory buildup.",
        },
        {
            "label": "Regional price gap exposure",
            "value": round(price_pressure, 1),
            "detail": f"{distributor.price_gap_exposure:.1f}% cross-region price gap exposure",
            "note": "Larger price gaps create stronger arbitrage incentives for unauthorized resale.",
        },
        {
            "label": "Compliance history",
            "value": round(compliance_pressure, 1),
            "detail": f"{distributor.compliance_flags} prior compliance flags",
            "note": "Repeat governance exceptions raise the probability of future leakage.",
        },
        {
            "label": "Allocation intensity",
            "value": round(allocation_pressure, 1),
            "detail": f"{distributor.allocation_volume:,} units allocated",
            "note": "Higher allocation volume magnifies the commercial impact of any leakage.",
        },
    ]
    return sorted(drivers, key=lambda item: item["value"], reverse=True)


def _build_recommendations(distributor):
    recommendations = []

    if distributor.risk_score >= 86:
        recommendations.append({
            "title": "Pause next shipment release",
            "owner": "Distributor Governance",
            "timing": "Immediate",
            "reason": "Risk is above the hold-shipment threshold and requires pre-shipment approval.",
        })
    elif distributor.risk_score >= 66:
        recommendations.append({
            "title": "Open audit workstream",
            "owner": "Regional Compliance",
            "timing": "This week",
            "reason": "Signals are strong enough to justify evidence collection before the next allocation cycle.",
        })
    elif distributor.risk_score >= 41:
        recommendations.append({
            "title": "Move to enhanced monitoring",
            "owner": "Brand Protection",
            "timing": "Next 7 days",
            "reason": "Risk is building and should be reviewed alongside marketplace and reseller activity.",
        })
    else:
        recommendations.append({
            "title": "Maintain baseline monitoring",
            "owner": "Market Surveillance",
            "timing": "Ongoing",
            "reason": "Current signals remain within monitor band, but regional pressure still warrants visibility.",
        })

    if distributor.order_to_sales_ratio >= 1.35:
        recommendations.append({
            "title": "Validate sell-through evidence",
            "owner": "Supply Chain",
            "timing": "Before next PO",
            "reason": "Orders are materially ahead of normalized sales velocity for this partner profile.",
        })

    if distributor.price_gap_exposure >= 20:
        recommendations.append({
            "title": "Review regional pricing and allocation mix",
            "owner": "Commercial Strategy",
            "timing": "Next planning cycle",
            "reason": "Cross-region price gaps are large enough to sustain grey market arbitrage.",
        })

    if distributor.compliance_flags >= 2:
        recommendations.append({
            "title": "Escalate contract enforcement readiness",
            "owner": "Legal / Compliance",
            "timing": "Prepare now",
            "reason": "Repeated compliance exceptions increase the need for documented intervention options.",
        })

    return recommendations[:4]


def _build_signal_feed(distributor):
    alerts = (
        DiversionAlert.query
        .filter(
            DiversionAlert.region == distributor.region,
            DiversionAlert.status.in_(["Open", "Investigating"])
        )
        .order_by(desc(DiversionAlert.created_at))
        .limit(3)
        .all()
    )
    listings = (
        MarketplaceListing.query
        .filter_by(region=distributor.region, is_flagged=True)
        .order_by(desc(MarketplaceListing.confidence), desc(MarketplaceListing.detection_timestamp))
        .limit(3)
        .all()
    )
    anomalies = (
        PriceAnomaly.query
        .filter_by(region=distributor.region)
        .order_by(desc(PriceAnomaly.gap_pct), desc(PriceAnomaly.detected_at))
        .limit(2)
        .all()
    )

    signals = []
    for alert in alerts:
        signals.append({
            "type": "Alert",
            "severity": alert.severity,
            "title": alert.title,
            "subtitle": f"{alert.maison} | {alert.region}",
            "detail": alert.description,
            "metric": f"${round(alert.estimated_impact_usd):,} est. impact",
        })
    for listing in listings:
        maison = listing.product.maison if listing.product else "Unknown Maison"
        product_name = listing.product.product_name if listing.product else listing.product_sku
        signals.append({
            "type": "Marketplace",
            "severity": listing.risk_level,
            "title": f"{maison} listing on {listing.platform}",
            "subtitle": f"{product_name} | {listing.seller_name}",
            "detail": listing.flag_reason or "Flagged resale activity in the same region as this distributor.",
            "metric": f"{listing.confidence * 100:.0f}% confidence",
        })
    for anomaly in anomalies:
        maison = anomaly.product.maison if anomaly.product else "Unknown Maison"
        product_name = anomaly.product.product_name if anomaly.product else anomaly.product_sku
        signals.append({
            "type": "Price gap",
            "severity": anomaly.severity,
            "title": f"{maison} regional price anomaly",
            "subtitle": f"{product_name} | {anomaly.region}",
            "detail": "Resale pricing is materially below authorized regional MSRP.",
            "metric": f"{anomaly.gap_pct:.1f}% gap",
        })

    return signals[:6]


def _build_peer_context(distributor):
    peers = (
        Distributor.query
        .filter_by(region=distributor.region)
        .order_by(desc(Distributor.risk_score))
        .all()
    )
    rank = next(
        (index + 1 for index, peer in enumerate(peers) if peer.distributor_id == distributor.distributor_id),
        1,
    )
    region_count = len(peers)
    percentile = 100 if region_count <= 1 else round((1 - ((rank - 1) / (region_count - 1))) * 100)

    avg_anomaly_gap = (
        db.session.query(func.avg(PriceAnomaly.gap_pct))
        .filter_by(region=distributor.region)
        .scalar()
        or 0
    )
    regional_arbitrage = (
        db.session.query(func.sum(PriceAnomaly.arbitrage_potential_usd))
        .filter_by(region=distributor.region)
        .scalar()
        or 0
    )
    region_flagged = MarketplaceListing.query.filter_by(region=distributor.region, is_flagged=True).count()
    region_open_alerts = (
        DiversionAlert.query
        .filter(
            DiversionAlert.region == distributor.region,
            DiversionAlert.status.in_(["Open", "Investigating"])
        )
        .count()
    )

    return {
        "region": distributor.region,
        "rank_in_region": rank,
        "region_distributor_count": region_count,
        "risk_percentile": percentile,
        "region_avg_risk_score": _avg([peer.risk_score for peer in peers]),
        "region_avg_price_gap_exposure": _avg([peer.price_gap_exposure for peer in peers]),
        "region_high_risk_count": sum(peer.risk_score >= 66 for peer in peers),
        "region_flagged_listings": region_flagged,
        "region_open_alerts": region_open_alerts,
        "region_avg_anomaly_gap_pct": round(avg_anomaly_gap, 1),
        "regional_arbitrage_usd": round(regional_arbitrage, 0),
    }


def _build_distributor_profile(distributor):
    if distributor.risk_score >= 86:
        narrative = "Immediate intervention recommended before the next shipment release."
    elif distributor.risk_score >= 66:
        narrative = "Risk is elevated enough to justify an audit and tighter shipment governance."
    elif distributor.risk_score >= 41:
        narrative = "Signals are mixed but meaningful; this partner belongs on the watchlist."
    else:
        narrative = "Current indicators remain within monitor range, with no immediate hold action."

    return {
        "distributor": distributor.to_dict(),
        "risk_band": _score_color_bucket(distributor.risk_score),
        "narrative": narrative,
        "score_drivers": _build_driver_breakdown(distributor),
        "peer_context": _build_peer_context(distributor),
        "regional_signals": _build_signal_feed(distributor),
        "recommended_actions": _build_recommendations(distributor),
        "model_inputs": {
            "allocation_volume": distributor.allocation_volume,
            "sales_velocity": distributor.sales_velocity,
            "order_to_sales_ratio": distributor.order_to_sales_ratio,
            "price_gap_exposure": distributor.price_gap_exposure,
            "compliance_flags": distributor.compliance_flags,
            "tier": distributor.tier,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# API: DASHBOARD KPIs
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/kpis")
def get_kpis():
    """Return top-level KPI metrics for dashboard cards."""
    total_listings = MarketplaceListing.query.count()
    flagged = MarketplaceListing.query.filter_by(is_flagged=True).count()
    critical = MarketplaceListing.query.filter_by(risk_level="Critical").count()
    high_risk = Distributor.query.filter(Distributor.risk_score >= 66).count()
    hold_shipment = Distributor.query.filter_by(risk_tier="Hold Shipment").count()
    open_alerts = DiversionAlert.query.filter_by(status="Open").count()
    investigating = DiversionAlert.query.filter_by(status="Investigating").count()

    # Estimated revenue at risk: sum of price gap x frequency
    anomalies = PriceAnomaly.query.all()
    revenue_at_risk = sum(a.arbitrage_potential_usd for a in anomalies)

    # Detection rate trend (mock 7-day)
    detection_rate = round((flagged / max(total_listings, 1)) * 100, 1)

    return jsonify({
        "total_listings_scanned": total_listings,
        "unauthorized_flagged": flagged,
        "critical_listings": critical,
        "high_risk_distributors": high_risk,
        "hold_shipment_distributors": hold_shipment,
        "open_alerts": open_alerts + investigating,
        "revenue_at_risk_usd": round(revenue_at_risk, 0),
        "detection_rate_pct": detection_rate,
        "total_distributors": Distributor.query.count(),
        "total_products": Product.query.count(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# API: CHARTS DATA
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/charts/platform-distribution")
def platform_distribution():
    """Pie chart: listings by platform."""
    results = (
        db.session.query(
            MarketplaceListing.platform,
            func.count(MarketplaceListing.listing_id).label("count"),
            func.sum(
                db.case((MarketplaceListing.is_flagged == True, 1), else_=0)
            ).label("flagged"),
        )
        .group_by(MarketplaceListing.platform)
        .order_by(desc("count"))
        .all()
    )
    return jsonify([
        {"platform": r.platform, "count": r.count, "flagged": r.flagged or 0}
        for r in results
    ])


@app.route("/api/charts/risk-by-region")
def risk_by_region():
    """Bar chart: diversion risk signals by region."""
    results = (
        db.session.query(
            MarketplaceListing.region,
            func.count(MarketplaceListing.listing_id).label("total"),
            func.sum(
                db.case((MarketplaceListing.is_flagged == True, 1), else_=0)
            ).label("flagged"),
            func.avg(MarketplaceListing.confidence).label("avg_confidence"),
        )
        .group_by(MarketplaceListing.region)
        .order_by(desc("flagged"))
        .all()
    )
    return jsonify([
        {
            "region": r.region,
            "total": r.total,
            "flagged": r.flagged or 0,
            "avg_confidence": round((r.avg_confidence or 0) * 100, 1),
        }
        for r in results
    ])


@app.route("/api/charts/price-gap-by-region")
def price_gap_by_region():
    """Bar chart: average price gap % by region from anomalies."""
    results = (
        db.session.query(
            PriceAnomaly.region,
            func.avg(PriceAnomaly.gap_pct).label("avg_gap"),
            func.count(PriceAnomaly.event_id).label("events"),
            func.sum(PriceAnomaly.arbitrage_potential_usd).label("total_arbitrage"),
        )
        .group_by(PriceAnomaly.region)
        .order_by(desc("avg_gap"))
        .all()
    )
    return jsonify([
        {
            "region": r.region,
            "avg_gap_pct": round(r.avg_gap or 0, 1),
            "events": r.events,
            "total_arbitrage_usd": round(r.total_arbitrage or 0, 0),
        }
        for r in results
    ])


@app.route("/api/charts/risk-score-distribution")
def risk_score_distribution():
    """Histogram: distributor risk score ladder breakdown."""
    tiers = (
        db.session.query(
            Distributor.risk_tier,
            func.count(Distributor.distributor_id).label("count"),
        )
        .group_by(Distributor.risk_tier)
        .all()
    )
    tier_order = ["Monitor", "Flag for Review", "Trigger Audit", "Hold Shipment"]
    tier_map = {t.risk_tier: t.count for t in tiers}
    return jsonify([
        {"tier": tier, "count": tier_map.get(tier, 0)}
        for tier in tier_order
    ])


@app.route("/api/charts/maison-exposure")
def maison_exposure():
    """Bar chart: flagged listings by Maison."""
    results = (
        db.session.query(
            Product.maison,
            func.count(MarketplaceListing.listing_id).label("total"),
            func.sum(
                db.case((MarketplaceListing.is_flagged == True, 1), else_=0)
            ).label("flagged"),
        )
        .join(MarketplaceListing, MarketplaceListing.product_sku == Product.sku)
        .group_by(Product.maison)
        .order_by(desc("flagged"))
        .all()
    )
    return jsonify([
        {"maison": r.maison, "total": r.total, "flagged": r.flagged or 0}
        for r in results
    ])


@app.route("/api/charts/daily-detections")
def daily_detections():
    """Line chart: daily listing detections (last 14 days)."""
    from datetime import datetime, timedelta
    results = (
        db.session.query(
            func.date(MarketplaceListing.detection_timestamp).label("day"),
            func.count(MarketplaceListing.listing_id).label("total"),
            func.sum(
                db.case((MarketplaceListing.is_flagged == True, 1), else_=0)
            ).label("flagged"),
        )
        .group_by(func.date(MarketplaceListing.detection_timestamp))
        .order_by("day")
        .limit(30)
        .all()
    )
    return jsonify([
        {"day": str(r.day), "total": r.total, "flagged": r.flagged or 0}
        for r in results
    ])


# ─────────────────────────────────────────────────────────────────────────────
# API: LISTINGS TABLE
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/listings")
def get_listings():
    """Paginated listings with filter support."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    risk_filter = request.args.get("risk", None)
    platform_filter = request.args.get("platform", None)
    flagged_only = request.args.get("flagged", "false").lower() == "true"
    search = request.args.get("search", "").strip()

    query = MarketplaceListing.query

    if flagged_only:
        query = query.filter_by(is_flagged=True)
    if risk_filter and risk_filter != "all":
        query = query.filter_by(risk_level=risk_filter)
    if platform_filter and platform_filter != "all":
        query = query.filter_by(platform=platform_filter)
    if search:
        query = query.filter(
            MarketplaceListing.product_sku.ilike(f"%{search}%") |
            MarketplaceListing.seller_name.ilike(f"%{search}%") |
            MarketplaceListing.platform.ilike(f"%{search}%")
        )

    query = query.order_by(desc(MarketplaceListing.detection_timestamp))
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "listings": [l.to_dict() for l in paginated.items],
        "total": paginated.total,
        "pages": paginated.pages,
        "current_page": page,
        "per_page": per_page,
    })


@app.route("/api/listings/flagged/recent")
def recent_flagged():
    """Top 10 most recent flagged/critical listings for dashboard feed."""
    listings = (
        MarketplaceListing.query
        .filter(MarketplaceListing.is_flagged == True)
        .order_by(desc(MarketplaceListing.detection_timestamp))
        .limit(10)
        .all()
    )
    return jsonify([l.to_dict() for l in listings])


# ─────────────────────────────────────────────────────────────────────────────
# API: DISTRIBUTORS
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/distributors/top-risk")
def top_risk_distributors():
    """Top 10 highest-risk distributors for dashboard."""
    distributors = (
        Distributor.query
        .order_by(desc(Distributor.risk_score))
        .limit(10)
        .all()
    )
    return jsonify([d.to_dict() for d in distributors])


@app.route("/api/distributors")
def get_all_distributors():
    """All distributors, sorted by risk score."""
    sort = request.args.get("sort", "risk_score")
    tier_filter = request.args.get("tier", "all")
    search = request.args.get("search", "").strip()

    query = Distributor.query
    if tier_filter and tier_filter != "all":
        query = query.filter_by(risk_tier=tier_filter)
    if search:
        query = query.filter(
            Distributor.name.ilike(f"%{search}%") |
            Distributor.distributor_id.ilike(f"%{search}%") |
            Distributor.region.ilike(f"%{search}%") |
            Distributor.country.ilike(f"%{search}%")
        )

    if sort == "name":
        query = query.order_by(Distributor.name.asc())
    else:
        query = query.order_by(desc(Distributor.risk_score))

    distributors = query.all()
    return jsonify([d.to_dict() for d in distributors])


@app.route("/api/distributors/summary")
def distributor_summary():
    """Summary metrics and region rollups for distributor intelligence page."""
    distributors = Distributor.query.all()

    tier_counts = (
        db.session.query(
            Distributor.risk_tier,
            func.count(Distributor.distributor_id).label("count"),
        )
        .group_by(Distributor.risk_tier)
        .all()
    )
    tier_order = ["Monitor", "Flag for Review", "Trigger Audit", "Hold Shipment"]
    tier_map = {row.risk_tier: row.count for row in tier_counts}

    listing_region_map = {
        row.region: row.flagged or 0
        for row in (
            db.session.query(
                MarketplaceListing.region,
                func.sum(db.case((MarketplaceListing.is_flagged == True, 1), else_=0)).label("flagged"),
            )
            .group_by(MarketplaceListing.region)
            .all()
        )
    }
    alert_region_map = {
        row.region: row.count
        for row in (
            db.session.query(
                DiversionAlert.region,
                func.count(DiversionAlert.alert_id).label("count"),
            )
            .filter(DiversionAlert.status.in_(["Open", "Investigating"]))
            .group_by(DiversionAlert.region)
            .all()
        )
    }
    anomaly_region_map = {
        row.region: round(row.avg_gap or 0, 1)
        for row in (
            db.session.query(
                PriceAnomaly.region,
                func.avg(PriceAnomaly.gap_pct).label("avg_gap"),
            )
            .group_by(PriceAnomaly.region)
            .all()
        )
    }

    region_rows = (
        db.session.query(
            Distributor.region,
            func.count(Distributor.distributor_id).label("count"),
            func.avg(Distributor.risk_score).label("avg_score"),
            func.avg(Distributor.price_gap_exposure).label("avg_gap"),
            func.sum(
                db.case((Distributor.risk_score >= 66, 1), else_=0)
            ).label("high_risk_count"),
        )
        .group_by(Distributor.region)
        .order_by(desc("avg_score"))
        .all()
    )
    region_exposure = [
        {
            "region": row.region,
            "distributor_count": row.count,
            "avg_risk_score": round(row.avg_score or 0, 1),
            "avg_price_gap_exposure": round(row.avg_gap or 0, 1),
            "high_risk_count": row.high_risk_count or 0,
            "flagged_listings": listing_region_map.get(row.region, 0),
            "open_alerts": alert_region_map.get(row.region, 0),
            "avg_anomaly_gap_pct": anomaly_region_map.get(row.region, 0),
        }
        for row in region_rows
    ]
    highest_risk_region = region_exposure[0] if region_exposure else None

    return jsonify({
        "total_distributors": len(distributors),
        "avg_risk_score": _avg([d.risk_score for d in distributors]),
        "hold_shipment_count": sum(d.risk_tier == "Hold Shipment" for d in distributors),
        "watchlist_count": sum(d.risk_score >= 41 for d in distributors),
        "avg_price_gap_exposure": _avg([d.price_gap_exposure for d in distributors]),
        "highest_risk_region": highest_risk_region,
        "tier_distribution": [
            {"tier": tier, "count": tier_map.get(tier, 0)}
            for tier in tier_order
        ],
        "region_exposure": region_exposure,
    })


@app.route("/api/distributors/<distributor_id>/profile")
def distributor_profile(distributor_id):
    """Explainable detail profile for one distributor."""
    distributor = Distributor.query.filter_by(distributor_id=distributor_id).first_or_404()
    return jsonify(_build_distributor_profile(distributor))


# ─────────────────────────────────────────────────────────────────────────────
# API: ALERTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/alerts")
def get_alerts():
    """Recent open/investigating diversion alerts."""
    n = request.args.get("n", 20, type=int)
    alerts = (
        DiversionAlert.query
        .filter(DiversionAlert.status.in_(["Open", "Investigating"]))
        .order_by(desc(DiversionAlert.created_at))
        .limit(n)
        .all()
    )
    return jsonify([a.to_dict() for a in alerts])


# ─────────────────────────────────────────────────────────────────────────────
# API: UTILITY
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/reseed", methods=["POST"])
def reseed():
    """Dev utility: re-seed the database with fresh data."""
    with app.app_context():
        seed_all()
    return jsonify({"status": "reseeded", "message": "Database reseeded successfully."})


@app.route("/api/scan", methods=["POST"])
def run_scan():
    """
    Run the Phase 2 scan pipeline and return a change summary for the dashboard.
    """
    try:
        from ml_engine import (
            score_listings_with_isolation_forest,
            rescore_all_distributors,
            reclassify_listings,
            build_scan_summary,
        )
    except ImportError:
        return jsonify({"error": "ml_engine.py is missing from the project root."}), 500

    t_start = time.time()

    listings = MarketplaceListing.query.all()
    distributors = Distributor.query.all()

    ml_results = score_listings_with_isolation_forest(listings, contamination=0.22)
    listing_changes = reclassify_listings(listings, ml_results)
    distributor_changes = rescore_all_distributors(distributors)

    # Enrich listing changes with DB fields needed for the evidence trail UI
    listing_map = {l.listing_id: l for l in listings}
    for change in listing_changes:
        src = listing_map.get(change["listing_id"])
        if src:
            change["flag_reason"] = src.flag_reason or ""
            change["seller_name"] = src.seller_name or ""
            change["maison"] = src.product.maison if src.product else ""

    db.session.flush()

    elapsed_ms = round((time.time() - t_start) * 1000)
    summary = build_scan_summary(
        listing_changes=listing_changes,
        distributor_changes=distributor_changes,
        total_listings=len(listings),
        total_distributors=len(distributors),
        scan_duration_ms=elapsed_ms,
    )

    summary_stats = summary["summary"]
    scan_run = ScanRun(
        duration_ms=elapsed_ms,
        listings_scanned=summary_stats["listings_scanned"],
        listings_reclassified=summary_stats["listings_reclassified"],
        new_critical_listings=summary_stats["new_critical"],
        new_high_listings=summary_stats["new_high"],
        distributors_scanned=summary_stats["distributors_rescored"],
        distributors_changed=summary_stats["distributors_changed"],
        distributors_escalated=summary_stats["distributors_escalated"],
        distributors_deescalated=summary_stats["distributors_deescalated"],
        severity=summary["severity"],
        narrative=summary["narrative"],
    )
    db.session.add(scan_run)
    db.session.flush()

    dis_snapshot = _calculate_dis_snapshot()
    dis_history = _history_from_snapshot(dis_snapshot, scan_id=scan_run.scan_id)
    db.session.add(dis_history)
    db.session.commit()

    summary["scan_run"] = scan_run.to_dict()
    summary["dis_snapshot"] = dis_history.to_dict()

    return jsonify(summary)


@app.route("/api/price-anomalies")
def get_price_anomalies():
    """Return price anomalies ordered by gap severity."""
    severity_filter = request.args.get("severity", "all")
    region_filter = request.args.get("region", "all")
    limit = request.args.get("n", 100, type=int)

    query = PriceAnomaly.query
    if severity_filter != "all":
        query = query.filter_by(severity=severity_filter)
    if region_filter != "all":
        query = query.filter_by(region=region_filter)

    anomalies = query.order_by(desc(PriceAnomaly.gap_pct)).limit(limit).all()
    return jsonify([anomaly.to_dict() for anomaly in anomalies])


@app.route("/api/analytics/summary")
def analytics_summary():
    """Aggregate stats for the analytics page."""
    total_anomalies = PriceAnomaly.query.count()
    critical_anomalies = PriceAnomaly.query.filter_by(severity="Critical").count()
    total_arbitrage = db.session.query(func.sum(PriceAnomaly.arbitrage_potential_usd)).scalar() or 0
    avg_gap = db.session.query(func.avg(PriceAnomaly.gap_pct)).scalar() or 0

    severity_rows = (
        db.session.query(
            PriceAnomaly.severity,
            func.count(PriceAnomaly.event_id).label("count"),
            func.sum(PriceAnomaly.arbitrage_potential_usd).label("arbitrage"),
        )
        .group_by(PriceAnomaly.severity)
        .all()
    )

    region_rows = (
        db.session.query(
            PriceAnomaly.region,
            func.count(PriceAnomaly.event_id).label("events"),
            func.avg(PriceAnomaly.gap_pct).label("avg_gap"),
            func.sum(PriceAnomaly.arbitrage_potential_usd).label("total_arb"),
        )
        .group_by(PriceAnomaly.region)
        .order_by(desc("avg_gap"))
        .all()
    )

    maison_rows = (
        db.session.query(
            Product.maison,
            func.count(PriceAnomaly.event_id).label("events"),
            func.avg(PriceAnomaly.gap_pct).label("avg_gap"),
            func.sum(PriceAnomaly.arbitrage_potential_usd).label("total_arb"),
        )
        .join(PriceAnomaly, PriceAnomaly.product_sku == Product.sku)
        .group_by(Product.maison)
        .order_by(desc("events"))
        .all()
    )

    return jsonify({
        "total_anomalies": total_anomalies,
        "critical_anomalies": critical_anomalies,
        "total_arbitrage_usd": round(total_arbitrage, 0),
        "avg_gap_pct": round(avg_gap, 1),
        "severity_distribution": [
            {
                "severity": row.severity,
                "count": row.count,
                "arbitrage": round(row.arbitrage or 0, 0),
            }
            for row in severity_rows
        ],
        "by_region": [
            {
                "region": row.region,
                "events": row.events,
                "avg_gap_pct": round(row.avg_gap or 0, 1),
                "total_arbitrage_usd": round(row.total_arb or 0, 0),
            }
            for row in region_rows
        ],
        "by_maison": [
            {
                "maison": row.maison,
                "events": row.events,
                "avg_gap_pct": round(row.avg_gap or 0, 1),
                "total_arbitrage_usd": round(row.total_arb or 0, 0),
            }
            for row in maison_rows
        ],
    })


@app.route("/api/analytics/allocation")
def analytics_allocation():
    """
    Priority 2 — Allocation Intelligence.
    Aggregates distributor data by region to surface over-allocated areas
    where excess inventory is most likely to feed grey market channels.
    """
    rows = (
        db.session.query(
            Distributor.region,
            func.count(Distributor.distributor_id).label("distributor_count"),
            func.sum(Distributor.allocation_volume).label("total_allocation"),
            func.sum(Distributor.sales_velocity * 30).label("total_demand"),
            func.avg(Distributor.risk_score).label("avg_risk_score"),
            func.avg(Distributor.price_gap_exposure).label("avg_price_gap"),
            func.sum(Distributor.compliance_flags).label("total_flags"),
        )
        .group_by(Distributor.region)
        .order_by(desc("total_allocation"))
        .all()
    )

    result = []
    for r in rows:
        total_alloc = float(r.total_allocation or 0)
        total_demand = float(r.total_demand or 0)
        overage = total_alloc - total_demand
        overage_pct = round((overage / max(total_demand, 1)) * 100, 1) if total_demand > 0 else 0
        diversion_potential = round(overage * 2800 * 0.65, 0)  # avg product value × capture rate

        if overage_pct >= 40:
            risk_flag = "Critical"
        elif overage_pct >= 25:
            risk_flag = "High"
        elif overage_pct >= 10:
            risk_flag = "Medium"
        else:
            risk_flag = "Low"

        result.append({
            "region": r.region,
            "distributor_count": r.distributor_count,
            "total_allocation": round(total_alloc),
            "total_demand": round(total_demand),
            "overage_units": round(overage),
            "overage_pct": overage_pct,
            "avg_risk_score": round(float(r.avg_risk_score or 0), 1),
            "avg_price_gap_pct": round(float(r.avg_price_gap or 0), 1),
            "total_compliance_flags": int(r.total_flags or 0),
            "diversion_potential_usd": diversion_potential,
            "risk_flag": risk_flag,
        })

    # Sort by overage_pct descending for most-at-risk first
    result.sort(key=lambda x: x["overage_pct"], reverse=True)
    return jsonify(result)


@app.route("/api/dis_legacy")
def get_dis():
    """
    Diversion Intelligence Score — 0–100 portfolio-level risk gauge.
    Weighted: flagged listing rate (35%) + avg distributor risk (35%) + avg price gap (30%).
    Also returns the previous score stored in a simple in-memory cache so
    the UI can show a before/after delta.
    """
    total = MarketplaceListing.query.count() or 1
    flagged = MarketplaceListing.query.filter_by(is_flagged=True).count()
    flagged_rate = (flagged / total) * 100

    avg_dist_risk = db.session.query(func.avg(Distributor.risk_score)).scalar() or 0
    avg_price_gap = db.session.query(func.avg(PriceAnomaly.gap_pct)).scalar() or 0

    # Normalise each driver to 0–100
    flagged_norm  = min(100, flagged_rate * 1.8)       # 55% flag rate → 100
    dist_norm     = min(100, float(avg_dist_risk))
    gap_norm      = min(100, float(avg_price_gap) * 2.5)  # 40% gap → 100

    score = round(
        flagged_norm  * 0.35 +
        dist_norm     * 0.35 +
        gap_norm      * 0.30,
        1
    )

    if score >= 81:
        band, label = "Critical", "Immediate Action Required"
    elif score >= 61:
        band, label = "High",     "Elevated Diversion Risk"
    elif score >= 31:
        band, label = "Elevated", "Monitoring Advised"
    else:
        band, label = "Controlled", "Within Acceptable Range"

    return jsonify({
        "score":            score,
        "band":             band,
        "label":            label,
        "drivers": {
            "flagged_listing_rate": round(flagged_norm, 1),
            "avg_distributor_risk": round(dist_norm, 1),
            "avg_price_gap":        round(gap_norm, 1),
        },
        "raw": {
            "flagged_pct":   round(flagged_rate, 1),
            "avg_dist_risk": round(float(avg_dist_risk), 1),
            "avg_gap_pct":   round(float(avg_price_gap), 1),
        }
    })


@app.route("/api/dis")
def get_live_dis():
    """Diversion Intelligence Score - 0-100 portfolio-level risk gauge."""
    return jsonify(_calculate_dis_snapshot())


@app.route("/api/dis/history")
def get_dis_history():
    """Return persisted DIS snapshots created by Run Scan events."""
    limit = request.args.get("limit", 20, type=int)
    limit = min(max(limit or 20, 1), 100)

    rows_desc = (
        DiversionScoreHistory.query
        .order_by(desc(DiversionScoreHistory.created_at))
        .limit(limit)
        .all()
    )
    rows = list(reversed(rows_desc))

    if rows:
        items = [row.to_dict() for row in rows]
        latest = items[-1]
        previous = items[-2] if len(items) > 1 else None
        scores = [item["score"] for item in items]
        delta = round(latest["score"] - previous["score"], 1) if previous else 0.0
        return jsonify({
            "items": items,
            "count": DiversionScoreHistory.query.count(),
            "latest": latest,
            "delta": delta,
            "trend": {
                "min": round(min(scores), 1),
                "max": round(max(scores), 1),
                "avg": round(sum(scores) / len(scores), 1),
            },
        })

    live_snapshot = _calculate_dis_snapshot()
    live_item = {
        **live_snapshot,
        "history_id": None,
        "scan_id": None,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "is_live_snapshot": True,
    }
    return jsonify({
        "items": [live_item],
        "count": 0,
        "latest": live_item,
        "delta": 0.0,
        "trend": {
            "min": live_snapshot["score"],
            "max": live_snapshot["score"],
            "avg": live_snapshot["score"],
        },
    })


@app.route("/api/seller-network")
def seller_network():
    """
    Seller network graph data for D3 force-directed visualisation.
    Builds nodes (sellers) and edges (shared signals: same SKU cluster,
    same platform-region combo, or high-volume listing patterns).
    Returns a subset of the most connected sellers for performance.
    """
    from sqlalchemy import text

    # Pull ALL listings (not just flagged) for better color distribution
    # Use a broader pull so nodes span the full risk spectrum
    listings = (
        MarketplaceListing.query
        .filter(MarketplaceListing.confidence > 0.1)
        .order_by(desc(MarketplaceListing.confidence))
        .limit(300)
        .all()
    )

    # Build seller profiles
    seller_map = {}
    for l in listings:
        sid = l.seller_id
        if sid not in seller_map:
            seller_map[sid] = {
                "id":            sid,
                "name":          l.seller_name or sid[:12],
                "platform":      l.platform,
                "region":        l.region,
                "skus":          set(),
                "risk_levels":   [],
                "listing_count": 0,
                "confidence_sum": 0,
                "price_dev_sum": 0,
                "flagged_count": 0,
            }
        seller_map[sid]["skus"].add(l.product_sku)
        seller_map[sid]["risk_levels"].append(l.risk_level)
        seller_map[sid]["listing_count"] += 1
        seller_map[sid]["confidence_sum"] += l.confidence
        seller_map[sid]["price_dev_sum"] += abs(l.price_deviation_pct)
        if l.is_flagged:
            seller_map[sid]["flagged_count"] += 1

    # Score and cap nodes at top 40
    nodes = []
    for sid, s in seller_map.items():
        avg_conf = s["confidence_sum"] / max(s["listing_count"], 1)
        avg_dev  = s["price_dev_sum"]  / max(s["listing_count"], 1)
        flag_rate = s["flagged_count"] / max(s["listing_count"], 1)

        risk_score = (
            s["listing_count"] * 4 +
            len(s["skus"]) * 8 +
            avg_conf * 30
        )

        # Derive risk tier from a composite of confidence + deviation + flag rate
        # This produces a natural distribution across all four tiers
        composite = (avg_conf * 0.5) + (min(avg_dev, 50) / 50 * 0.3) + (flag_rate * 0.2)
        if composite >= 0.72:
            tier = "Critical"
        elif composite >= 0.52:
            tier = "High"
        elif composite >= 0.35:
            tier = "Medium"
        else:
            tier = "Low"

        nodes.append({
            "id":             sid,
            "name":           s["name"],
            "platform":       s["platform"],
            "region":         s["region"],
            "listing_count":  s["listing_count"],
            "flagged_count":  s["flagged_count"],
            "sku_count":      len(s["skus"]),
            "risk":           tier,
            "score":          round(risk_score, 1),
            "avg_confidence": round(avg_conf, 2),
            "avg_deviation":  round(avg_dev, 1),
        })

    nodes.sort(key=lambda x: x["score"], reverse=True)
    nodes = nodes[:40]
    node_ids = {n["id"] for n in nodes}

    # Build edges: sellers connected by shared SKU or same platform+region combo
    edges = []
    node_list = [n for n in nodes]
    seen_edges = set()
    for i, a in enumerate(node_list):
        a_skus = seller_map[a["id"]]["skus"]
        for j, b in enumerate(node_list):
            if j <= i:
                continue
            b_skus = seller_map[b["id"]]["skus"]
            shared = a_skus & b_skus
            same_platform = (
                seller_map[a["id"]]["platform"] == seller_map[b["id"]]["platform"] and
                seller_map[a["id"]]["region"]   == seller_map[b["id"]]["region"]
            )
            if shared or same_platform:
                eid = tuple(sorted([a["id"], b["id"]]))
                if eid not in seen_edges:
                    seen_edges.add(eid)
                    strength = len(shared) * 2 + (1 if same_platform else 0)
                    edges.append({
                        "source":   a["id"],
                        "target":   b["id"],
                        "strength": strength,
                        "shared_skus": len(shared),
                    })

    # Cap edges for performance
    edges.sort(key=lambda e: e["strength"], reverse=True)
    edges = edges[:120]

    return jsonify({"nodes": nodes, "edges": edges})


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "3.1.0-dis-history"})


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if os.environ.get("LVMH_AUTO_INIT_DB", "1").lower() not in ("0", "false", "no"):
    initialize_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_default = "0" if os.environ.get("PORT") else "1"
    debug = os.environ.get("FLASK_DEBUG", debug_default).lower() in ("1", "true", "yes")
    print(f"\n[run] LVMH Grey Market Intelligence running at http://localhost:{port}\n")
    app.run(debug=debug, host="0.0.0.0", port=port)
