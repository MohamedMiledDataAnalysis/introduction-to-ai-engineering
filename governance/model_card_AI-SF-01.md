# Model card — AI-SF-01 Prospectus assistant

| Item | Value |
|---|---|
| Purpose | Draft answers to investor questions from the prospectus |
| Users | Cash management analysts |
| Decision impact | Draft for review; no automatic sending |
| Model | qwen3.5:4b |
| Human review | Every answer approved |
| Data | Prospectus (public to investors) |
| Owner | Head of cash management |
| Risk tier | Medium |
| Prompt version | answer_with_citations_v1 (hash bc9eed1576) |

## Evaluation

- Evaluation set: `evals/sf_prospectus_qa.csv`, 20 cases.
- Result: 18/20 passed (95% interval 70% to 97%).
- Failed cases: Q08, Q18.

## Monitoring (period of the log)

- Requests: 422; days: 18.
- Error rate: 1.4%.
- Review rate (median day): 10.0%; worst day: 23.3%.
- Median response time (median day): 3.9 s.

## Known limitations

- Small evaluation set: the interval above is wide.
- Answers are limited to the prospectus excerpt; other documents are out of scope.

## Sign-off

| Role | Name | Date |
|---|---|---|
| Owner | | |
| Model validation | | |
| Compliance | | |
