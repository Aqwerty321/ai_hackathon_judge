"""Sample project code for Project Alpha."""

from __future__ import annotations


def predict_energy_usage(history: list[int]) -> int:
    """Return a naive energy usage prediction based on recent history."""
    if not history:
        return 0
    return round(sum(history[-3:]) / min(len(history), 3))


def recommend_action(prediction: int) -> str:
    """Suggest a simple recommendation based on the predicted usage."""
    if prediction > 80:
        return "Enable eco-mode for HVAC and dim smart lighting."
    if prediction > 50:
        return "Prompt occupants to shift appliance usage to off-peak hours."
    return "Maintain standard automation routines."
