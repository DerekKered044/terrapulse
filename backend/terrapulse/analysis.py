"""Turn a regional monthly series into the analysis payload served by the API.

Slopes are reported per decade. "Significant" always means p < 0.05.
"""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
from statsmodels.stats.multitest import multipletests

from . import stats
from .catalog import END_YEAR, REGIONS, SOURCE, START_YEAR, VARIABLES
from .power import load_provenance, load_series

MIN_WINDOW_YEARS = 15
ALPHA = stats.ALPHA


def _clean(obj):
    """Make a structure JSON-safe: NaN/inf -> None, numpy scalars -> Python."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return v if math.isfinite(v) else None
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def decimal_year(year: np.ndarray, month: np.ndarray) -> np.ndarray:
    return year + (month - 0.5) / 12.0


def window_trend(t: np.ndarray, anomalies: np.ndarray, year: np.ndarray, start: int, end: int) -> dict:
    """AR(1)-adjusted OLS trend of anomalies for the years start..end inclusive."""
    sel = (year >= start) & (year <= end)
    res = stats.ols_trend(t[sel], anomalies[sel])
    adj = res["adjusted"]
    return {
        "start": start,
        "end": end,
        "slope_per_decade": res["slope"] * 10,
        "intercept": res["intercept"],
        "ci_low": adj["ci_low"] * 10,
        "ci_high": adj["ci_high"] * 10,
        "p_value": adj["p_value"],
        "significant": adj["p_value"] < ALPHA,
    }


def full_trend(t: np.ndarray, anomalies: np.ndarray, year: np.ndarray, start: int, end: int) -> dict:
    """All trend statistics for one window."""
    sel = (year >= start) & (year <= end)
    tt, yy = t[sel], anomalies[sel]
    ols = stats.ols_trend(tt, yy)
    mk = stats.mann_kendall(yy)
    sen = stats.theil_sen(tt, yy)
    n_years = end - start + 1
    detect = stats.years_to_detect(ols["slope"], ols["residual_std"], ols["lag1_autocorrelation"], n_years)
    return {
        "start": start,
        "end": end,
        "n_months": ols["n"],
        "ols": {
            "slope_per_decade": ols["slope"] * 10,
            "intercept": ols["intercept"],
            "r_squared": ols["r_squared"],
            "ci_low": ols["adjusted"]["ci_low"] * 10,
            "ci_high": ols["adjusted"]["ci_high"] * 10,
            "p_value": ols["adjusted"]["p_value"],
            "naive_ci_low": ols["naive"]["ci_low"] * 10,
            "naive_ci_high": ols["naive"]["ci_high"] * 10,
            "naive_p_value": ols["naive"]["p_value"],
        },
        "theil_sen": {
            "slope_per_decade": sen["slope"] * 10,
            "ci_low": sen["ci_low"] * 10,
            "ci_high": sen["ci_high"] * 10,
        },
        "mann_kendall": {
            "tau": mk["tau"],
            "p_value": mk["hamed_rao"]["p_value"],
            "classic_p_value": mk["classic"]["p_value"],
            "variance_factor": mk["hamed_rao"]["variance_factor"],
        },
        "noise": {
            "residual_std": ols["residual_std"],
            "lag1_autocorrelation": ols["lag1_autocorrelation"],
            "n_effective": ols["n_effective"],
        },
        "detectability": detect,
    }


def all_windows(t: np.ndarray, anomalies: np.ndarray, year: np.ndarray) -> list[dict]:
    out = []
    for start in range(START_YEAR, END_YEAR - MIN_WINDOW_YEARS + 2):
        for end in range(start + MIN_WINDOW_YEARS - 1, END_YEAR + 1):
            out.append(window_trend(t, anomalies, year, start, end))
    return out


def summarize_windows(windows: list[dict], full_slope: float) -> dict:
    sign = np.sign(full_slope)
    slopes = np.array([w["slope_per_decade"] for w in windows])
    sig = np.array([w["significant"] for w in windows])
    same = np.sign(slopes) == sign
    return {
        "n_windows": len(windows),
        "min_years": MIN_WINDOW_YEARS,
        "share_same_direction": float(same.mean()),
        "share_significant_same_direction": float((same & sig).mean()),
        "share_significant_opposite_direction": float((~same & sig).mean()),
        "slope_min": float(slopes.min()),
        "slope_max": float(slopes.max()),
    }


def verdict(trend: dict, windows_summary: dict, units: str) -> dict:
    """Plain-language reading of the statistics. Describes change, never causes."""
    slope = trend["ols"]["slope_per_decade"]
    direction = "rising" if slope > 0 else "falling"
    ols_sig = trend["ols"]["p_value"] < ALPHA
    mk_sig = trend["mann_kendall"]["p_value"] < ALPHA
    same = windows_summary["share_same_direction"]
    opposite_sig = windows_summary["share_significant_opposite_direction"]
    sig_same = windows_summary["share_significant_same_direction"]
    det = trend["detectability"]
    span = f"{trend['start']}-{trend['end']}"
    rate = f"{slope:+.3g} {units} per decade"

    if ols_sig and mk_sig:
        if same >= 0.9 and opposite_sig == 0:
            code, title = "robust", f"Significant {direction} trend that holds across date ranges"
            text = (
                f"Over {span} the series changed by {rate}. Both significance tests agree after "
                f"allowing for month-to-month persistence, and {same:.0%} of all date windows of "
                f"{windows_summary['min_years']}+ years point the same way."
            )
        else:
            code, title = "date_sensitive", f"Significant {direction} trend, but it depends on the dates chosen"
            text = (
                f"Over {span} the series changed by {rate} and both tests call it significant. "
                f"However only {same:.0%} of date windows of {windows_summary['min_years']}+ years point the "
                f"same way, so a different start or end year can change the conclusion."
            )
    elif ols_sig or mk_sig:
        code, title = "mixed", f"Possible {direction} trend: the two tests disagree"
        text = (
            f"Over {span} the estimated change is {rate}. One of the two significance tests passes "
            f"and the other does not, so treat this as suggestive rather than established."
        )
    else:
        if sig_same + opposite_sig >= 0.25:
            code, title = "date_sensitive", "No significant trend overall, but some date ranges show one"
            text = (
                f"Over {span} the estimated change is {rate}, which is not statistically significant. "
                f"Yet {sig_same + opposite_sig:.0%} of shorter date windows are significant on their own: "
                f"a claim built on one of those windows would not hold for the full record."
            )
        else:
            code, title = "not_detected", "No significant trend detected yet"
            text = f"Over {span} the estimated change is {rate}, which cannot be told apart from natural variability."
        if det["years_needed"] is not None:
            text += (
                f" If the true trend were this size, about {det['years_needed']:.0f} years of data "
                f"(range {det['low']:.0f}-{det['high']:.0f}) would be needed to detect it reliably; "
                f"the record has {det['record_years']:.0f}."
            )
    return {"code": code, "title": title, "text": text, "direction": direction}


@lru_cache(maxsize=None)
def _prepared(region_id: str, variable: str):
    frame = load_series(region_id, variable)
    year = frame["year"].to_numpy()
    month = frame["month"].to_numpy()
    values = frame["value"].to_numpy(dtype=float)
    clim = stats.monthly_climatology(month, values)
    anomalies = stats.deseasonalize(month, values, clim)
    return frame, year, month, values, clim, anomalies, decimal_year(year, month)


def custom_trend(region_id: str, variable: str, start: int, end: int) -> dict:
    _, year, _, _, _, anomalies, t = _prepared(region_id, variable)
    if end - start + 1 < MIN_WINDOW_YEARS:
        raise ValueError(f"window must span at least {MIN_WINDOW_YEARS} years")
    if start < START_YEAR or end > END_YEAR:
        raise ValueError(f"window must lie within {START_YEAR}-{END_YEAR}")
    return _clean(full_trend(t, anomalies, year, start, end))


@lru_cache(maxsize=None)
def analysis(region_id: str, variable: str) -> dict:
    frame, year, month, values, clim, anomalies, t = _prepared(region_id, variable)
    var = VARIABLES[variable]
    trend = full_trend(t, anomalies, year, START_YEAR, END_YEAR)
    windows = all_windows(t, anomalies, year)
    wsum = summarize_windows(windows, trend["ols"]["slope_per_decade"])
    prov = load_provenance()["series"][f"{region_id}/{variable}"]
    annual = frame.groupby("year")["value"].mean()
    n_missing = int(np.isnan(values).sum())
    cells = frame["n_cells_valid"].to_numpy()
    d = var["decimals"]
    return _clean(
        {
            "region": {"id": region_id, **REGIONS[region_id]},
            "variable": {"id": variable, **var},
            "period": [START_YEAR, END_YEAR],
            "series": {
                "t": [round(float(v), 4) for v in t],
                "year": year.tolist(),
                "month": month.tolist(),
                "value": [round(float(v), d + 1) for v in values],
                "anomaly": [round(float(v), d + 1) for v in anomalies],
                "climatology": [round(float(v), d + 1) for v in clim],
                "annual_year": annual.index.tolist(),
                "annual_mean": [round(float(v), d + 1) for v in annual.to_numpy()],
            },
            "trend": trend,
            "windows": windows,
            "windows_summary": wsum,
            "verdict": verdict(trend, wsum, var["units"]),
            "quality": {
                "months_total": int(len(values)),
                "months_missing": n_missing,
                "coverage": 1 - n_missing / len(values),
                "grid_cells": prov["grid"]["n_cells"],
                "min_cells_valid": int(cells.min()),
                "lag1_autocorrelation": trend["noise"]["lag1_autocorrelation"],
                "n_effective": trend["noise"]["n_effective"],
                "units_reported_by_nasa": prov["units_reported"],
            },
            "provenance": {**prov, "source": SOURCE},
        }
    )


@lru_cache(maxsize=None)
def overview(variable: str) -> dict:
    """Full-period trend for every region, with a false-discovery-rate check."""
    rows = []
    for region_id in REGIONS:
        a = analysis(region_id, variable)
        rows.append(
            {
                "region": region_id,
                "name": REGIONS[region_id]["name"],
                "bbox": REGIONS[region_id]["bbox"],
                "slope_per_decade": a["trend"]["ols"]["slope_per_decade"],
                "ci_low": a["trend"]["ols"]["ci_low"],
                "ci_high": a["trend"]["ols"]["ci_high"],
                "p_value": a["trend"]["ols"]["p_value"],
                "mk_p_value": a["trend"]["mann_kendall"]["p_value"],
                "verdict": a["verdict"]["code"],
                "verdict_title": a["verdict"]["title"],
            }
        )
    reject, p_adj, _, _ = multipletests([r["p_value"] for r in rows], alpha=ALPHA, method="fdr_bh")
    for r, rej, pa in zip(rows, reject, p_adj):
        r["p_value_fdr"] = float(pa)
        r["significant_after_fdr"] = bool(rej)
    return _clean(
        {
            "variable": {"id": variable, **VARIABLES[variable]},
            "period": [START_YEAR, END_YEAR],
            "regions": rows,
            "multiple_testing": {
                "method": "Benjamini-Hochberg false discovery rate, alpha 0.05",
                "n_tests": len(rows),
                "n_significant_raw": int(sum(r["p_value"] < ALPHA for r in rows)),
                "n_significant_fdr": int(sum(reject)),
            },
        }
    )
