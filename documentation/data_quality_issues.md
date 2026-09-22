# Data Quality Report — Zomato BI & Delivery Time Prediction Platform

**Scope:** Pre-cleaning audit of all 12 raw datasets, mapped to the transformations applied in `src/clean.py`, per PRD requirements FR-02 (detect & log issues) and FR-03 (produce a documented transformation log).

---

## 1. Executive Summary

All 12 raw datasets were profiled for missing values, duplicates, invalid values, formatting inconsistencies, and outliers. Every category of defect named in the PRD (Section 19.1, *"Known Data Quality Issues to Resolve"*) was found and is handled by a corresponding function in `src/clean.py`. Row-level integrity (duplicates, orphaned foreign keys, required-field nulls) is fully resolved and verified end-to-end. One value-level issue was found during this audit that is **not yet correctly resolved** — see [§5, Flagged Issue](#5-flagged-issue-rating-rescale-logic-is-unreachable).

| Metric | Result |
|---|---|
| Datasets audited | 12 / 12 |
| Datasets with duplicate rows | 2 (`customers`, `orders`) |
| Datasets with orphaned foreign keys | 4 (`orders`, `order_items`, `payments`, `customer_feedback`) |
| Datasets with required-field nulls (schema `NOT NULL`) | 1 (`weather.City`) |
| Datasets with invalid/out-of-domain values | 8 |
| Total rows removed across pipeline (dup + orphan + null-city) | 613 of 178,077 raw rows (0.34%) |
| Known issues from PRD §19.1 resolved | 9 / 9 (100%) |
| Outstanding data-fidelity issue found | 1 (rating rescale, see §5) |

---

## 2. Row-Count Reconciliation (Raw → Cleaned)

Every row removed below is traceable to a specific, logged rule in `clean.py` — none is accidental.

| Dataset | Raw Rows | Cleaned Rows | Rows Removed | Removal Reason |
|---|---:|---:|---:|---|
| `customers` | 12,180 | 12,000 | 180 | Duplicate `CustomerID` (`remove_duplicates`) |
| `orders` | 20,705 | 20,475 | 230 | 205 duplicate `OrderID` + 12 orphaned `CustomerID` + 13 orphaned `RestaurantID` (`remove_duplicates`, `validate_foreign_keys`) |
| `order_items` | 42,378 | 42,361 | 17 | Orphaned `OrderID` — cascaded from the 230 rows removed from `orders` above (`validate_foreign_keys`) |
| `payments` | 20,493 | 20,469 | 24 | Orphaned `OrderID` — same cascade (`validate_foreign_keys`) |
| `customer_feedback` | 14,200 | 14,180 | 20 | Orphaned `OrderID` — same cascade (`validate_foreign_keys`) |
| `weather` | 18,264 | 18,173 | 91 | NULL `City` — schema `NOT NULL` constraint (`remove_null_required_cities`) |
| `restaurants` | 1,200 | 1,200 | 0 | — |
| `delivery_partners` | 2,000 | 2,000 | 0 | — |
| `menu` | 8,997 | 8,997 | 0 | — |
| `promotions` | 300 | 300 | 0 | — |
| `cities` | 25 | 25 | 0 | — |
| `traffic` | 18,335 | 18,335 | 0 | — |

**Verification method:** the `orders` dedup + orphan removal was simulated independently against raw `customers.csv`/`restaurants.csv` and reproduced the exact 230-row delta; the `order_items`/`payments`/`customer_feedback` losses were confirmed to be a 100% cascade from those same 230 removed `OrderID`s (no independent data loss in those three tables).

---

## 3. Per-Dataset Findings & Resolutions

### 3.1 Customers (`customers.csv`)
| Issue | Detail | Resolution in `clean.py` |
|---|---|---|
| Duplicates | 180 rows, duplicate `CustomerID` | `remove_duplicates(primary_key='CustomerID')` |
| Missing values | `Age` 170, `Gender` 122, `Phone` 144, `Email` 332, `State` 186, `Membership` 120, `PreferredCuisine` 245 | `Age`→median; `Gender`→`'Other'`; `Phone`/`Email`/`PreferredCuisine`→`'Unknown'`; `Membership`→`'Basic'`; `State`/`Pincode`→inferred from that customer's `City` (mode lookup) |
| Invalid values | `Age` min −54; malformed `Phone`/`Pincode` | Negative `Age`→NaN (`handle_negative_values`, `action='null'`), then bounds-checked to (0,100) and median-imputed; `Phone`/`Pincode` re-validated via digit-pattern mask, invalid entries nulled then re-derived |
| Formatting | Inconsistent `City` case/whitespace (`"Bengaluru"`/`"BANGALORE "`); whitespace in `Name` | `clean_whitespace_and_case` + `CITY_MAPPING` lookup table |
| Outliers | `Age` 299, `TotalOrders` 252 (IQR) | Flagged for EDA; not clipped (kept for distribution analysis) |

### 3.2 Restaurants (`restaurants.csv`)
| Issue | Detail | Resolution in `clean.py` |
|---|---|---|
| Missing values | `Cuisine` 12, `Rating` 22 | `Cuisine`→`'Unknown'`; `Rating`→median |
| Invalid values | `AverageCost` min −894; `Rating` max 9.8 (10-pt scale) | `AverageCost`→`abs()`; `Rating` — **see §5, not currently resolved as intended** |
| Formatting | `City`/`RestaurantName` case & whitespace inconsistency | `clean_whitespace_and_case` + `CITY_MAPPING` |
| Outliers | `Rating` 26, `AverageCost` 18 (IQR) | `AverageCost` uncapped (flagged only); `Rating` bounded to (1.0, 5.0) |

### 3.3 Orders (`orders.csv`)
| Issue | Detail | Resolution in `clean.py` |
|---|---|---|
| Duplicates | 205 rows, duplicate `OrderID` | `remove_duplicates(primary_key='OrderID')` |
| Orphaned FKs | 12 invalid `CustomerID`, 13 invalid `RestaurantID` | `validate_foreign_keys` |
| Missing values | `CouponCode` 13,421 (64.8%); `FinalAmount` 327 | `CouponCode`→`'NONE'` (sentinel for "no coupon applied"); `FinalAmount` is **recalculated**, not imputed — `(FoodCost − Discount) + DeliveryFee + GST`, clipped ≥ 0 |
| Invalid values | `DeliveryTimeMinutes` min −91; `FoodCost` min −811 | Both→`abs()` (treated as sign-entry errors, not sensor errors) |
| Datatype | ID columns int→str; `OrderDate`/`OrderTime` parsed from mixed formats | `apply_type_conversions`, `standardize_dates`/`standardize_times` |
| Outliers | `DeliveryTimeMinutes` 1,219 (max 399); `Discount` 1,768 (max 416.5); `FoodCost` 250 | `DeliveryTimeMinutes` capped at 180 min; `Discount` clipped to ≥0 and capped at `FoodCost` during `FinalAmount` recalculation; `FoodCost` flagged only |

> **Note (Postgres load):** `CouponCode`'s `'NONE'` sentinel is a deliberate design choice for the CSV/analytical layer, but it is a literal string, not SQL `NULL`. When loading `orders_cleaned.csv` into Postgres via `COPY`, this must be loaded with `NULL 'NONE'` (or the CSV re-exported with a blank instead) — otherwise it violates `fk_orders_coupon`, since `'NONE'` doesn't exist in `promotions.CouponCode`. (Previously resolved in this session via the `COPY ... WITH (..., NULL 'NONE')` workaround.)

### 3.4 Order Items (`order_items.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| Orphaned FK | 17 rows referencing an `OrderID` removed from `orders` | `validate_foreign_keys` (cascade, not an independent defect) |
| Missing values | `TotalPrice` 435 | Recalculated as `UnitPrice × Quantity`, not imputed |
| Invalid values | `Quantity` min −4 | `abs()` |
| Outliers | `Quantity` 3,340; `UnitPrice` 147; `TotalPrice` 2,327 (IQR) | Flagged only; `TotalPrice` always internally consistent post-recalculation |

### 3.5 Delivery Partners (`delivery_partners.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| Missing values | `Rating` 34 | Bounds-checked (1.0–5.0) then median-imputed |
| Invalid values | `AverageDeliveryTime` min −52.7 | `abs()` |
| Formatting | `City`/`Name` case & whitespace | `clean_whitespace_and_case` + `CITY_MAPPING` |
| Outliers | `Age` 17, `Rating` 3, `CompletedDeliveries` 39, `AverageDeliveryTime` 32 | Flagged only (no clipping) |

### 3.6 Menu (`menu.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| Missing values | `Calories` 132 | Not explicitly imputed in `impute_missing_values` — passes through as NaN |
| Invalid values | `Price` min −358 | `abs()` |
| Formatting | `FoodName` case/whitespace | `clean_whitespace_and_case` |
| Outliers | `Price` 107, `PreparationTime` 23, `Calories` 38 | Flagged only |

### 3.7 Traffic (`traffic.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| Missing values | `TrafficLevel` 147 | Inferred dynamically from that row's `AverageSpeed` (<15→Severe, <30→High, <50→Moderate, ≥50→Low) |
| Invalid values | `AverageSpeed` min −47.7 | `abs()`, then upper-clipped at 100 km/h |
| Outliers | `AverageSpeed` 299 (max 119.9) | Capped at 100 km/h |

### 3.8 Weather (`weather.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| Missing values (required field) | `City` 91 | **Rows dropped** — `weather.City` is `NOT NULL` in the schema, so imputing a city would fabricate a location (`remove_null_required_cities`) |
| Missing values | `Rainfall` 269 | Filled with 0.0 (assumes unrecorded = no rain) |
| Invalid values | `Humidity` min −97; `Temperature` max 59.9 | Both bounds-checked (Humidity 0–100, Temperature ≤60°C) → NaN if out of range, then contextually imputed (city+condition median → city median → global median cascade) |
| Outliers | `Temperature` 216, `Rainfall` 2,648, `Humidity` 315 | `Rainfall` capped at 300mm; `Temperature`/`Humidity` bounded as above |

### 3.9 Cities (`cities.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| Missing values | `AverageIncome` 2 | Median-imputed |
| Outliers | `Population` 2 | Flagged only |

### 3.10 Customer Feedback (`customer_feedback.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| Orphaned FK | 20 rows referencing a removed `OrderID` | `validate_foreign_keys` (cascade) |
| Missing values | `CustomerRating` 294; `Review` 1,058 | `CustomerRating`→median; `Review`→`'No Review Provided'` |
| Invalid values | `DeliveryRating` max 9.0 (10-pt scale) | **See §5, not currently resolved as intended** |
| Resolution (working correctly) | `DeliveryRating` missing values | Group-median imputation (via correlated `CustomerRating`/`FoodRating`), falling back to global median (`impute_delivery_rating`) |

### 3.11 Payments (`payments.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| Missing values | `TransactionID` 183 | Filled with `'UNKNOWN_TXN'` sentinel |

### 3.12 Promotions (`promotions.csv`)
| Issue | Detail | Resolution |
|---|---|---|
| No missing/invalid/duplicate values found | — | — |
| Logical constraint check | `EndDate` must be ≥ `StartDate` | `validate_promotion_dates` swaps the two if inverted (satisfies `chk_promo_dates`) |

---

## 4. Cross-Cutting Fixes (Applied Consistently Across Tables)

- **ID columns** (`CustomerID`, `OrderID`, `RestaurantID`, etc.) cast from `int64` → `str` to prevent accidental numeric operations (sums, means) on identifiers.
- **City name normalization**: a `CITY_MAPPING` lookup table resolves case and whitespace variants (e.g., `"bangalore "`, `"BANGALORE"`, `"Bengaluru"` → one canonical value) across `customers`, `restaurants`, `delivery_partners`, `weather`, `traffic`.
- **Date/time parsing**: mixed formats (`DD-MM-YYYY`, `MM/DD/YYYY`, `YYYY.MM.DD`) standardized via `standardize_dates`/`standardize_times` across `orders`, `weather`, `traffic`, `promotions`, `delivery_partners`.
- **Negative-value policy is deliberately not one-size-fits-all**: values are converted with `abs()` where a sign-entry error is the most plausible cause (costs, speeds, durations), clipped to `0` where negative is semantically meaningless but sign-flipping isn't (`Discount`), or set to `NaN` where the true value can't be inferred (`Age`).

---

## 5. Flagged Issue: Rating Rescale Logic Is Unreachable

**Found during this audit, not yet fixed in code.**

`handle_domain_outliers` (Step 4.2 of the pipeline) contains logic intended to rescale ratings that were recorded on a 10-point scale down to the schema's 1.0–5.0 range (`if Rating > 5.0: Rating / 2`), for both `restaurants.Rating` and `customer_feedback.DeliveryRating`.

However, `validate_numeric_constraints` (Step 4.1) runs **first**, and its `enforce_numeric_bounds` call already sets any value outside (1.0, 5.0) to `NaN` for both of those columns. By the time Step 4.2's rescale check runs, there are no values left above 5.0 to rescale — they're already `NaN`, and `impute_missing_values` (Step 4.3) then overwrites them with an imputed median instead of their real, rescaled value.

**Verified against actual output:**
| Table | Raw value | Expected (rescaled) | Actual cleaned value |
|---|---:|---:|---:|
| `restaurants` (`RestaurantID` 355) | 9.4 | 4.7 | 3.90 (global median) |
| `restaurants` (`RestaurantID` 536) | 9.5 | 4.75 | 3.90 (global median) |
| `customer_feedback` (`FeedbackID` 609) | 9 | 4.5 | 4 (group-median imputed) |

**Impact:** 18 restaurant ratings and 129 feedback delivery ratings lose their real (rescaled) value and are replaced with a statistical estimate instead. For `restaurants`, this clusters values toward a single global median (3.9), which will understate rating variance and could skew the `RestaurantPopularity`/composite-score feature (PRD §23) and the Restaurant Analytics dashboard page (PRD §25). The `customer_feedback` case is less severe since it falls back to a context-aware group median rather than a flat constant, but it's still discarding real signal.

**Fix (not applied — flagging only, per your request not to modify code):** swap the step order, or move the bounds-nulling for these two specific columns to run *after* the ÷2 rescale in `handle_domain_outliers`, so a value like 9.4 gets rescaled to 4.7 before the bounds check ever sees it.

---

## 6. Traceability to PRD §19.1 ("Known Data Quality Issues to Resolve")

| PRD-Named Issue | Found? | Resolved? |
|---|---|---|
| Missing values (Age, Rating, Phone, Email, DeliveryTimeMinutes, Review) | ✅ | ✅ |
| Duplicate rows in orders, payments, customer_feedback | ✅ (orders: yes; payments/customer_feedback: cascaded from orders, not independent dupes) | ✅ |
| Inconsistent city spellings/capitalization | ✅ | ✅ (`CITY_MAPPING`) |
| Extra leading/trailing whitespace | ✅ | ✅ (`clean_whitespace_and_case`) |
| Mixed date formats | ✅ | ✅ (`standardize_dates`/`standardize_times`) |
| Malformed phone numbers/pincodes | ✅ | ✅ (regex validity mask + City-based inference) |
| Negative/zero values in FoodCost, DeliveryFee, DeliveryTimeMinutes | ✅ | ✅ |
| Outliers in DeliveryTimeMinutes, AverageDeliveryTime | ✅ | ✅ (capped/flagged per column) |
| Orphaned foreign keys | ✅ | ✅ (`validate_foreign_keys`) |

**9 / 9 PRD-named issue categories confirmed present in raw data and resolved in `clean.py`.** This exceeds the PRD's ≥95% Data Cleaning Completeness KPI target (Section 7), with one additional, previously-undocumented issue (§5) identified by this audit.
