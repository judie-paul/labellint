# Demo workflow

1. Run `make docker-up`, then open http://localhost:8080.
2. Select Run sample with seed 42 and wait for completion.
3. Open a record to inspect its prompt, response, rationale and detector evidence.
4. Filter by detector or annotator, then open the Annotators and Evaluation views.
5. Download the audit JSON. Upload `reports/sim.jsonl` after `make pipeline` to
   demonstrate local file ingestion and evaluation from complete ground truth.

`npm --prefix dashboard test` records desktop/mobile screenshots in
`dashboard/test-results/`. CI uploads those files as `browser-results`. A demo GIF
can be recorded from this flow with a screen recorder; no fabricated animation or
unavailable hosted demo is presented as real.
