"""DC circuit calculator for basic Ohm's law calculations.

This module can evaluate a single resistor as well as series and parallel
resistor networks using common electrical engineering formulas.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence


def _as_float(value, name: str) -> float:
    """Convert a value to float and reject invalid inputs."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number.") from exc

    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite.")
    return number


def _validate_positive(value, name: str) -> float:
    """Ensure a voltage or resistance value is positive."""
    number = _as_float(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return number


def _validate_resistances(resistances: Iterable[float]) -> list[float]:
    """Normalize a resistance sequence and reject invalid entries."""
    values = []
    for index, resistance in enumerate(resistances, start=1):
        value = _validate_positive(resistance, f"resistance[{index}]")
        values.append(value)
    if not values:
        raise ValueError("At least one resistance value is required.")
    return values


def analyze_dc(voltage_v, resistance_ohm):
    """Calculate current and power for a single resistor using Ohm's law."""
    voltage = _validate_positive(voltage_v, "voltage_v")
    resistance = _validate_positive(resistance_ohm, "resistance_ohm")

    current_a = voltage / resistance
    power_w = voltage * current_a
    return {
        "voltage_v": voltage,
        "resistance_ohm": resistance,
        "current_a": current_a,
        "power_w": power_w,
    }


def calculate_series_resistance(resistances: Sequence[float]) -> float:
    """Return the equivalent resistance of a series circuit."""
    return sum(_validate_resistances(resistances))


def calculate_parallel_resistance(resistances: Sequence[float]) -> float:
    """Return the equivalent resistance of a parallel circuit."""
    values = _validate_resistances(resistances)
    reciprocal_total = sum(1.0 / value for value in values)
    return 1.0 / reciprocal_total


def analyze_series_circuit(voltage_v, resistances: Sequence[float]):
    """Analyze a series resistor circuit."""
    voltage = _validate_positive(voltage_v, "voltage_v")
    values = _validate_resistances(resistances)
    total_resistance = calculate_series_resistance(values)
    current_a = voltage / total_resistance
    power_w = voltage * current_a
    return {
        "voltage_v": voltage,
        "resistances_ohm": list(values),
        "total_resistance_ohm": total_resistance,
        "current_a": current_a,
        "power_w": power_w,
    }


def analyze_parallel_circuit(voltage_v, resistances: Sequence[float]):
    """Analyze a parallel resistor circuit."""
    voltage = _validate_positive(voltage_v, "voltage_v")
    values = _validate_resistances(resistances)
    total_resistance = calculate_parallel_resistance(values)
    total_current_a = voltage / total_resistance
    branch_currents = [voltage / value for value in values]
    power_w = voltage * total_current_a
    return {
        "voltage_v": voltage,
        "resistances_ohm": list(values),
        "total_resistance_ohm": total_resistance,
        "branch_currents_a": branch_currents,
        "total_current_a": total_current_a,
        "power_w": power_w,
    }


if __name__ == "__main__":
    print("DC Circuit Calculator")
    print("Single resistor example:")
    print(analyze_dc(12, 6))
    print("\nSeries example:")
    print(analyze_series_circuit(12, [2, 3, 6]))
    print("\nParallel example:")
    print(analyze_parallel_circuit(12, [2, 3, 6]))