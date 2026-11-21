# Real-model runs of 18 November 2026

Two runs of `.github/workflows/real-model.yml` with `qwen3.5:4b` (Ollama 0.40, 4 processors, 16 GB, no graphics card), an hour apart on two GitHub machines.

- `run1/`: the printed output of every model script, in Python and R, and the agent evaluations' answers. Chapter 3 prints its output from this run; the other chapters print the run of 21 November and quote this one where it shows a different behaviour.
- `run2/`: the answers saved by the second run (Chapter 5 live evaluation and the agent evaluations). Correction 5.6 reads the Chapter 5 answers from it.

The two runs differ in a few answers: temperature 0 and a fixed seed make a run repeatable on one machine, not identical across machines (Chapter 3).
