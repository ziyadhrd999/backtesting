def clamp_weight(target_weight: float, max_abs_weight: float = 1.0) -> float:
    return max(-max_abs_weight, min(max_abs_weight, target_weight))
