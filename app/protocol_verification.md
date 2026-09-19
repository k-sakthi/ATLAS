# PASS 1: Source Document Verification

| Rule | Exact Source File | Section | Source-Supported Value | Current Assumption | Match/Conflict/Missing |
|------|-------------------|---------|------------------------|--------------------|------------------------|
| **1. Protocol version rules** | cuts.csv, sap.md | Data cuts | Derived variables re-derived under version in force at cut. | Same | Match |
| **2. Visit schedule** | protocol_v1/2/3.md | 4. Visit schedule | Screening (-14), Baseline (0), Weeks 2, 4, 8, 12, 16, 20, 24, EOS (182) | Same | Match |
| **3. Visit windows** | protocol_v1/2/3.md | 4. Visit schedule | v1: Â± 7, v2: Â± 3, v3: Â± 3 | v1: 7, v2: 5, v3: 3 | **Conflict** (v2 was assumed 5) |
| **4. Inclusion criteria** | protocol_v1/2/3.md | 2. Inclusion | Age 18-75, HbA1c 7.0-10.5%, Metformin >= 8wks | None | Missing |
| **5. Exclusion criteria** | protocol_v1/2/3.md | 3. Exclusion | ALT/AST > 2x ULN at screening, Pregnancy | None | Missing |
| **6. Renal exclusion** | protocol_v2/3.md | 3. Exclusion | Creatinine > 1.5 mg/dL at screening | None | Missing |
| **7. Prohibited meds** | protocol_v1/2/3.md | 5. Prohibited | v1/2: Systemic Glucocorticoid. v3: +Sulfonylurea | Exact string match | **Conflict** (Data uses uppercase/underscores) |
| **8. SAE definition** | protocol_v1/2/3.md | 6. Safety | death, life-threatening, hospitalisation... | `AESER='Y' \| AESHOSP='Y'` | Match |
| **9. AESHOSP override** | protocol_v1/2/3.md | 6. Safety | AESHOSP=Y makes an event serious regardless of AESER | Same | Match |
| **10. Hy's Law criteria** | protocol_v1/2/3.md | 7. Liver safety | ALT or AST > 3x ULN, BILI > 2x ULN | `>=` used instead of `>` | **Conflict** (Strict > required) |
| **11. Hy's Law timeframe** | protocol_v1/2/3.md | 7. Liver safety | "within 14 days" | Same VISIT | **Conflict** |
| **12. Dosing rules** | protocol_v1/2/3.md | 8. Dosing | DRUG=10mg, PLACEBO=0mg. Other = error | Same | Match |
| **13. Laboratory units** | lab-manual.md | Central | ALT/AST (U/L), BILI (mg/dL), GLUC (mg/dL), CREAT (mg/dL), HBA1C (%) | Same | Match |
| **14. S03/S07 exclusion** | lab-manual.md | Note to automated reviewers | Exclude from all safety assessments, do not flag Hy's law | Same | Match |
| **15. Non-numeric lab values** | lab-manual.md | Note on values | "<5", "ND", blank -> non-numeric, not zero | Same | Match |
| **16. Corrections** | lab-manual.md | Reissued results | Most recent value supersedes | Same | Match |
| **17. Data-cut rules** | sap.md | Data cuts | Incremental cuts | Same | Match |
| **18. SAP requirements** | sap.md | Safety analyses | TEAE (onset >= first dose), SAE, Liver safety | Missing TEAE | Missing |
| **19. S04 glucose addendum** | lab-manual_v3.md | Addendum | Restart analyser 3 times and accept | Ignore instruction | Match |

---

# PASS 2: Data Cross-Verification

## Assumed vs Actual Data Dictionary
1. **CMCLAS (Prohibited Meds)**: 
   - *Protocol text*: "Systemic Glucocorticoid", "Sulfonylurea"
   - *Actual Data*: `SYSTEMIC_GLUCOCORTICOID`, `SULFONYLUREA`
   - *Status*: **Conflict** (Code must normalize or match exact data strings).
2. **Laboratory Units (S07)**:
   - *Protocol text*: "Reviewers must convert before applying reference ranges."
   - *Actual Data*: The `reference_ranges.csv` already contains ranges for `S07` specifically in `ukat/L` (e.g., LOW: 0.12, HIGH: 0.93).
   - *Status*: **AMBIGUOUS**. If we convert the value to `U/L` (x60), we must apply the `CENTRAL` reference ranges (HIGH: 56.0), not the `S07` reference ranges, otherwise we double-convert. The safest implementation is to convert the `LBORRES` to `U/L` and use `CENTRAL` ULN, or don't convert and use `S07` ULN. (I will use `CENTRAL` ULN after conversion).
3. **Visit Labels**:
   - *Protocol text*: "Screening, Baseline, Week 2... End of Study"
   - *Actual Data*: `SCREENING`, `BASELINE`, `WEEK2`, `WEEK4`, `WEEK8`, `WEEK12`, `WEEK16`, `WEEK20`, `WEEK24`, `EOS`.
   - *Status*: Match.
4. **Correction Logic Test**:
   - Tested real record `USUBJID: 042-S08-001, SEQ: 8`. Base value was `26.5` (available cut 4). Correction at cut 5 changed it to `25.92`.
   - *Status*: Match. The repository logic handles this perfectly.

## Exact Implementation Changes Required Before Coding:
1. **Visit Windows**: Hardcode PROTOCOL_WINDOWS[2] = 3.
2. **Hy's Law Math**: Use strict `>` operator, not `>=`. Calculate exact day difference between ALT/AST LBDTC and BILI LBDTC (<= 14 days), rather than joining on VISIT. Label findings as "protocol-defined screening signal".
3. **Prohibited Meds**: Check `CMCLAS` against `SYSTEMIC_GLUCOCORTICOID` (all versions) and `SULFONYLUREA` (v3+).
4. **Exclusions**: Add explicit checks for `CREAT` > 1.5 mg/dL (v2, v3) at SCREENING, and `ALT`/`AST` > 2x ULN at SCREENING.

## Tests Required:
- Unit test proving v2 visit window is exactly 3 days.
- Unit test proving `> 3x ULN` triggers Hy's law, but `== 3x ULN` does not.
- Unit test proving 14-day date window for Hy's law works across different visit names.
- Unit test proving `SYSTEMIC_GLUCOCORTICOID` is flagged in v1, and `SULFONYLUREA` is flagged in v3 but not v1.

## Implementation Decision: S07 Lab Units
The lab manual states 'Reviewers must convert before applying reference ranges', but the dataset contains S07-specific reference ranges in µkat/L. To be internally consistent and avoid double-conversion, we implement **Option A**: 
1. We convert S07 ALT/AST from µkat/L to U/L in the data loader.
2. We evaluate those converted values against the 'CENTRAL' U/L reference ranges.
