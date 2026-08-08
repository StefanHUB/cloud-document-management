"""
Region catalog with cost and carbon intensity data for cloud regions.
This module powers the cost-aware and carbon-aware region selection feature.
"""

from dataclasses import dataclass, asdict
from typing import List


@dataclass
class CloudRegion:
    """Represents a cloud region with cost and sustainability metrics."""
    region_id: str          # GCP region identifier
    name: str               # Human-readable name
    location: str           # Geographic location
    cost_per_gb_month: float  # Storage cost in USD per GB per month
    carbon_intensity: float   # gCO2eq/kWh (grid carbon intensity)
    renewable_pct: float      # Percentage of renewable energy
    latency_ms: int           # Average latency from London (ms)
    provider: str             # Cloud provider

    @property
    def sustainability_score(self) -> float:
        """Higher is better. Combines low carbon + high renewable."""
        return (100.0 - self.carbon_intensity) * 0.6 + self.renewable_pct * 0.4

    @property
    def cost_score(self) -> float:
        """Higher is better (lower cost = higher score)."""
        return 100.0 - (self.cost_per_gb_month * 10.0)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["sustainability_score"] = round(self.sustainability_score, 1)
        d["cost_score"] = round(self.cost_score, 1)
        return d


# Region catalogue based on published GCP pricing and carbon-aware data
# Sources: Google Cloud pricing page; Electricity Maps carbon intensity data
REGIONS: List[CloudRegion] = [
    CloudRegion(
        region_id="europe-west1",
        name="Europe West 1",
        location="St. Ghislain, Belgium",
        cost_per_gb_month=0.020,
        carbon_intensity=120.0,
        renewable_pct=35.0,
        latency_ms=8,
        provider="Google Cloud",
    ),
    CloudRegion(
        region_id="europe-north1",
        name="Europe North 1",
        location="Hamina, Finland",
        cost_per_gb_month=0.020,
        carbon_intensity=45.0,
        renewable_pct=85.0,
        latency_ms=15,
        provider="Google Cloud",
    ),
    CloudRegion(
        region_id="us-central1",
        name="US Central 1",
        location="Council Bluffs, Iowa",
        cost_per_gb_month=0.020,
        carbon_intensity=380.0,
        renewable_pct=20.0,
        latency_ms=90,
        provider="Google Cloud",
    ),
    CloudRegion(
        region_id="us-east1",
        name="US East 1",
        location="Moncks Corner, South Carolina",
        cost_per_gb_month=0.020,
        carbon_intensity=420.0,
        renewable_pct=15.0,
        latency_ms=95,
        provider="Google Cloud",
    ),
    CloudRegion(
        region_id="europe-west4",
        name="Europe West 4",
        location="Eemshaven, Netherlands",
        cost_per_gb_month=0.023,
        carbon_intensity=280.0,
        renewable_pct=40.0,
        latency_ms=10,
        provider="Google Cloud",
    ),
    CloudRegion(
        region_id="asia-southeast1",
        name="Asia Southeast 1",
        location="Singapore",
        cost_per_gb_month=0.026,
        carbon_intensity=410.0,
        renewable_pct=10.0,
        latency_ms=170,
        provider="Google Cloud",
    ),
    CloudRegion(
        region_id="southamerica-east1",
        name="South America East 1",
        location="São Paulo, Brazil",
        cost_per_gb_month=0.027,
        carbon_intensity=60.0,
        renewable_pct=80.0,
        latency_ms=180,
        provider="Google Cloud",
    ),
    CloudRegion(
        region_id="australia-southeast1",
        name="Australia Southeast 1",
        location="Sydney, Australia",
        cost_per_gb_month=0.028,
        carbon_intensity=530.0,
        renewable_pct=12.0,
        latency_ms=250,
        provider="Google Cloud",
    ),
]


def get_all_regions() -> List[dict]:
    """Return all regions as dictionaries."""
    return [r.to_dict() for r in REGIONS]


def recommend_regions(mode: str = "cost") -> dict:
    """
    Recommend regions based on the selected mode.

    Args:
        mode: 'cost' for cost-aware selection, 'carbon' for carbon-aware selection

    Returns:
        Dictionary with recommended region, rationale, and comparison data
    """
    if mode == "cost":
        ranked = sorted(REGIONS, key=lambda r: r.cost_per_gb_month)
        recommended = ranked[0]
        rationale = (
            f"Selected {recommended.name} ({recommended.region_id}) because it has "
            f"the lowest storage cost at ${recommended.cost_per_gb_month:.3f}/GB/month. "
            f"While multiple regions share the same base storage rate, this region "
            f"also offers reasonable latency ({recommended.latency_ms}ms from UK) "
            f"and {recommended.renewable_pct:.0f}% renewable energy usage."
        )
        metric = "cost_per_gb_month"
        metric_label = "Cost (USD/GB/month)"
    elif mode == "carbon":
        ranked = sorted(REGIONS, key=lambda r: r.sustainability_score, reverse=True)
        recommended = ranked[0]
        rationale = (
            f"Selected {recommended.name} ({recommended.region_id}) because it has "
            f"the best sustainability profile with a carbon intensity of "
            f"{recommended.carbon_intensity:.0f} gCO2eq/kWh and "
            f"{recommended.renewable_pct:.0f}% renewable energy usage. "
            f"The sustainability score is {recommended.sustainability_score:.1f}/100."
        )
        metric = "sustainability_score"
        metric_label = "Sustainability Score (/100)"
    else:
        return {"error": f"Unknown mode: {mode}. Use 'cost' or 'carbon'."}

    return {
        "mode": mode,
        "mode_label": "Cost-Aware" if mode == "cost" else "Carbon-Aware",
        "recommended_region": recommended.to_dict(),
        "rationale": rationale,
        "metric": metric,
        "metric_label": metric_label,
        "all_regions_ranked": [r.to_dict() for r in ranked],
    }
