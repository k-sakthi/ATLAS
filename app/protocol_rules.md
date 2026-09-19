# STUDY-042 Internal Protocol Rules Specification

## 1. Protocol Version Selection
- Determined by the data cut (`cuts.csv`).

## 2. Inclusion/Exclusion Criteria
- **Age**: 18–75 years at screening.
- **HbA1c**: 7.0% – 10.5% at screening.
- **Metformin**: Stable dose for ≥ 8 weeks.
- **Hepatic Disease Exclusion**: ALT or AST > 2x ULN at screening.
- **Pregnancy Exclusion**: Excluded.
- **Renal Impairment Exclusion (v2, v3)**: Creatinine > 1.5 mg/dL at screening.

## 3. Visit Schedules and Windows
- **Target Days**: Screening (Day -14), Baseline (Day 0), Week 2 (14), Week 4 (28), Week 8 (56), Week 12 (84), Week 16 (112), Week 20 (140), Week 24 (168), End of Study (Day 182).
- **Windows**: 
  - Protocol Version 1: ± 7 days
  - Protocol Version 2: ± 3 days
  - Protocol Version 3: ± 3 days

## 4. Prohibited Medications
- **Protocol Versions 1 & 2**: Systemic Glucocorticoid.
- **Protocol Version 3**: Systemic Glucocorticoid, Sulfonylurea.

## 5. Serious Adverse Events
- Events with `AESHOSP = Y` are classified as serious (SAE) regardless of the `AESER` code.

## 6. Hy's Law (Liver Safety)
- **Criteria**: (ALT or AST > 3x ULN) AND (total bilirubin > 2x ULN).
- **Timeframe**: Within 14 days of each other.

## 7. Dosing Rules
- **DRUG-042 Arm**: 10 mg once daily. (Any other dose is an error).
- **PLACEBO Arm**: 0 mg. (Any other dose is an error).

## 8. Laboratory Units and Normalization
- **Central Lab**: ALT/AST (U/L), Bilirubin (mg/dL), Glucose (mg/dL), Creatinine (mg/dL), HbA1c (%).
- **Site S07 (Local Lab)**: ALT/AST in µkat/L. Must convert (1 µkat/L = 60 U/L).
- **Missing Values**: "<5", "ND", or blank must be parsed as non-numeric (null), NOT zero.
- *(Note: Ignoring analyser restart instructions for Site S04).*

## 9. Safety Exclusions
- Sites S03 and S07 are entirely excluded from safety assessments and Hy's Law reporting.

## 10. Amendments and Data Cuts
- Derived variables (e.g. visit windows, prohibited meds) must respect the protocol version active at the requested data cut.
- Laboratory value corrections from the central lab replace previous values (resolved sequentially by cut).

## Implementation Decision: S07 Lab Units
The lab manual states 'Reviewers must convert before applying reference ranges', but the dataset contains S07-specific reference ranges in �kat/L. To be internally consistent and avoid double-conversion, we implement **Option A**: 
1. We convert S07 ALT/AST from �kat/L to U/L in the data loader.
2. We evaluate those converted values against the 'CENTRAL' U/L reference ranges.
