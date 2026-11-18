# Chapter 4 - Extract facts from the 18 servicer notes, with a versioned prompt and a JSON schema
source("aie_r/llm.R"); source("aie_r/prompts.R"); source("aie_r/validate.R")

p      <- load_prompt("extract_servicer_note_v1")
schema <- fromJSON("prompts/servicer_note_schema.json", simplifyVector = FALSE)
notes  <- lapply(readLines("data/sf/rmbs/servicer_notes_2026_09.jsonl", encoding = "UTF-8"),
                 fromJSON, simplifyVector = FALSE)

fields  <- c("loan_id", "months_in_arrears", "arrears_balance", "action", "promise_date")
correct <- setNames(rep(0, length(fields)), fields)
invalid <- 0
for (note in notes) {
  reply <- chat(list(list(role = "user", content = render(p$text, note_text = note$text))),
                format = schema)
  obj <- tryCatch(parse_json_reply(reply$text), error = function(e) NULL)
  if (is.null(obj) || length(validate(obj, schema)) > 0) { invalid <- invalid + 1; next }
  for (f in fields) {
    same <- identical(obj[[f]], note$truth[[f]]) || isTRUE(all.equal(obj[[f]], note$truth[[f]]))
    correct[f] <- correct[f] + same
  }
}
cat(sprintf("Prompt version %s; %d notes; %d invalid replies\n", p$hash, length(notes), invalid))
for (f in fields) cat(sprintf("  %-18s %2d/%d correct\n", f, correct[f], length(notes)))
