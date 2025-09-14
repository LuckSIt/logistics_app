from __future__ import annotations

from math import ceil
from typing import Any, Dict, Optional


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except Exception:
        return default


def format_number(n: Optional[float], digits: int = 0) -> str:
    if n is None:
        return ""
    try:
        fmt = f"{n:,.{digits}f}"
        return fmt.replace(",", " ")
    except Exception:
        return str(n)


def coerce_days(value: Any) -> str:
    """Return transit days as integer string; ceil fractional positive values."""
    try:
        if value in (None, "", "None"):
            return ""
        v = float(value)
        if v <= 0:
            return ""
        d = int(ceil(v)) if v % 1 != 0 else int(v)
        return str(d)
    except Exception:
        return ""


def volumetric_weight(weight_kg: Any, volume_m3: Any) -> float:
    w = to_float(weight_kg, 0.0)
    v = to_float(volume_m3, 0.0)
    return max(w, v * 167.0)


def calc_air_costs(
    *,
    weight_kg: Any,
    volume_m3: Any,
    precarriage_cost: Any,
    air_tariff: Any,
    terminal_handling_cost: Any,
    auto_pickup_cost: Any,
) -> Dict[str, Any]:
    vw = volumetric_weight(weight_kg, volume_m3)
    pre = to_float(precarriage_cost)
    t = to_float(air_tariff)
    th = to_float(terminal_handling_cost)
    ap = to_float(auto_pickup_cost)

    air_usd = pre + t * vw
    rub = th + ap

    # Формировать формулы без нулевых слагаемых
    usd_parts = []
    if pre > 0:
        usd_parts.append(format_number(pre))
    if t > 0 and vw > 0:
        usd_parts.append(f"{format_number(t)} × {format_number(vw)}")
    air_usd_formula = f"{' + '.join(usd_parts)} = {format_number(air_usd)}" if usd_parts else ""

    rub_parts = []
    if th > 0:
        rub_parts.append(format_number(th))
    if ap > 0:
        rub_parts.append(format_number(ap))
    rub_rub_formula = f"{' + '.join(rub_parts)} = {format_number(rub)}" if rub_parts else ""

    return {
        "volumetric_weight": vw,
        "air_cost_usd": air_usd,
        "rub_cost_rub": rub,
        "air_usd_formula": air_usd_formula,
        "rub_rub_formula": rub_rub_formula,
    }


# Заглушки/сумматоры для других типов при отсутствии разбиения на составляющие в данных
def calc_sum_rub(*parts: Any) -> float:
    return sum(to_float(p) for p in parts if p not in (None, "", "None"))


def build_formula(parts: Any, total: Optional[float]) -> str:
    """Строит строку вида: a + b + c = total, пропуская пустые части."""
    nums = [to_float(p) for p in parts if p not in (None, "", "None")]
    if not nums:
        return ""
    left = " + ".join(format_number(n) for n in nums)
    if total is None:
        total_val = sum(nums)
    else:
        total_val = to_float(total)
    return f"{left} = {format_number(total_val)}"


