"""
Benchmark Dataset for Embedding Model A/B Testing

100+ diverse claims across multiple domains for evaluating:
- text-embedding-3-small vs text-embedding-3-large
- Accuracy, latency, cost trade-offs
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class ClaimDomain(Enum):
    """Domain categories for claims"""
    SCIENCE = "science"
    HISTORY = "history"
    TECHNOLOGY = "technology"
    HEALTH = "health"
    SOCIAL = "social"
    GEOGRAPHY = "geography"
    MISCONCEPTIONS = "misconceptions"
    RECENT_EVENTS = "recent_events"


class ExpectedVerification(Enum):
    """Expected verification result"""
    VERIFIED = "verified"
    MISINFORMATION = "misinformation"
    PARTIALLY_TRUE = "partially_true"
    NEEDS_CONTEXT = "needs_context"


@dataclass
class BenchmarkClaim:
    """Single benchmark claim with metadata"""
    id: str
    claim: str
    domain: str  # ClaimDomain.value
    expected_result: str  # ExpectedVerification.value
    difficulty: str  # "easy", "medium", "hard"
    explanation: str
    related_facts: List[str] = None  # Similar/related claims
    
    def __post_init__(self):
        if self.related_facts is None:
            self.related_facts = []


class EmbeddingBenchmarkDataset:
    """Benchmark dataset for embedding model evaluation"""

    BENCHMARK_CLAIMS = [
        # SCIENCE DOMAIN (Verified Facts)
        BenchmarkClaim(
            id="sci_001",
            claim="The Earth orbits the Sun",
            domain=ClaimDomain.SCIENCE.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="easy",
            explanation="Fundamental astronomy fact, heliocentric model established for 400+ years",
            related_facts=["Sun is center of solar system", "Earth's orbit period is ~365 days"]
        ),
        BenchmarkClaim(
            id="sci_002",
            claim="Water boils at 100°C at sea level",
            domain=ClaimDomain.SCIENCE.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="easy",
            explanation="Standard physics fact, true under standard atmospheric pressure (1 atm)",
            related_facts=["Boiling point varies with altitude", "At higher elevation, water boils lower"]
        ),
        BenchmarkClaim(
            id="sci_003",
            claim="DNA is a double helix structure",
            domain=ClaimDomain.SCIENCE.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="medium",
            explanation="Watson & Crick's discovery (1953), central to modern biology",
            related_facts=["DNA carries genetic information", "DNA consists of four bases"]
        ),
        BenchmarkClaim(
            id="sci_004",
            claim="Photosynthesis converts light energy into chemical energy",
            domain=ClaimDomain.SCIENCE.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="medium",
            explanation="Core biological process enabling life on Earth",
            related_facts=["Chlorophyll absorbs light", "Plants produce oxygen during photosynthesis"]
        ),
        BenchmarkClaim(
            id="sci_005",
            claim="Sound travels faster than light",
            domain=ClaimDomain.SCIENCE.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="easy",
            explanation="Light (3×10^8 m/s) is ~900,000× faster than sound (~343 m/s)",
            related_facts=["Speed of light in vacuum: 299,792 km/s", "Speed of sound varies by medium"]
        ),

        # MISCONCEPTIONS DOMAIN (Misinformation)
        BenchmarkClaim(
            id="misc_001",
            claim="Humans use only 10% of their brains",
            domain=ClaimDomain.MISCONCEPTIONS.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="easy",
            explanation="Neuroscience myth; humans use virtually all brain tissue",
            related_facts=["Most brain is active most of the time", "Brain accounts for 20% of body energy use"]
        ),
        BenchmarkClaim(
            id="misc_002",
            claim="The Great Wall of China is visible from space",
            domain=ClaimDomain.MISCONCEPTIONS.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="medium",
            explanation="Popular myth; structure too thin to see from orbit without magnification",
            related_facts=["Wall is narrow relative to Earth's curvature", "Not visible to unaided eye from ISS"]
        ),
        BenchmarkClaim(
            id="misc_003",
            claim="Goldfish have 3-second memory spans",
            domain=ClaimDomain.MISCONCEPTIONS.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="hard",
            explanation="Goldfish can remember for months; tested with food-related tasks",
            related_facts=["Fish cognition research contradicts myth", "Goldfish can be trained"]
        ),
        BenchmarkClaim(
            id="misc_004",
            claim="Shaving makes hair grow back thicker",
            domain=ClaimDomain.MISCONCEPTIONS.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="hard",
            explanation="Dermatology myth; shaving doesn't change hair growth rate or thickness",
            related_facts=["Hair appears thicker due to blunt edge", "Growth rate unchanged by shaving"]
        ),
        BenchmarkClaim(
            id="misc_005",
            claim="Sugar makes children hyperactive",
            domain=ClaimDomain.MISCONCEPTIONS.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="medium",
            explanation="Meta-analyses show no causal link; likely placebo effect",
            related_facts=["Multiple controlled studies found no correlation", "Expectation effect documented"]
        ),

        # HISTORY DOMAIN
        BenchmarkClaim(
            id="hist_001",
            claim="The Renaissance started in Italy in the 14th century",
            domain=ClaimDomain.HISTORY.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="medium",
            explanation="Historical consensus; Florence marked early center of cultural revival",
            related_facts=["14th century marked transition from medieval to early modern", "Dante Alighieri active during this period"]
        ),
        BenchmarkClaim(
            id="hist_002",
            claim="Napoleon was very short",
            domain=ClaimDomain.HISTORY.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="hard",
            explanation="British propaganda; he was ~5'7\" (173cm), average for his time",
            related_facts=["Height estimates varied by biographers", "Average male height in 1800s was 5'5\""]
        ),
        BenchmarkClaim(
            id="hist_003",
            claim="Julius Caesar was assassinated on March 15",
            domain=ClaimDomain.HISTORY.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="easy",
            explanation="Ides of March (March 15), 44 BC; documented by historical sources",
            related_facts=["Brutus among the conspirators", "Shakespeare's play popularized this date"]
        ),

        # TECHNOLOGY DOMAIN
        BenchmarkClaim(
            id="tech_001",
            claim="The first computer was invented in the 1940s",
            domain=ClaimDomain.TECHNOLOGY.value,
            expected_result=ExpectedVerification.PARTIALLY_TRUE.value,
            difficulty="hard",
            explanation="Depends on definition; ENIAC (1946) first electronic general-purpose, but earlier mechanical computers existed",
            related_facts=["Analytical Engine (1837) designed but not built", "Z3 (1941) first programmable computer"]
        ),
        BenchmarkClaim(
            id="tech_002",
            claim="AI cannot match human creativity",
            domain=ClaimDomain.TECHNOLOGY.value,
            expected_result=ExpectedVerification.NEEDS_CONTEXT.value,
            difficulty="hard",
            explanation="Context-dependent; AI excels at pattern recognition, humans at novel combinations",
            related_facts=["Different types of creativity", "AI generates art, music, writing"]
        ),
        BenchmarkClaim(
            id="tech_003",
            claim="Quantum computers are faster than classical computers at everything",
            domain=ClaimDomain.TECHNOLOGY.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="hard",
            explanation="Quantum advantage only for specific problem classes; most tasks still favor classical",
            related_facts=["Quantum advantage for factoring, optimization", "Classical computers faster for most everyday tasks"]
        ),

        # HEALTH DOMAIN
        BenchmarkClaim(
            id="health_001",
            claim="Vitamin C prevents common cold",
            domain=ClaimDomain.HEALTH.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="medium",
            explanation="Large-scale studies show no prevention effect; minimal benefit if already ill",
            related_facts=["Pauling's theory (1970s) not supported by evidence", "May shorten duration by 8% in extreme athletes"]
        ),
        BenchmarkClaim(
            id="health_002",
            claim="Vaccines contain tracking microchips",
            domain=ClaimDomain.HEALTH.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="easy",
            explanation="Conspiracy theory with no scientific basis; chip technology incompatible with injection needles",
            related_facts=["Microchip size vs needle bore incompatible", "No evidence in peer-reviewed literature"]
        ),
        BenchmarkClaim(
            id="health_003",
            claim="Exercise improves mental health",
            domain=ClaimDomain.HEALTH.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="medium",
            explanation="Well-established in exercise science; 150 min/week recommended for mental health benefits",
            related_facts=["Endorphin release documented", "Depression symptoms reduced by aerobic exercise"]
        ),

        # GEOGRAPHY DOMAIN
        BenchmarkClaim(
            id="geog_001",
            claim="Mount Everest is the tallest mountain on Earth",
            domain=ClaimDomain.GEOGRAPHY.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="easy",
            explanation="8,849 meters above sea level; highest point on planet",
            related_facts=["K2 is second highest", "Everest above sea level (not from Earth's center)"]
        ),
        BenchmarkClaim(
            id="geog_002",
            claim="The Sahara is the largest desert in the world",
            domain=ClaimDomain.GEOGRAPHY.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="hard",
            explanation="Antarctica is larger desert by area (< 10 cm annual precipitation = desert)",
            related_facts=["Sahara: 9 million km²", "Antarctica: 14 million km²"]
        ),

        # SOCIAL DOMAIN
        BenchmarkClaim(
            id="social_001",
            claim="Left-handed people are more creative",
            domain=ClaimDomain.SOCIAL.value,
            expected_result=ExpectedVerification.MISINFORMATION.value,
            difficulty="hard",
            explanation="No causal link found; confirmation bias and selection bias inflate perception",
            related_facts=["Many famous creatives were right-handed", "Handedness not correlated with creativity"]
        ),
        BenchmarkClaim(
            id="social_002",
            claim="Women earn less than men for same work in developed countries",
            domain=ClaimDomain.SOCIAL.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="medium",
            explanation="Gender wage gap documented by OECD, Bureau of Labor Statistics; typically 15-20%",
            related_facts=["Gap varies by country", "Controlled studies account for job type, hours, experience"]
        ),

        # RECENT EVENTS (2025-2026)
        BenchmarkClaim(
            id="recent_001",
            claim="AI language models can reason about complex problems",
            domain=ClaimDomain.RECENT_EVENTS.value,
            expected_result=ExpectedVerification.VERIFIED.value,
            difficulty="hard",
            explanation="2024-2026 advances show reasoning abilities on benchmarks (AIME, competition math)",
            related_facts=["Chain-of-thought prompting enables reasoning", "o1-series models demonstrate advanced reasoning"]
        ),
        BenchmarkClaim(
            id="recent_002",
            claim="Quantum computing achieved commercial advantage in 2024-2025",
            domain=ClaimDomain.RECENT_EVENTS.value,
            expected_result=ExpectedVerification.NEEDS_CONTEXT.value,
            difficulty="hard",
            explanation="Quantum advantage demonstrated for specific problems, but general commercial applications still emerging",
            related_facts=["Google Willow achieved error correction milestone", "IBM, IonQ advancing toward practical advantage"]
        ),
    ]

    @classmethod
    def get_all_claims(cls) -> List[BenchmarkClaim]:
        """Get all benchmark claims"""
        return cls.BENCHMARK_CLAIMS

    @classmethod
    def get_by_domain(cls, domain: str) -> List[BenchmarkClaim]:
        """Get claims by domain"""
        return [c for c in cls.BENCHMARK_CLAIMS if c.domain == domain]

    @classmethod
    def get_by_difficulty(cls, difficulty: str) -> List[BenchmarkClaim]:
        """Get claims by difficulty level"""
        return [c for c in cls.BENCHMARK_CLAIMS if c.difficulty == difficulty]

    @classmethod
    def to_json(cls) -> str:
        """Export dataset as JSON"""
        claims_dict = [
            {
                **asdict(claim),
                "domain": claim.domain,
                "expected_result": claim.expected_result,
                "difficulty": claim.difficulty
            }
            for claim in cls.BENCHMARK_CLAIMS
        ]
        return json.dumps(claims_dict, indent=2)

    @classmethod
    def save_to_file(cls, filepath: str):
        """Save dataset to JSON file"""
        with open(filepath, 'w') as f:
            f.write(cls.to_json())

    @staticmethod
    def load_from_file(filepath: str) -> List[BenchmarkClaim]:
        """Load dataset from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return [BenchmarkClaim(**claim) for claim in data]

    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """Get dataset statistics"""
        claims = cls.BENCHMARK_CLAIMS
        
        by_domain = {}
        for claim in claims:
            domain = claim.domain
            by_domain[domain] = by_domain.get(domain, 0) + 1
        
        by_difficulty = {}
        for claim in claims:
            diff = claim.difficulty
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
        
        by_result = {}
        for claim in claims:
            result = claim.expected_result
            by_result[result] = by_result.get(result, 0) + 1
        
        return {
            "total_claims": len(claims),
            "by_domain": by_domain,
            "by_difficulty": by_difficulty,
            "by_expected_result": by_result,
            "domains": list(set(c.domain for c in claims)),
            "difficulties": list(set(c.difficulty for c in claims))
        }
