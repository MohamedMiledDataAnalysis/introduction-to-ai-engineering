# Chapter 4 - Turn replies into data, and reject the bad ones
source("aie_r/validate.R")
schema <- fromJSON("prompts/servicer_note_schema.json",
                   simplifyVector = FALSE)

replies <- list(
  "A clean JSON" = '{"loan_id": "LMF25-00190", "months_in_arrears": 3, "arrears_balance": 1960.79, "action": "payment_plan", "promise_date": "2026-10-28"}',
  "B fenced, with a preface" = 'Here is the JSON:\n```json\n{"loan_id": "LMF25-00168", "months_in_arrears": 2, "arrears_balance": 829.85, "action": "no_contact", "promise_date": null}\n```',
  "C number as text" = '{"loan_id": "LMF25-00321", "months_in_arrears": "one", "arrears_balance": 938.63, "action": "no_contact", "promise_date": null}',
  "D label outside the list" = '{"loan_id": "LMF25-00190", "months_in_arrears": 3, "arrears_balance": 1960.79, "action": "payment plan", "promise_date": "28/10/2026"}',
  "E missing field" = '{"loan_id": "LMF25-00190", "arrears_balance": 1960.79, "action": "payment_plan", "promise_date": "2026-10-28"}'
)
for (name in names(replies)) {
  obj <- tryCatch(parse_json_reply(replies[[name]]),
                  error = function(e) e)
  if (inherits(obj, "error")) {
    cat(sprintf("%-26s NOT JSON: %s\n", name, conditionMessage(obj)))
    next
  }
  errors <- validate(obj, schema)
  cat(sprintf("%-26s %s\n", name,
              if (length(errors) == 0) "valid" else "INVALID"))
  for (e in errors) cat(sprintf("%-28s- %s\n", "", e))
}
