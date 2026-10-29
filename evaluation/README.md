# Independent evaluation materials

Materials for the blinded question-answering evaluation reported in the manuscript
"A Traditional Chinese Medicine Knowledge Graph for Hypertension With Emotional
Comorbidity: Development and Blinded Question-Answering Evaluation" (submitted to
JMIR Medical Informatics, manuscript 101606).

## Contents of this directory

| File | Contents | Manuscript reference |
|---|---|---|
| `question_set_73.json` | The 73 evaluation questions with reference answer points, sources and question types | Methods, *Evaluation design* |
| `rating_rubric.md` | The four-category rubric, fixed before rating commenced | Methods, *Evaluation design* |
| `ratings_round1_three_conditions.json` | Item-level ratings, 219 responses (73 questions x 3 conditions: complete system, retrieval only, model only; Qwen2.5-7B-Instruct, no output-token limit) | Results, *Independent blinded evaluation*; Table 4 |
| `ratings_round3_model_comparison.json` | Item-level ratings, 146 responses (73 questions x 2 generation models under a 6000-token limit: Qwen2.5-7B-Instruct and DeepSeek-V4-Pro) | Results, *Comparison of generation models*; Table 5 |
| `summary_results.json` | Aggregate counts by condition and by model for the two rounds above | Tables 4 and 5 |
| `retrieval_ablation.py` | The six retrieval configurations (A0, D1, D1.5, D2, D3, D4) and the graph-level statistics underlying the failure analysis | Results, *Retrieval strategy ablation* and *Failure analysis*; Table 6 |

Each rating record carries both independent ratings (`rater1`, `rater2`), the
consensus category, and the separately recorded `fabrication` and `safety_flag`
fields. Where the two raters disagreed, the consensus is the more conservative of
the two categories. In `summary_results.json`, `strict_accuracy` is the proportion
of fully correct responses and `directional_accuracy` is the correct-or-partially-
correct proportion; the latter is a combination of two rubric categories and is not
a measure of clinical acceptability.

## Materials provided with the manuscript rather than in this directory

The following item-level materials are supplied as Multimedia Appendices of the
manuscript and are not part of release v2.0 of this repository:

- the six-configuration (retrieval-strategy) ratings, 438 responses (Table 6);
- the additional matched DeepSeek-V4-Pro comparison with and without graph
  retrieval, 146 responses, including the exact prompts, recognized entities and
  the exported run record (Table 7);
- the original answer texts for the initial, generation-model and matched
  comparisons, and the 73 reference-answer keys with scoring instructions;
- the complete source-attributed workbook for the original 100-relation review,
  its independent reviewer worksheets, release-membership mapping, and restricted
  80-relation analysis (Multimedia Appendix 4). A compact rating/membership CSV
  and reproducibility script are also provided below in this directory.

Note that the DeepSeek-V4-Pro answers rated in `ratings_round3_model_comparison.json`
are the same 73 A0 answers that were rated in the six-configuration round; they were
rated in two separate blinded rounds by the same two physicians and the two sets of
labels are reported separately in the manuscript (Tables 5 and 6). They are not
independent generations.

## Provenance of the question set

Three practising TCM clinicians who had taken no part in constructing the system each
contributed questions arising from their own clinical practice and teaching: a chief
physician (28 years), and two associate chief physicians (18 and 15 years). While
authoring questions they were given no access to the system, the knowledge graph, or
the corpus record list. Of 75 submitted items, 3 were returned for rewording because
they could not be scored against a determinate answer and 2 were removed as substantive
duplicates, yielding the final set of 73.

The 73 questions name 35 distinct formulas, of which 9 are retrievable from the
knowledge graph. This is a measure of graph coverage of the question set, not a test
of question-set independence.

## Rating procedure

Responses were rated by two further TCM clinicians who had taken no part in question
authoring, working independently and without knowledge of which condition produced each
response. Within each question the responses were presented in independently randomized
order and labelled neutrally, with the label-to-condition mapping redrawn for every
question. Initial inter-rater agreement was 186/219 (84.9%; Gwet AC1 = 0.82) in Round 1
and 132/146 (90.4%; Gwet AC1 = 0.87) in Round 3.

## Evaluation rounds

- Round 1 compared three conditions using the generation call as originally
  configured, without an output-token limit. Many Qwen2.5-7B-Instruct responses were
  truncated or degenerate: 62/73 model-only responses were truncated after their first
  item and ended with a chat-template artefact, 6/73 complete-system responses contained
  such an artefact, and 5/73 complete-system responses degenerated into repetition or
  garbled text (2 overlapped, giving 9 distinct affected complete-system responses). All were rated as produced; the model-only condition of this round
  therefore characterises the configuration as run, not the model's unaided capability.
  Response texts are provided in Multimedia Appendix 6 of the manuscript.
- Round 2 compared six retrieval configurations with DeepSeek-V4-Pro as the generation
  model (`retrieval_ablation.py`; ratings in the manuscript appendices).
- Round 3 compared generation models under a 6000-token output limit with the same
  graph, retrieval procedure, prompts and raters.
- An additional matched comparison (October 2026) ran DeepSeek-V4-Pro with and without
  graph retrieval on the same 73 questions, one response per condition per question,
  using the JSON retrieval backend; materials are in the manuscript appendices.

All rounds used the same 73 questions, the same rubric and the same two raters. The
rounds are reported separately in the manuscript; results from different rounds are
not pooled and are not interpreted as controlled estimates of improvement over time.

## Reproducing the graph-level analysis

```bash
python evaluation/retrieval_ablation.py .
```

Requires only `data/triples.json` and `data/entities.json` from this repository. The script
prints the graph statistics on which the failure analysis rests, including the hub
threshold derivation (degree greater than five times the mean degree; mean 6.18,
threshold 30.9), the proportion of hub-directed relations (173/312), and the
hub-coverage distribution of treatment-side terms.

## Note on the source corpus

`data/extracted/literature_records.json` lists the 419 source records as bibliographic
metadata (authors, title, journal, year, volume/issue/pages, keywords, database):
257 from Wanfang, 95 from CNKI, 62 from VIP, and 5 records whose database field was not
recorded in the export. The source-record file distributed in the current release
contains metadata without abstracts or full texts. Earlier Git history retains
versions containing abstracts; this history has not been rewritten. Access to
source texts remains subject to the applicable database terms.

## Prompt 1 execution

At the question-answering stage, the system first normalized synonyms and matched entity names as strings in the question. It called the entity-recognition prompt (Prompt 1) only if no entity was matched, supplying up to the first 20 entity names in each type from the entity index. The exact prompt texts and the matched-comparison prompts are documented in Multimedia Appendices 2 and 6, respectively.

## Relation-review correction

The original 100-relation review came from an earlier unpublished local development graph in which all 100 relations were present. Twenty were removed during subsequent curation, but the original review list was retained. The answer summaries in Multimedia Appendix 4 were generated later using the updated graph, after those removals. The relation list and the summaries therefore refer to different graph versions. The reference to a 200-triple test set was a typographical error, not the sampling frame. Of the 100 reviewed relations, 80 occur in `data/triples.json` in v2.0; 20 do not (9 COMPOSED_OF, 7 TREATS, 4 USES). The released-subset analysis uses those 80 records without obtaining new ratings. It is not a new stratified sample or a design-weighted estimate for the full graph.

Consensus confirmed 79/80 (98.8%; 95% Wilson CI 93.3–99.8): TREATS 47/47, COMPOSED_OF 21/21, USES 6/6, and CAUSES 5/6. Initial agreement was 77/80 (96.3%); quadratic-weighted Cohen kappa = −0.02 and Gwet AC1 = 0.96 (95% paired bootstrap CI 0.91–1.00; 20,000 resamples, seed 20261028, three fixed categories). The original 96/100 is retained as a historical review result, not a final-graph sampling result. Of the 20 excluded relations, 17 had been confirmed and 3 rejected at consensus. Thus, 3 of the 4 originally rejected relations were excluded, and the higher confirmation proportion in the retained subset should not be interpreted as improved graph quality.

The available records do not document the item-specific curation decision behind each removal. The absences are concentrated: 16 of the 20 relations involve five formulas (杞菊地黄汤, 滋肾平肝汤, 龙藤降压汤, 平调颗粒, and 养心安神定眩汤) that are not nodes in the release; 3 are COMPOSED_OF relations of 解郁平肝汤, which remains a node but has no recorded composition; and 1 involves 滋阴潜阳, which is not a graph node.

`relation_review_release_mapping.csv` preserves all 100 rating records and release-membership flags. `relation_review_statistics.json` contains the recomputed results. Reproduce them with `python evaluation/recalculate_relation_review.py` (Python with NumPy); the script verifies membership against `data/triples.json` and reports the reviewed subset separately from the historical sample. Multimedia Appendix 4 also contains the source attributions and the original reviewer worksheets. The graph data and the historical v2.0 tag are unchanged.


## Archived record counts and bibliographic corrections

The 419 entries are archived records, not a count of distinct publications. Export labels are Journal Article (321), Dissertation/Thesis (95), and Journal (3). Author-confirmed duplicate entries 130/131, 377/375, and 407/408 are cross-referenced in Multimedia Appendix 3. Record 170 is a conference paper; its citation in Multimedia Appendix 3 was completed using the bibliographic details supplied by the authors. Original archive numbering and record-level corpus counts are retained. See `data/extracted/bibliography_audit.csv` for the bibliographic checks (record numbers are 1-based array positions).


## Formula coverage and candidate-fusion checks

Run `python evaluation/check_reported_counts.py` from the repository root.
`report_consistency_checks.json` records the corresponding counts. Six of the eight
formula-composition questions name formulas absent from both the entity index and
the graph: Q013, Q014, Q038, Q039, Q062 and Q063. Q038 asks about 黄连温胆汤; the
indexed and connected formula 温胆汤 is a substring match, not the same recorded
formula name. Exact-name coverage and partial string recognition must be reported
separately. Q012 and Q040 have exact-name entries and composition relations.

Candidate fusion reduced 1004 entity records to 1002, and the archived
`fusion_info.merged_entities` value is 2. The fusion implementation uses six built-in
alias groups; these are distinct from the 28-group dictionary in `data/synonyms.json`
used for question processing. Six alias groups do not mean six merged entities.

The previously reported 366,707-character corpus total could not be reproduced
from the archived fields, so that total and its derived mean have been removed
from the manuscript. Counting title, keyword strings and abstract text without
added list syntax gives 300,730 Unicode code points. Converting keyword lists with
Python `str(list)` gives 308,362, including brackets, quotes and separators. These
are different counting conventions and neither establishes the number of characters
actually submitted to the extraction model. The optional `--source-records` input
accepts an original local export and reports the first, explicitly defined count;
the current metadata-only release cannot reproduce an abstract-inclusive count.

In Round 3, the Qwen responses contain seven template artifacts and one separate
degenerate-repetition flag (Q019), as recorded in Multimedia Appendix 6.
