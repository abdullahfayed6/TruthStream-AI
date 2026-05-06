"""
TruthStream AI — In-memory fallback store for demo mode.

When MongoDB is unreachable, this module provides a fully-functional
in-memory data store pre-seeded with realistic demo articles.
The routers detect `app.state.use_fallback` and query this store instead.
"""
from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Any


def _make_id(title: str) -> str:
    return hashlib.sha256(title.encode()).hexdigest()[:24]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------
_DEMO_ARTICLES: list[dict[str, Any]] = [
    {
        "title": "Scientists Discover New Species in Deep Ocean Trenches",
        "source": "Reuters",
        "url": "https://reuters.com/science/deep-ocean-species",
        "author": "Dr. Sarah Chen",
        "content": "Marine biologists from the Monterey Bay Aquarium Research Institute have identified three previously unknown species of bioluminescent fish during a groundbreaking expedition to the Mariana Trench. The discovery, published in Nature Marine Biology, challenges existing assumptions about the depth at which complex life can thrive. The team used advanced remotely operated vehicles equipped with ultra-low-light cameras to document the organisms at depths exceeding 10,000 meters.",
        "label": "Real",
        "confidence": 0.94,
        "category": "Science",
    },
    {
        "title": "BREAKING: World Leaders Secretly Control Weather Using Hidden Technology",
        "source": "SocialBuzz",
        "url": "https://example.com/weather-control",
        "author": None,
        "content": "Anonymous sources within the United Nations have allegedly revealed that a secret coalition of world leaders has been manipulating global weather patterns using satellite-based frequency emitters since 2018. The sources, who cannot be named for security reasons, claim the technology was reverse-engineered from classified military research programs.",
        "label": "Fake",
        "confidence": 0.97,
        "category": "Politics",
    },
    {
        "title": "Tech Giant Reports Record Quarterly Earnings Amid AI Boom",
        "source": "Bloomberg",
        "url": "https://bloomberg.com/tech/quarterly-earnings",
        "author": "Michael Torres",
        "content": "Major technology firm Alphabet Inc. announced a 28% increase in Q1 2026 profits, driven primarily by strong growth in cloud computing services and AI product adoption. Revenue exceeded analyst expectations at $92.4 billion. CEO Sundar Pichai attributed the growth to enterprise AI deployments and the expansion of Google Cloud's infrastructure.",
        "label": "Real",
        "confidence": 0.91,
        "category": "Business",
    },
    {
        "title": "Miracle Cure Found in Common Household Item - Doctors Hate This!",
        "source": "BlogNet",
        "url": "https://example.com/miracle-cure",
        "author": "Health Truth Network",
        "content": "A viral social media post claims that drinking a mixture of baking soda and lemon juice can cure diabetes, cancer, and heart disease overnight. The post, which has been shared over 500,000 times, cites unnamed doctors and references a study that does not exist in any medical database. Medical professionals have universally condemned the claims.",
        "label": "Fake",
        "confidence": 0.99,
        "category": "Health",
    },
    {
        "title": "Federal Reserve Maintains Interest Rates Amid Stable Inflation",
        "source": "AP News",
        "url": "https://apnews.com/fed-interest-rates",
        "author": "Emma Williams",
        "content": "The Federal Reserve announced today that it will maintain the federal funds rate at 4.25-4.50%, citing stable inflation figures and robust employment data. Chair Jerome Powell indicated that the committee sees no immediate need for rate adjustments, though it remains data-dependent. The decision was widely anticipated by financial markets.",
        "label": "Real",
        "confidence": 0.93,
        "category": "Economy",
    },
    {
        "title": "EXPOSED: Famous Actor Running Underground Criminal Network",
        "source": "SocialBuzz",
        "url": "https://example.com/celebrity-exposed",
        "author": None,
        "content": "Unverified claims from an anonymous social media account suggest that a famous Hollywood actor is secretly involved in a vast underground criminal network. The allegations are based entirely on blurry photographs and circumstantial connections that have been debunked by multiple fact-checking organizations.",
        "label": "Fake",
        "confidence": 0.96,
        "category": "Entertainment",
    },
    {
        "title": "City Council Approves $2.3B Public Transit Expansion Plan",
        "source": "CNN",
        "url": "https://localnews.com/transit-expansion",
        "author": "James Park",
        "content": "The Metropolitan Transportation Authority board voted 9-2 to approve a $2.3 billion light rail expansion that will add three new lines serving historically underserved communities in the city's southern and eastern corridors. Construction is expected to begin in Q3 2026 and complete by 2030.",
        "label": "Real",
        "confidence": 0.88,
        "category": "Local",
    },
    {
        "title": "Government Hiding Alien Spacecraft at Secret Base - Leaked Documents Prove It",
        "source": "SocialBuzz",
        "url": "https://example.com/alien-base",
        "author": "Truth Seeker 101",
        "content": "Alleged leaked documents obtained through anonymous channels claim that extraterrestrial spacecraft and beings are being held at an undisclosed military facility in Nevada. The documents, whose authenticity cannot be verified, describe advanced propulsion technology and biological specimens.",
        "label": "Fake",
        "confidence": 0.98,
        "category": "Conspiracy",
    },
    {
        "title": "University Study Links Regular Exercise to 40% Reduction in Anxiety",
        "source": "Reuters",
        "url": "https://sciencedaily.com/exercise-anxiety",
        "author": "Dr. Lisa Martinez",
        "content": "A comprehensive peer-reviewed study published in The Lancet Psychiatry demonstrates a significant correlation between regular physical activity and reduced anxiety symptoms. The study followed 14,000 participants over five years and found that individuals engaging in moderate exercise for 150 minutes per week experienced a 40% reduction in anxiety-related disorders.",
        "label": "Real",
        "confidence": 0.92,
        "category": "Health",
    },
    {
        "title": "Shocking: Common Vaccine Actually Implants Tracking Microchips",
        "source": "BlogNet",
        "url": "https://example.com/vaccine-chips",
        "author": None,
        "content": "A widely debunked conspiracy theory has resurfaced claiming that standard vaccination programs are secretly implanting microscopic tracking devices in recipients. The claim, which contradicts the laws of physics regarding miniaturization, has been thoroughly investigated and rejected by the World Health Organization, the CDC, and independent researchers worldwide.",
        "label": "Fake",
        "confidence": 0.99,
        "category": "Health",
    },
    {
        "title": "International Climate Summit Reaches Historic Emissions Agreement",
        "source": "Reuters",
        "url": "https://bbc.com/climate-summit",
        "author": "Robert Green",
        "content": "World leaders at the COP31 climate summit in Dubai have reached a historic agreement committing to a 60% reduction in carbon emissions by 2035. The agreement, signed by 196 nations, includes binding enforcement mechanisms and a $500 billion climate finance package for developing nations.",
        "label": "Real",
        "confidence": 0.95,
        "category": "Environment",
    },
    {
        "title": "5G Towers Proven to Cause Mind Control - Scientists Silenced!",
        "source": "ViralNews",
        "url": "https://example.com/5g-mind-control",
        "author": "FreeThinker101",
        "content": "Baseless claims about 5G cellular infrastructure affecting human cognition have spread across social media platforms. The post claims that telecommunications companies are suppressing research showing cognitive effects, despite the fact that thousands of independent studies have found no such effects. The International Commission on Non-Ionizing Radiation Protection confirms 5G frequencies are safe.",
        "label": "Fake",
        "confidence": 0.97,
        "category": "Technology",
    },
    {
        "title": "SpaceX Successfully Launches First Mars Cargo Mission",
        "source": "Bloomberg",
        "url": "https://spacenews.com/spacex-mars-cargo",
        "author": "Alex Turner",
        "content": "SpaceX's Starship successfully completed its first unmanned cargo delivery mission to Mars orbit, carrying 150 tons of supplies and equipment for the planned Ares Base. The mission, which launched from Cape Canaveral on May 1, achieved trans-Mars injection flawlessly.",
        "label": "Real",
        "confidence": 0.89,
        "category": "Science",
    },
    {
        "title": "URGENT: Global Banking System to Collapse Within 48 Hours",
        "source": "Reuters",
        "url": "https://example.com/bank-collapse",
        "author": None,
        "content": "An anonymous insider claims the entire global banking system will collapse within 48 hours due to a hidden debt crisis. The post urges readers to withdraw all savings immediately. No credible financial institutions, regulatory bodies, or economists have corroborated these claims.",
        "label": "Fake",
        "confidence": 0.96,
        "category": "Economy",
    },
    {
        "title": "New CRISPR Treatment Shows Promise for Sickle Cell Disease",
        "source": "AP News",
        "url": "https://nih.gov/crispr-sickle-cell",
        "author": "Dr. James Wong",
        "content": "The National Institutes of Health announced promising results from a Phase III clinical trial of a CRISPR-based gene therapy for sickle cell disease. Of 45 patients treated, 42 showed sustained hemoglobin production and elimination of pain crises after 12 months of follow-up.",
        "label": "Real",
        "confidence": 0.96,
        "category": "Health",
    },
    {
        "title": "AI Startup Raises $500M to Build Autonomous Delivery Network",
        "source": "CNN",
        "url": "https://techcrunch.com/ai-delivery-startup",
        "author": "Sarah Kim",
        "content": "Bay Area startup NexDel has raised $500 million in Series C funding led by Sequoia Capital to expand its autonomous delivery drone network to 50 US cities by 2027. The company currently operates in 12 metropolitan areas with a fleet of 3,000 drones completing over 100,000 deliveries monthly.",
        "label": "Real",
        "confidence": 0.87,
        "category": "Technology",
    },
    {
        "title": "Secret Society Controls All Major World Governments - Whistleblower",
        "source": "Bloomberg",
        "url": "https://example.com/secret-society",
        "author": "Anonymous Patriot",
        "content": "A self-proclaimed whistleblower claims that a secret society of 13 families has controlled every major government decision since the 1800s. The claims are presented without any verifiable documentation, named sources, or corroborating evidence.",
        "label": "Fake",
        "confidence": 0.95,
        "category": "Politics",
    },
    {
        "title": "EU Passes Comprehensive AI Regulation Framework",
        "source": "BBC",
        "url": "https://ft.com/eu-ai-regulation",
        "author": "Hans Mueller",
        "content": "The European Parliament has passed the AI Act with a decisive 523-46 vote, establishing the world's most comprehensive regulatory framework for artificial intelligence. The regulation classifies AI systems by risk level and imposes strict requirements on high-risk applications in healthcare, transportation, and law enforcement.",
        "label": "Real",
        "confidence": 0.94,
        "category": "Politics",
    },
    {
        "title": "Eating This One Food Will Make You Immune to All Diseases",
        "source": "BlogNet",
        "url": "https://example.com/miracle-food",
        "author": "Dr. Wellness",
        "content": "A viral blog post claims that consuming raw turmeric root daily provides complete immunity against all known diseases, including cancer and viral infections. The article references no clinical studies and contradicts established medical science. Leading nutritionists have called the claims dangerous misinformation.",
        "label": "Fake",
        "confidence": 0.98,
        "category": "Health",
    },
    {
        "title": "Toyota Unveils Solid-State Battery With 1000km Range",
        "source": "Reuters",
        "url": "https://nikkei.com/toyota-solid-state",
        "author": "Yuki Tanaka",
        "content": "Toyota Motor Corporation unveiled its next-generation solid-state battery technology at the Tokyo Motor Show, demonstrating an electric vehicle with a verified 1,000 km range on a single charge. The battery can be recharged to 80% in just 10 minutes and is expected to enter mass production by 2028.",
        "label": "Real",
        "confidence": 0.90,
        "category": "Technology",
    },
]


def _seed_articles() -> list[dict[str, Any]]:
    """Create demo articles with timestamps spread across the last 24 hours."""
    now = datetime.now(timezone.utc)
    articles = []
    for i, template in enumerate(_DEMO_ARTICLES):
        offset_minutes = random.randint(5, 1440)
        ts = now - timedelta(minutes=offset_minutes)
        article = {
            **template,
            "id": _make_id(template["title"]),
            "published_at": (ts - timedelta(minutes=random.randint(0, 30))).isoformat(),
            "fetched_at": ts.isoformat(),
            "scored_at": (ts + timedelta(seconds=random.randint(5, 30))).isoformat(),
        }
        articles.append(article)
    # Sort newest first
    articles.sort(key=lambda a: a["scored_at"], reverse=True)
    return articles


# ---------------------------------------------------------------------------
# FallbackStore class
# ---------------------------------------------------------------------------

class FallbackStore:
    """
    In-memory store that mimics the MongoDB collection interface
    used by the routers. Pre-seeded with demo articles.
    """

    def __init__(self):
        self.articles: list[dict[str, Any]] = _seed_articles()
        self._article_counter = 0
        print(f"[DEMO] Fallback store initialized with {len(self.articles)} articles")

    # --- Query helpers ---

    def get_articles(
        self,
        label: str = "all",
        source: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        filtered = self.articles
        if label != "all":
            filtered = [a for a in filtered if a["label"] == label]
        if source:
            filtered = [a for a in filtered if source.lower() in a["source"].lower()]

        total = len(filtered)
        skip = (page - 1) * page_size
        page_articles = filtered[skip: skip + page_size]
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, -(-total // page_size)),
            "articles": page_articles,
        }

    def get_article(self, article_id: str) -> dict | None:
        for a in self.articles:
            if a["id"] == article_id:
                return a
        return None

    def get_stats(self) -> dict:
        total = len(self.articles)
        fake = sum(1 for a in self.articles if a["label"] == "Fake")
        real = total - fake

        # Sources
        source_counts: dict[str, int] = {}
        source_fake: dict[str, int] = {}
        for a in self.articles:
            src = a["source"]
            source_counts[src] = source_counts.get(src, 0) + 1
            if a["label"] == "Fake":
                source_fake[src] = source_fake.get(src, 0) + 1

        top_sources = sorted(
            [{"source": s, "count": c} for s, c in source_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        fake_rate_by_source = []
        for src, cnt in source_counts.items():
            fc = source_fake.get(src, 0)
            if cnt >= 1:
                fake_rate_by_source.append({
                    "source": src,
                    "total": cnt,
                    "fake_count": fc,
                    "fake_rate": round(fc / cnt, 3),
                })
        fake_rate_by_source.sort(key=lambda x: x["fake_rate"], reverse=True)

        # Per-source breakdown (real + fake counts) sorted by volume
        source_breakdown = []
        for src, cnt in source_counts.items():
            fc = source_fake.get(src, 0)
            source_breakdown.append({
                "source": src,
                "total": cnt,
                "real": cnt - fc,
                "fake": fc,
            })
        source_breakdown.sort(key=lambda x: x["total"], reverse=True)

        return {
            "total": total,
            "fake": fake,
            "real": real,
            "fake_pct": round(fake / total * 100, 1) if total else 0,
            "real_pct": round(real / total * 100, 1) if total else 0,
            "top_sources": top_sources[:10],
            "fake_rate_by_source": fake_rate_by_source[:10],
            "source_breakdown": source_breakdown[:10],
        }

    def get_timeline(self, hours: int = 24) -> list[dict]:
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=hours)

        buckets: dict[str, dict[str, int]] = {}
        for a in self.articles:
            scored = a.get("scored_at", "")
            if not scored:
                continue
            try:
                ts = datetime.fromisoformat(scored.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue
            if ts < since:
                continue
            hour_key = ts.strftime("%Y-%m-%dT%H:00")
            if hour_key not in buckets:
                buckets[hour_key] = {"hour": hour_key, "fake": 0, "real": 0}
            lbl = a.get("label", "Real").lower()
            if lbl in ("fake", "real"):
                buckets[hour_key][lbl] += 1

        result = sorted(buckets.values(), key=lambda x: x["hour"])
        for row in result:
            row["total"] = row["fake"] + row["real"]
        return result

    def get_new_articles_since(self, since_iso: str) -> list[dict]:
        """Return articles scored after the given ISO timestamp."""
        return [a for a in self.articles if a.get("scored_at", "") > since_iso]
