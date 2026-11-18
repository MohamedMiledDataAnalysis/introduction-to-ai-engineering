# Chapter 14 - Build the September 2026 investor report figures: reconcile, compute, comment
source("aie_r/investor_report.R")
f <- month_figures("2026-09-30")
checks <- reconcile(f)
for (nm in names(checks)) cat(if (checks[[nm]]) "PASS " else "FAIL ", nm, "\n")
if (!all(checks)) stop("Reconciliation failed: the report is not produced.")
cat("\nCPR:", sprintf("%.1f%%", f$cpr), " arrears:",
    sprintf("%.2f%% (previous %.2f%%)", f$arrears_ratio,
            f$prev_arrears_ratio), "\n")
print(f$buckets)
cat("\nCommentary:", template_commentary(f), "\n")
