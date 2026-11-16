# Architecture and verification

## Model grain

| Relation or layer | Grain and responsibility |
|---|---|
| [`raw.rental_listings`](../postgres/init/sql/rental-listings.sql) | One row per observation ID. Rent lands as text so downstream rules can classify malformed values. |
| [Rental staging](../models/staging/stg_rental_listings.sql) and [intermediate models](../models/intermediate/) | One row per observation in staging. Valid and rejected views split the staging rows by quality status. The latest view keeps one valid observation per listing business key. |
| [`fct_rental_listings`](../models/marts/fct_rental_listings.sql) and [`dim_suburbs`](../models/marts/dim_suburbs.sql) | One latest valid observation per listing in the fact table and one row per distinct suburb in the dimension. The fact references the dimension through `suburb_key`. |
| [Synthetic analytics](../models/synthetic/analytics/) | Separate seed-backed tables at suburb, suburb/room type, and price band/room type grain. Their lineage begins at [`synthetic_rental_listings.csv`](../seeds/synthetic_rental_listings.csv). |

The staging and intermediate models are views. The marts and the three synthetic aggregates are tables. [dbt project configuration](../dbt_project.yml)

## Data quality and orchestration

[Python ingestion](../run_ingestion.py) validates CSV headers and observation IDs. The [PostgreSQL loader](../ingestion/postgres_loader.py) handles inserts, identical replays, and conflicts in one transaction. dbt handles business rules such as positive rent and retains the first applicable rejection reason. Its data tests also check key uniqueness, fact/dimension relationships, and aggregate counts.

The [Airflow DAG](../airflow/dags/student_rental_pipeline.py) passes the input count and ingested observation IDs through XCom. The dbt task uses a fresh artifact directory per attempt and verifies that `manifest.json` and `run_results.json` share an invocation ID. It publishes the resolved database and relations. The [final validator](../ingestion/pipeline_validation.py) uses a read-only transaction to reconcile only the current batch IDs against the valid and rejected views. Fact row count can differ from batch size because the fact contains one latest valid observation per listing across the available history.

## Local verification evidence

| Run ID | Ingestion | Classification | dbt invocation ID |
|---|---|---|---|
| `step23f_20261116_002_first` | 3 inserted, 0 skipped | 2 valid, 1 rejected | `e2fa9c6d-0f76-482a-b5fc-3b8251033fdb` |
| `step23f_20261116_002_replay` | 0 inserted, 3 skipped | 2 valid, 1 rejected | `0d15aefc-a3e5-40f7-aec6-3740b382af99` |

Both scheduler-managed runs targeted `student_rental_test_db` with build schemas `dbt_step23f_20261116_002` and `dbt_step23f_20261116_002_synthetic`. A read-only fixture mount supplied three previously absent observation IDs, including one negative rent. The first run inserted them. The replay preserved the raw row count and checksum. Both runs finished with four successful tasks and four persisted return XComs. The original development catalog and raw checksum matched their pre-run values.

- **Recorded results:** The table summarizes two local scheduler-managed runs. It is the repository’s evidence summary.
- **Runtime evidence:** Task logs remain in the local Airflow log directory. The local Airflow metadata database retains the run states and four return XComs per run, including the resolved relations, dbt invocation ID, and final validation summary. The temporary dbt artifact directories were removed by the task after use.
- **Separate checks:** The earlier clean-stack rehearsal verified PostgreSQL bootstrap, Airflow initialization and imports, and dbt connectivity. The subsequent clean-clone runs below exercised the full DAG. Hosted GitHub Actions passed 43 Python unit tests on the same published revision.

## Clean-clone E2E

Cloned the published `docs/portfolio-readiness` branch at `ef598f42d7074daf808b6155f1d80969a3c3d09d`, built the Airflow image without cache, and initialized new PostgreSQL and Airflow metadata volumes under separate Compose projects, `sri-clean003-rental` and `sri-clean003-airflow`. A temporary scheduler override routed ingestion and dbt to the new `student_rental_test_db` and supplied the mixed-quality CSV fixture via a read-only bind mount.

| Run ID | Ingestion | Classification | dbt invocation ID | Artifact directory name |
|---|---|---|---|---|
| `cleanclone_20261116_003_first` | 3 inserted, 0 skipped | 2 valid, 1 rejected | `9e503e78-4f78-48ef-92df-5dc87072148f` | `airflow-build-r0vle_n4` |
| `cleanclone_20261116_003_replay` | 0 inserted, 3 skipped | 2 valid, 1 rejected | `443ebb78-f00a-428c-841d-496accd0ffda` | `airflow-build-fs8arp0z` |

Both runs validated three CSV rows, passed all four tasks, and retained four return XComs. dbt built 12 models and 2 seeds and passed 44 tests per run in `dbt_cleanclone_20261116_003` and its `_synthetic` companion. Raw row count went from 0 to 3 and stayed at 3 on replay. The raw checksum (`e38a773de5f4abd062bc9dc987a49dc7`) was unchanged across replay, each observation appeared in exactly one quality branch, and the existing development and test databases matched their pre-test baselines.

## Isolated local runs

The [rental Compose stack](../docker-compose.yml) publishes PostgreSQL at `127.0.0.1:5433` by default. Inside the [Airflow stack](../docker-compose.airflow.yml), the scheduler uses the network alias `student-rental-postgres:5432`.

For side-by-side rehearsal, choose distinct Compose project names with `-p` for both stacks and use a separate checkout or bind-mount directory for Airflow logs and configuration. Set `RENTAL_NETWORK_NAME` to `<rental-project>_default`, and set `RENTAL_POSTGRES_HOST_PORT` and `AIRFLOW_WEB_PORT` to unused ports. Start rental PostgreSQL before Airflow. See the [README startup commands](../README.md#start-postgresql-and-airflow).

Before triggering a test DAG run:

1. In an Airflow Compose override, set both `POSTGRES_DB=student_rental_test_db` and `RENTAL_DB_NAME=student_rental_test_db` under `services.airflow-scheduler.environment`. Ingestion reads `POSTGRES_*`, while the dbt profile reads `RENTAL_DB_*`. The base Compose file maps both families to the same endpoint, so keep the host and port aligned if you override those too. Changing the shell environment for a trigger command does not change the scheduler’s task environment.
2. Mount a temporary copy of the [dbt profile](../airflow/dbt/profiles.yml) into the scheduler and point `DBT_PROFILES_DIR` to the mounted **directory**. Keep profile `default` and target `local`. Set the profile’s target schema to a fresh base name. Its synthetic models and seeds resolve to `<base_schema>_synthetic`. The raw source remains `raw.rental_listings` in the selected database.
3. Apply the override to the scheduler. Confirm the effective PostgreSQL database from a fresh connection inside that container and inspect the resolved model and seed destinations from `dbt parse` before triggering. Final validation uses the dbt relation metadata, checks that ingestion used the same endpoint, and verifies the connected database.

The DAG shares one fixed container path for [the bundled three-record fixture](../tests/fixtures/e2e_postgres_test.csv). A test-only read-only mount at that path lets both CSV tasks use fresh IDs while preserving the repository fixture.

## Host ingestion and integration test

Export `POSTGRES_HOST` (default `127.0.0.1`), `POSTGRES_PORT` (default `5433`), `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB=student_rental_test_db` in the Python process environment. Match the port to your rehearsal’s published port when using an override.

```bash
python -m pip install -r requirements.txt
python run_ingestion.py --file data/ingestion_sample.csv
python -m pytest -q tests/test_postgres_loader_integration.py
```

The [integration test](../tests/test_postgres_loader_integration.py) fixes its database name to `student_rental_test_db`, verifies the connected database, and commits a test observation there.
