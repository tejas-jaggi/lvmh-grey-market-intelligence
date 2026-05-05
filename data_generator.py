"""
data_generator.py — Synthetic LVMH Grey Market Data Generator
Creates realistic mock data for Products, Distributors, Listings, Anomalies, Alerts
Run this once after creating the DB to seed all tables.
"""

import random
import string
from datetime import datetime, timedelta
from database import db, Product, Distributor, MarketplaceListing, PriceAnomaly, DiversionAlert

# ── Seed for reproducibility ─────────────────────────────────────────────────
random.seed(42)

# ── LVMH Maisons & Product Catalog ───────────────────────────────────────────
MAISONS = {
    "Louis Vuitton": {
        "categories": ["Handbags", "Small Leather Goods", "Accessories", "Shoes"],
        "price_range": (800, 8500),
        "products": [
            "Neverfull MM", "Speedy 30", "Pochette Métis", "Alma BB",
            "Dauphine MM", "OnTheGo GM", "Twist MM", "Capucines BB",
            "Card Holder", "Key Pouch", "Zippy Wallet", "Chain Louise",
        ],
    },
    "Christian Dior": {
        "categories": ["Handbags", "Ready-to-Wear", "Accessories", "Jewelry"],
        "price_range": (900, 9200),
        "products": [
            "Lady Dior", "Book Tote", "Saddle Bag", "30 Montaigne",
            "Bobby Bag", "Caro Bag", "Oblique Tote", "Dior Caro",
        ],
    },
    "Givenchy": {
        "categories": ["Handbags", "Accessories", "Ready-to-Wear"],
        "price_range": (700, 4500),
        "products": [
            "Antigona Soft", "Kenny Bag", "Cut-Out Bag", "4G Bag",
            "Voyou Bag", "Shark Lock", "Top Handle Small",
        ],
    },
    "Celine": {
        "categories": ["Handbags", "Small Leather Goods", "Shoes"],
        "price_range": (800, 5500),
        "products": [
            "Classic Box", "Triomphe Canvas", "Nano Luggage", "Belt Bag",
            "Tabou Bag", "Teen Triomphe", "Bucket 16",
        ],
    },
    "Loewe": {
        "categories": ["Handbags", "Leather Goods", "Accessories"],
        "price_range": (900, 6500),
        "products": [
            "Puzzle Bag", "Hammock Bag", "Gate Bag", "Flamenco Clutch",
            "Amazona 28", "Elephant Pocket", "Balloon Bag",
        ],
    },
    "Fendi": {
        "categories": ["Handbags", "Ready-to-Wear", "Accessories"],
        "price_range": (800, 7200),
        "products": [
            "Baguette", "Peekaboo", "First Bag", "O'Lock",
            "Sunshine Shopper", "Iconic Baguette", "Mini Sunshine",
        ],
    },
    "Bulgari": {
        "categories": ["Jewelry", "Watches", "Accessories"],
        "price_range": (1200, 25000),
        "products": [
            "Serpenti Viper Ring", "B.zero1 Ring", "Fiorever Necklace",
            "Bulgari Bulgari Watch", "Octo Finissimo", "Serpenti Tubogas",
        ],
    },
    "TAG Heuer": {
        "categories": ["Watches", "Accessories"],
        "price_range": (1800, 18000),
        "products": [
            "Carrera Chronograph", "Monaco Calibre", "Formula 1 Watch",
            "Aquaracer Professional", "Connected Watch", "Autavia",
        ],
    },
}

PLATFORMS = [
    "Dewu (得物)", "Vestiaire Collective", "StockX", "eBay", "Rebag",
    "The RealReal", "Poshmark", "Mercari", "Depop", "Taobao (淘宝)", "Xianyu (闲鱼)"
]

REGIONS = [
    "Greater China", "Southeast Asia", "Middle East", "Eastern Europe",
    "North America", "Western Europe", "Japan & Korea", "Latin America",
    "Africa", "South Asia"
]

COUNTRIES_BY_REGION = {
    "Greater China": ["China", "Hong Kong", "Macau", "Taiwan"],
    "Southeast Asia": ["Singapore", "Thailand", "Malaysia", "Vietnam", "Indonesia"],
    "Middle East": ["UAE", "Saudi Arabia", "Qatar", "Kuwait"],
    "Eastern Europe": ["Russia", "Poland", "Ukraine", "Czech Republic"],
    "North America": ["USA", "Canada", "Mexico"],
    "Western Europe": ["France", "Germany", "Italy", "UK", "Spain"],
    "Japan & Korea": ["Japan", "South Korea"],
    "Latin America": ["Brazil", "Argentina", "Chile", "Colombia"],
    "Africa": ["South Africa", "Nigeria", "Kenya"],
    "South Asia": ["India", "UAE", "Pakistan"],
}

# Price gap multipliers by region (vs. USD MSRP)
REGIONAL_PRICE_MULTIPLIERS = {
    "Greater China": 1.35,
    "Southeast Asia": 1.15,
    "Middle East": 1.08,
    "Eastern Europe": 1.22,
    "North America": 1.0,
    "Western Europe": 1.05,
    "Japan & Korea": 1.12,
    "Latin America": 1.28,
    "Africa": 1.18,
    "South Asia": 1.32,
}

FLAG_REASONS = [
    "Price 22% below regional MSRP — arbitrage signal",
    "Seller volume spike: 15+ LVMH SKUs listed in 48h",
    "Cross-platform identity match detected",
    "SKU concentration: 8 units same model same day",
    "Geographic clustering — same logistics address as 3 other sellers",
    "Price 31% below floor price — structural diversion",
    "New account with immediate high-volume luxury listings",
    "Shared payment method with flagged distributor",
    "Listing price matches daigou markup pattern",
]

ALERT_TYPES = [
    "Marketplace Surge", "Distributor Anomaly", "Price Floor Breach",
    "Seller Network Detected", "Allocation Mismatch", "Cross-Region Arbitrage"
]

DISTRIBUTOR_NAMES = [
    "Pacific Luxury Trading Co.", "Horizon Brands Asia", "Éclat Distribution",
    "Golden Gate Luxury", "Silk Road Partners", "Meridian Trade Group",
    "Summit Luxury Imports", "Azure Channel Partners", "Prestige Global",
    "Pinnacle Distribution HK", "Regent Luxury Services", "Apex Brands MENA",
    "Sterling Luxury Network", "Crest Distribution SE", "Maison Alliance Group",
    "Alliance Luxury EU", "Luxe Connect GmbH", "Orient Express Retail",
    "Delta Luxury Holdings", "Nova Prestige Corp", "Crown Trade International",
    "Vanguard Luxury ME", "Royale Distribution SA", "Constellation Partners",
    "Harvest Luxury Inc.", "Cascade Brands KK", "Imperial Luxury Co.",
    "Oasis Trading FZCO", "Pinnacle Retail India", "Luxuria Brasil",
]


def _rand_sku(maison_code, n):
    return f"{maison_code}-{''.join(random.choices(string.digits, k=5))}-{n:03d}"


def generate_products():
    """Seed ~75 LVMH products across 8 Maisons."""
    products = []
    counter = 1
    for maison, data in MAISONS.items():
        code = maison.replace(" ", "").upper()[:3]
        lo, hi = data["price_range"]
        for pname in data["products"]:
            usd = round(random.uniform(lo, hi), -1)  # round to nearest 10
            eur = round(usd * 0.92, -1)
            cny = round(usd * 7.28 * random.uniform(1.25, 1.42), -1)
            cat = random.choice(data["categories"])
            limited = random.random() < 0.15
            year = random.randint(2018, 2024)
            sku = _rand_sku(code, counter)
            products.append(
                Product(
                    sku=sku,
                    maison=maison,
                    product_name=pname,
                    category=cat,
                    msrp_usd=usd,
                    msrp_eur=eur,
                    msrp_cny=cny,
                    is_limited_edition=limited,
                    launch_year=year,
                )
            )
            counter += 1
    db.session.bulk_save_objects(products)
    db.session.commit()
    print(f"  [ok] Generated {len(products)} products")
    return products


def generate_distributors():
    """Seed 30 distributors with realistic risk profiles."""
    distributors = []
    for i, name in enumerate(DISTRIBUTOR_NAMES):
        region = random.choice(REGIONS)
        country = random.choice(COUNTRIES_BY_REGION[region])
        tier = random.choices(["Platinum", "Gold", "Silver"], weights=[0.2, 0.4, 0.4])[0]
        alloc = random.randint(200, 3500)
        velocity = round(random.uniform(0.4, 1.6) * alloc / 30, 1)
        osr = round(alloc / max(velocity * 30, 1) * random.uniform(0.8, 1.8), 2)
        gap = round(REGIONAL_PRICE_MULTIPLIERS.get(region, 1.1) - 1.0 + random.uniform(-0.05, 0.1), 2)
        flags = random.choices([0, 1, 2, 3, 4], weights=[0.4, 0.25, 0.2, 0.1, 0.05])[0]

        # Risk score formula (simplified)
        score = min(100, max(0,
            flags * 18 +
            max(0, (osr - 1.0) * 30) +
            max(0, gap * 80) +
            random.uniform(-8, 8)
        ))
        if score < 41:
            tier_label = "Monitor"
        elif score < 66:
            tier_label = "Flag for Review"
        elif score < 86:
            tier_label = "Trigger Audit"
        else:
            tier_label = "Hold Shipment"

        distributors.append(
            Distributor(
                distributor_id=f"DIST-{i+1:04d}",
                name=name,
                region=region,
                country=country,
                tier=tier,
                allocation_volume=alloc,
                sales_velocity=velocity,
                order_to_sales_ratio=round(osr, 2),
                price_gap_exposure=round(gap * 100, 1),
                compliance_flags=flags,
                risk_score=round(score, 1),
                risk_tier=tier_label,
            )
        )
    db.session.bulk_save_objects(distributors)
    db.session.commit()
    print(f"  [ok] Generated {len(distributors)} distributors")
    return distributors


def generate_listings(products, n=520):
    """Seed marketplace listings with realistic diversion signals."""
    listings = []
    base_dt = datetime.utcnow() - timedelta(days=30)

    skus = [p.sku for p in products]
    msrp_map = {p.sku: p.msrp_usd for p in products}
    maison_map = {p.sku: p.maison for p in products}

    for i in range(n):
        sku = random.choice(skus)
        msrp = msrp_map[sku]
        platform = random.choice(PLATFORMS)
        region = random.choice(REGIONS)

        # Simulate real-world price distribution
        deviation = random.choices(
            ["normal", "slight_under", "heavy_under", "arbitrage"],
            weights=[0.35, 0.30, 0.20, 0.15]
        )[0]

        if deviation == "normal":
            factor = random.uniform(0.96, 1.12)
            is_flagged = False
            risk = "Low"
            flag_reason = None
            confidence = random.uniform(0.05, 0.25)
        elif deviation == "slight_under":
            factor = random.uniform(0.83, 0.95)
            is_flagged = random.random() < 0.4
            risk = "Medium"
            flag_reason = random.choice(FLAG_REASONS[:3]) if is_flagged else None
            confidence = random.uniform(0.30, 0.60)
        elif deviation == "heavy_under":
            factor = random.uniform(0.65, 0.82)
            is_flagged = True
            risk = "High"
            flag_reason = random.choice(FLAG_REASONS)
            confidence = random.uniform(0.60, 0.85)
        else:  # arbitrage
            factor = random.uniform(0.50, 0.68)
            is_flagged = True
            risk = "Critical"
            flag_reason = random.choice(FLAG_REASONS[-4:])
            confidence = random.uniform(0.82, 0.99)

        listed_price = round(msrp * factor, 2)
        dev_pct = round((factor - 1) * 100, 1)
        detected_at = base_dt + timedelta(
            days=random.randint(0, 29),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        seller_id = f"SLR-{''.join(random.choices(string.ascii_uppercase + string.digits, k=8))}"
        seller_name = f"{''.join(random.choices(string.ascii_uppercase, k=3))}_luxury_{random.randint(10,99)}"

        listings.append(
            MarketplaceListing(
                listing_id=f"LST-{i+1:05d}",
                platform=platform,
                seller_id=seller_id,
                seller_name=seller_name,
                product_sku=sku,
                listed_price=listed_price,
                currency="USD",
                msrp_equivalent=msrp,
                price_deviation_pct=dev_pct,
                is_flagged=is_flagged,
                flag_reason=flag_reason,
                risk_level=risk,
                confidence=confidence,
                detection_timestamp=detected_at,
                region=region,
                status=random.choices(
                    ["Active", "Under Review", "Removed"],
                    weights=[0.65, 0.20, 0.15]
                )[0],
            )
        )

    db.session.bulk_save_objects(listings)
    db.session.commit()
    flagged = sum(1 for l in listings if l.is_flagged)
    print(f"  [ok] Generated {len(listings)} listings ({flagged} flagged)")
    return listings


def generate_price_anomalies(products, n=200):
    """Seed price anomaly events showing cross-regional gaps."""
    anomalies = []
    base_dt = datetime.utcnow() - timedelta(days=30)

    for i in range(n):
        product = random.choice(products)
        region = random.choice(REGIONS)
        multiplier = REGIONAL_PRICE_MULTIPLIERS.get(region, 1.1)
        expected = round(product.msrp_usd * multiplier, 2)
        gap_factor = random.uniform(0.55, 0.92)
        detected = round(expected * gap_factor, 2)
        gap_pct = round((1 - gap_factor) * 100, 1)
        arbitrage = round((expected - detected) * random.randint(1, 25), 2)
        severity = (
            "Critical" if gap_pct > 35 else
            "High" if gap_pct > 25 else
            "Medium" if gap_pct > 15 else "Low"
        )

        anomalies.append(
            PriceAnomaly(
                event_id=f"ANO-{i+1:05d}",
                product_sku=product.sku,
                region=region,
                expected_msrp=expected,
                detected_resale_price=detected,
                gap_pct=gap_pct,
                arbitrage_potential_usd=arbitrage,
                detected_at=base_dt + timedelta(days=random.randint(0, 29)),
                severity=severity,
            )
        )

    db.session.bulk_save_objects(anomalies)
    db.session.commit()
    print(f"  [ok] Generated {len(anomalies)} price anomaly events")


def generate_alerts(n=40):
    """Seed high-level diversion alert feed."""
    alerts = []
    base_dt = datetime.utcnow() - timedelta(days=14)

    alert_templates = [
        ("Marketplace Surge", "High",
         "{maison}: Listing volume spike on {platform}",
         "Detected {n}x increase in {maison} listings on {platform} vs. 7-day average. Possible coordinated reseller network activity in {region}.",
         30000),
        ("Distributor Anomaly", "Critical",
         "DIST-{id}: Order-to-sales ratio exceeds 2.1x threshold",
         "Distributor in {region} placed orders 2.1x above their regional POS velocity. Allocation hold recommended pending investigation.",
         85000),
        ("Price Floor Breach", "High",
         "{maison} {product}: Floor price breach on {platform}",
         "Product listed at {gap}% below regional MSRP floor. Arbitrage signal consistent with grey market distribution pattern.",
         22000),
        ("Seller Network Detected", "Critical",
         "Coordinated reseller cluster identified — {n} accounts",
         "NLP seller analysis identified {n} linked accounts using shared logistics addresses and payment fingerprints. Likely daigou network operating in {region}.",
         120000),
        ("Allocation Mismatch", "Medium",
         "{region}: Inventory-to-demand misalignment flagged",
         "Region received {pct}% excess allocation vs. sell-through velocity. Historical pattern precedes grey market surge within 45 days.",
         45000),
        ("Cross-Region Arbitrage", "High",
         "{maison}: {gap}% price gap between {r1} and {r2}",
         "Price differential of {gap}% between {r1} and {r2} creating structural arbitrage. Consistent with detected resale volume on Dewu and Vestiaire.",
         67000),
    ]

    for i in range(n):
        tpl = random.choice(alert_templates)
        maison = random.choice(list(MAISONS.keys()))
        platform = random.choice(PLATFORMS)
        region1 = random.choice(REGIONS)
        region2 = random.choice([r for r in REGIONS if r != region1])
        gap = random.randint(18, 38)
        n_val = random.randint(4, 22)
        pct = random.randint(28, 65)
        dist_id = random.randint(1, 30)
        product = random.choice(list(MAISONS[maison]["products"]))

        fmt_kwargs = dict(
            maison=maison, platform=platform, id=dist_id,
            product=product, region=region1, r1=region1, r2=region2,
            gap=gap, n=n_val, pct=pct
        )
        title = tpl[2].format(**fmt_kwargs)
        desc  = tpl[3].format(**fmt_kwargs)
        impact = tpl[-1] * random.uniform(0.5, 2.0)
        severity = tpl[1]

        alerts.append(
            DiversionAlert(
                alert_id=f"ALT-{i+1:04d}",
                alert_type=tpl[0],
                severity=severity,
                title=title,
                description=desc,
                region=region1,
                maison=maison,
                estimated_impact_usd=round(impact, 2),
                status=random.choices(["Open", "Investigating", "Resolved"], weights=[0.5, 0.3, 0.2])[0],
                created_at=base_dt + timedelta(days=random.randint(0, 13), hours=random.randint(0, 23)),
            )
        )

    db.session.bulk_save_objects(alerts)
    db.session.commit()
    print(f"  [ok] Generated {len(alerts)} diversion alerts")


def seed_all():
    """Master function — seeds all tables in order."""
    print("\n[seed] Seeding LVMH prototype database...\n")
    db.drop_all()
    db.create_all()

    products = generate_products()
    generate_distributors()
    generate_listings(products)
    generate_price_anomalies(products)
    generate_alerts()

    print("\n[ok] Database seeded successfully.\n")
