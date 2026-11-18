# Chapter 12 - The model drafts the query to the servicer; code checks that it lists exactly the flagged loans
source("aie_r/dq.R"); source("aie_r/dq_email.R")
found <- run_rules(read.csv("data/sf/rmbs/dq/larkfield_2026_09_received.csv", stringsAsFactors = FALSE), "2026-09-30")
email <- template_email(found, "30 September 2026", "7 October 2026")
cat(substr(email, 1, 420), "...\n\n")
p <- check_email(email, found)
cat("Check of the template email:", if (length(p)) paste(p, collapse = "; ") else "complete and exact", "\n")
second <- found$loan_id[2]
swapped <- paste0(substr(second, 1, 8), substr(second, 10, 10), substr(second, 9, 9), substr(second, 11, 11))
draft <- sub(second, swapped, email, fixed = TRUE)
draft <- sub(paste0("- ", found$loan_id[1], ": "), "- ", draft, fixed = TRUE)
cat("Check of a faulty draft:   ", paste(check_email(draft, found), collapse = "; "), "\n")
