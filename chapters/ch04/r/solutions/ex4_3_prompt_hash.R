# Exercise 4.3 - Hash of prompt version 2
# Run from the root of the repository:  Rscript chapters/ch04/r/solutions/ex4_3_prompt_hash.R

# Step 1, done from the reference copy if you have not written the file yet
if (!file.exists("prompts/extract_servicer_note_v2.txt"))
  file.copy("prompts/solutions/extract_servicer_note_v2.txt", "prompts/")

source("aie_r/prompts.R"); cat(load_prompt("extract_servicer_note_v2")$hash)

cat("\n")
