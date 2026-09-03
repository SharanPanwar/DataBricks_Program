# Lab A — Reliable ingestion into bronze

**Monday 31 August · scored out of 25 · demo at 16:15**

Ingest from three source types into bronze. **It must be re-runnable, and it
must survive a malformed file without losing the batch.**

```bash
pip install pyspark
export PYTHONPATH=src

python -m laba.seeds generate ./landing     # lay out the three sources
python -m laba.ingest ./landing ./submission
python -m laba.ingest ./landing ./submission    # run it AGAIN
```

## The three sources

| Source | Where | What will catch you out |
|---|---|---|
| **File drop** | `landing/filedrop/orders/load_date=*/` | One file is malformed — and it sits in the same partition as a good file |
| **Database** | `landing/database/source.db` (SQLite) | Stands in for Azure SQL. A customer master |
| **API** | `landing/api/products/` | Paged JSON. No `totalCount` field, and one page repeats a record from the previous one |

## Deliver

```
submission/
  bronze/orders        bronze/customers     bronze/products
  bronze/rescued       run_manifest.json
```

`run_manifest.json` records **two full runs** and the bronze row count of each:

```json
{"runs": [{"run": 1, "bronze_rows": 6004},
          {"run": 2, "bronze_rows": 6004}]}
```

Equal counts is the criterion. **A pipeline that grows on retry is one nobody
dares re-run at 3am.**

## The two things the brief actually asks

**1 · Survive a malformed file without losing the batch.**

The malformed file contains **six bad rows and two good ones**. Both good rows
must land. Failing the file loses them; skipping the file loses them.

And the bad rows must go *somewhere you can read*. Skipping without a record is
data loss with extra steps.

**2 · Re-runnable.**

Two full runs over the same landing zone, same count. Work out what makes that
true — the checkpoint, `replaceWhere`, a merge key, or something else. The
rubric does not care which; it cares that it holds.

## How you build it is up to you

Auto Loader on Databricks, or a plain read locally. The rubric checks whether
the **output** has the properties the brief asks for — never how you got there.
A candidate who solves it with `cloudFiles` and one who solves it with
`spark.read` both score full marks.

What you will be asked in the demo is *why* you chose what you chose.

## Where the marks are

| Marks | Criterion |
|---|---|
| **6** | The malformed file did not lose the batch |
| **5** | Re-runnable — a second run changes nothing |
| **4** | All three batches ingested |
| **4** | Malformed rows captured, not dropped |
| **3** | Lineage columns present |
| **2** | All three source types landed |
| **1** | API paging followed the cursor to the end |

Plus two judgement items discussed in the one-to-one, not scored here:

- Is the design explained in your README?
- Did you choose Auto Loader or a plain read — and can you say why?

## Traps, named in advance

These are in the data on purpose. Knowing they exist is not the same as
handling them.

| In the data | What it breaks |
|---|---|
| A malformed file **beside a good one** | `FAILFAST` and `DROPMALFORMED` both lose something |
| Rows that *parse* but are unusable — a bad timestamp, `N/A` in a numeric field | A corrupt-record check alone will not see them |
| An empty price → `NULL` | `price >= 0` on a NULL is NULL, not FALSE. The row passes |
| A paged API with no `totalCount` | Arithmetic over page counts stops one page early |
| One page repeating a record | A naive concatenation double-counts it |
| A late-arriving order dated three weeks back | Dating rows by load date puts it in the wrong day |

## Notes worth having

**Spark 4 defaults to ANSI mode**, so a malformed cast *raises* instead of
returning NULL. That is better behaviour in general and exactly wrong in a
rescue check — the job dies on the row you were trying to catch. Use
`try_cast` and `try_to_timestamp` on untrusted input, and a plain cast only
after validation has passed.

**Count the written table, not the DataFrame.** Counting a DataFrame after
writing it re-executes the plan, including `current_timestamp()` and
`input_file_name()`. It is a different computation and the two can disagree.

## Done means

- [ ] Both good rows from the malformed file are in `bronze/orders`
- [ ] The bad rows are in `bronze/rescued`, and you can say what is wrong with each
- [ ] `run_manifest.json` shows two runs with equal counts
- [ ] All three sources landed, with lineage columns
- [ ] Your README says which read mode you chose and why
- [ ] You can demo, in thirty seconds, a malformed file **not** losing its batch
