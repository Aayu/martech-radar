from datetime import datetime, timezone

from radar.ranking import rank


NOW = datetime(2026, 11, 15, tzinfo=timezone.utc)


def test_scaled_implementation_with_outcomes_beats_generic_campaign():
    opella = rank(
        "How Opella, Microsoft Use Agentic AI to Build Enterprise Content Supply Chain",
        "Opella built an in-house content factory with 14 agents, increased output thirtyfold "
        "and lifted engagement to 50%.",
        {"kind": "publisher", "beats": ["fmcg"]},
        "2026-11-10",
        NOW,
    )
    generic = rank(
        "Netflix embraces 35mm film in international campaign",
        "A film-led international brand campaign celebrates human storytelling.",
        {"kind": "publisher", "beats": ["journey"]},
        "2026-11-10",
        NOW,
    )
    assert opella["priority"] >= 70
    assert "Quantified or business outcome" in opella["signals"]
    assert generic["priority"] == 0
    assert generic["tags"] == []


def test_standard_and_failure_are_leadership_signals():
    standard = rank(
        "IAB unveils framework for measuring AI's part in conversions",
        "The standard classifies AI-assisted conversions and requires evidence for attribution claims.",
        {"kind": "standards", "beats": ["adtech", "regulation"]},
        "2026-11-12",
        NOW,
    )
    failure = rank(
        "Meta's AI ads included unapproved discounts",
        "The platform inserted unapproved offers into live ads, creating a governance failure.",
        {"kind": "publisher", "beats": ["adtech"]},
        "2026-11-12",
        NOW,
    )
    assert standard["priority"] >= 50
    assert standard["evidence"] == "Primary rule or standards source"
    assert failure["priority"] >= 50
    assert "Failure or counter-evidence" in failure["signals"]


def test_partnership_announcement_without_outcome_is_not_shortlisted():
    result = rank(
        "Adobe partners with Disney to develop AI-powered creative tools",
        "The companies announced a strategic alliance to explore tools in the future.",
        {"kind": "platform", "beats": ["adtech", "journey"]},
        "2026-11-10",
        NOW,
    )
    assert result["priority"] < 50
    assert "Quantified or business outcome" not in result["signals"]

