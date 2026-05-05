"""
database.py — SQLAlchemy models for LVMH Grey Market Prototype
All tables: Products, Distributors, Listings, PriceAnomalies, DiversionAlerts
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = "products"

    sku = db.Column(db.String(20), primary_key=True)
    maison = db.Column(db.String(50), nullable=False)
    product_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    msrp_usd = db.Column(db.Float, nullable=False)
    msrp_eur = db.Column(db.Float, nullable=False)
    msrp_cny = db.Column(db.Float, nullable=False)
    is_limited_edition = db.Column(db.Boolean, default=False)
    launch_year = db.Column(db.Integer)

    listings = db.relationship("MarketplaceListing", backref="product", lazy=True)
    anomalies = db.relationship("PriceAnomaly", backref="product", lazy=True)

    def to_dict(self):
        return {
            "sku": self.sku,
            "maison": self.maison,
            "product_name": self.product_name,
            "category": self.category,
            "msrp_usd": self.msrp_usd,
            "msrp_eur": self.msrp_eur,
            "msrp_cny": self.msrp_cny,
            "is_limited_edition": self.is_limited_edition,
            "launch_year": self.launch_year,
        }


class Distributor(db.Model):
    __tablename__ = "distributors"

    distributor_id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(60), nullable=False)
    tier = db.Column(db.String(20), nullable=False)  # Platinum / Gold / Silver
    allocation_volume = db.Column(db.Integer, default=0)
    sales_velocity = db.Column(db.Float, default=0.0)  # units/month
    order_to_sales_ratio = db.Column(db.Float, default=1.0)
    price_gap_exposure = db.Column(db.Float, default=0.0)  # % price gap
    compliance_flags = db.Column(db.Integer, default=0)
    risk_score = db.Column(db.Float, default=0.0)  # 0–100
    risk_tier = db.Column(db.String(20), default="Monitor")  # Monitor/Flag/Audit/Hold

    def to_dict(self):
        return {
            "distributor_id": self.distributor_id,
            "name": self.name,
            "region": self.region,
            "country": self.country,
            "tier": self.tier,
            "allocation_volume": self.allocation_volume,
            "sales_velocity": self.sales_velocity,
            "order_to_sales_ratio": self.order_to_sales_ratio,
            "price_gap_exposure": self.price_gap_exposure,
            "compliance_flags": self.compliance_flags,
            "risk_score": round(self.risk_score, 1),
            "risk_tier": self.risk_tier,
        }


class MarketplaceListing(db.Model):
    __tablename__ = "marketplace_listings"

    listing_id = db.Column(db.String(30), primary_key=True)
    platform = db.Column(db.String(50), nullable=False)
    seller_id = db.Column(db.String(30), nullable=False)
    seller_name = db.Column(db.String(80))
    product_sku = db.Column(db.String(20), db.ForeignKey("products.sku"), nullable=False)
    listed_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(5), nullable=False)
    msrp_equivalent = db.Column(db.Float)
    price_deviation_pct = db.Column(db.Float, default=0.0)
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(120))
    risk_level = db.Column(db.String(20), default="Low")  # Low/Medium/High/Critical
    confidence = db.Column(db.Float, default=0.0)  # 0–1
    detection_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    region = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Active")  # Active/Removed/Under Review

    def to_dict(self):
        return {
            "listing_id": self.listing_id,
            "platform": self.platform,
            "seller_id": self.seller_id,
            "seller_name": self.seller_name,
            "product_sku": self.product_sku,
            "product_name": self.product.product_name if self.product else "Unknown",
            "maison": self.product.maison if self.product else "Unknown",
            "listed_price": self.listed_price,
            "currency": self.currency,
            "msrp_equivalent": self.msrp_equivalent,
            "price_deviation_pct": round(self.price_deviation_pct, 1),
            "is_flagged": self.is_flagged,
            "flag_reason": self.flag_reason,
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 2),
            "detection_timestamp": self.detection_timestamp.strftime("%Y-%m-%d %H:%M"),
            "region": self.region,
            "status": self.status,
        }


class PriceAnomaly(db.Model):
    __tablename__ = "price_anomalies"

    event_id = db.Column(db.String(30), primary_key=True)
    product_sku = db.Column(db.String(20), db.ForeignKey("products.sku"), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    expected_msrp = db.Column(db.Float, nullable=False)
    detected_resale_price = db.Column(db.Float, nullable=False)
    gap_pct = db.Column(db.Float, nullable=False)
    arbitrage_potential_usd = db.Column(db.Float, default=0.0)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(20), default="Medium")  # Low/Medium/High/Critical

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "product_sku": self.product_sku,
            "product_name": self.product.product_name if self.product else "Unknown",
            "maison": self.product.maison if self.product else "Unknown",
            "region": self.region,
            "expected_msrp": self.expected_msrp,
            "detected_resale_price": self.detected_resale_price,
            "gap_pct": round(self.gap_pct, 1),
            "arbitrage_potential_usd": round(self.arbitrage_potential_usd, 2),
            "detected_at": self.detected_at.strftime("%Y-%m-%d %H:%M"),
            "severity": self.severity,
        }


class DiversionAlert(db.Model):
    __tablename__ = "diversion_alerts"

    alert_id = db.Column(db.String(30), primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default="Medium")
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    region = db.Column(db.String(50))
    maison = db.Column(db.String(50))
    estimated_impact_usd = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="Open")  # Open/Investigating/Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "region": self.region,
            "maison": self.maison,
            "estimated_impact_usd": round(self.estimated_impact_usd, 2),
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }
