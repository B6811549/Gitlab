def analyze_dc(voltage_v, resistance_ohm):
    if resistance_ohm == 0:
        raise ValueError("Resistance cannot be zero.")
    current_a = voltage_v / resistance_ohm
    power_w = voltage_v * current_a
    return {"current_a": current_a, "power_w": power_w}
