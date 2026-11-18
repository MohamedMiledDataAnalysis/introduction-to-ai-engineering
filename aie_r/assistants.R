# The two final-project agents: scope guards before the model, the agent loop, output guards after it.
source("aie_r/agent.R"); source("aie_r/prompts.R")
out_of_scope_sf <- "This assistant covers Larkfield Mortgage Funding 2025-1 only."
out_of_scope_am <- "This assistant covers the three Harbourline funds only."
no_advice <- c(sf = paste("This assistant cannot give investment advice or forecasts.",
                          "It can describe the transaction's documents, data and past performance."),
               am = paste("This assistant cannot give investment advice or forecasts.",
                          "It can describe the funds' facts, costs and past performance."))
am_words <- "\\b(harbourline|hgef|hecb|hbma|factsheet|kid|sfdr|equity fund|bond fund)\\b"
sf_words <- "\\b(larkfield|lmf|class [abcd]\\b|tape|waterfall|prospectus|reserve fund|arrears|cpr)\\b"
advice_words <- paste0("\\b(should (i|we|my client)|recommend|worth (buying|investing)|best fund|good investment|forecast|",
                       "predict|will (\\w+ ){1,3}(rise|fall|go up|go down|recover|outperform|underperform|beat)|",
                       "(best|right|suitable|better) (\\w+ ){0,2}for (me|my|our|a client)|",
                       "(buy|sell|invest in|switch to) (\\w+ ){0,3}(now|today|this year))\\b")

new_assistant <- function(domain) {
  if (domain == "sf") {
    p <- load_prompt("sf_agent_system_v1")
    tools <- c("pool_summary", "note_balance", "waterfall_summary", "arrears_buckets", "search_prospectus")
  } else {
    p <- load_prompt("am_agent_system_v1")
    tools <- c("fund_performance", "top_holdings", "fund_characteristics", "search_fund_documents")
  }
  list(domain = domain, system = p$text, version = p$hash, tools = tools)
}

guard_question <- function(a, question) {
  has <- function(p) grepl(p, question, ignore.case = TRUE, perl = TRUE)
  if (a$domain == "sf" && has(am_words) && !has(sf_words)) return(out_of_scope_sf)
  if (a$domain == "am" && has(sf_words) && !has(am_words)) return(out_of_scope_am)
  if (has(advice_words)) return(unname(no_advice[a$domain]))
  NULL
}

ask_assistant <- function(a, question, history = list()) {
  refusal <- guard_question(a, question)
  if (!is.null(refusal)) return(list(answer = refusal, status = "declined", steps = 0, tokens = 0, trace = list(),
                                     unsupported = character(0), prompt = a$version))
  r <- run_agent(question, a$system, a$tools, history = history)
  flagged <- forbidden_phrases(r$answer)
  if (length(flagged)) { r$status <- "needs_review"; r$unsupported <- c(r$unsupported, paste("forbidden phrase:", flagged)) }
  r$prompt <- a$version
  r
}
