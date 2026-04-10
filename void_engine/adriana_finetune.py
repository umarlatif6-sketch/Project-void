"""
Adriana Fine-Tuning Pipeline

Takes JSONL training data, uploads to OpenAI fine-tuning API,
launches the fine-tuning job, polls for completion,
and stores the resulting model ID in the adriana_finetune_jobs table.

Usage (CLI):
    python -m void_engine.adriana_finetune submit --data adriana_training_data.jsonl
    python -m void_engine.adriana_finetune status --job-id ftjob-xxx
    python -m void_engine.adriana_finetune list
"""

import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

_FINETUNE_TABLE = "adriana_finetune_jobs"
_BASE_MODEL = "gpt-4o-mini-2024-07-18"


def _get_openai_client():
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    if not api_key:
        raise RuntimeError(
            "AI_INTEGRATIONS_OPENAI_API_KEY is not set. "
            "Add it via environment secrets to use fine-tuning."
        )
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_db():
    from void_engine.db_pool import get_db
    return get_db()


def init_finetune_tables():
    """Ensure the adriana_finetune_jobs table exists."""
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {_FINETUNE_TABLE} (
                id SERIAL PRIMARY KEY,
                openai_job_id VARCHAR(200) UNIQUE NOT NULL,
                openai_file_id VARCHAR(200),
                base_model VARCHAR(120) DEFAULT '{_BASE_MODEL}',
                fine_tuned_model_id VARCHAR(200),
                status VARCHAR(50) DEFAULT 'created',
                training_pairs INTEGER DEFAULT 0,
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error("init_finetune_tables failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def _to_messages_only_jsonl(jsonl_path: str) -> str:
    """
    OpenAI chat fine-tuning requires each record to contain only a `messages` key.
    Strip any extra top-level keys (system, user, assistant) that the training
    generator adds for spec compliance.  Returns path to a sanitized temp file.
    """
    import tempfile
    import json as _json

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".jsonl",
        prefix="adriana_ft_",
        delete=False,
        encoding="utf-8",
    )
    sanitized = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = _json.loads(line)
            if "messages" in record:
                tmp.write(_json.dumps({"messages": record["messages"]}, ensure_ascii=False) + "\n")
                sanitized += 1
    tmp.close()
    logger.info("Sanitized JSONL for OpenAI upload: %d records → %s", sanitized, tmp.name)
    return tmp.name


def upload_training_file(jsonl_path: str) -> str:
    """
    Upload a JSONL training file to OpenAI Files API.
    Sanitizes the file to messages-only format before upload to ensure
    OpenAI fine-tune validation passes.
    Returns the file ID.
    """
    client = _get_openai_client()
    clean_path = _to_messages_only_jsonl(jsonl_path)
    try:
        with open(clean_path, "rb") as f:
            response = client.files.create(file=f, purpose="fine-tune")
        file_id = response.id
        logger.info("Uploaded training file: %s → %s", jsonl_path, file_id)
        return file_id
    finally:
        import os as _os
        try:
            _os.unlink(clean_path)
        except OSError:
            pass


def submit_finetune_job(file_id: str, training_pairs: int = 0, base_model: str = _BASE_MODEL) -> dict:
    """
    Submit a fine-tuning job to OpenAI.
    Returns job info dict and stores to DB.
    """
    client = _get_openai_client()
    job = client.fine_tuning.jobs.create(
        training_file=file_id,
        model=base_model,
        suffix="adriana-void",
        hyperparameters={"n_epochs": 3},
    )
    job_id = job.id
    status = job.status

    _store_job(job_id, file_id, base_model, status, training_pairs)
    logger.info("Fine-tuning job submitted: %s (status=%s)", job_id, status)

    return {
        "job_id": job_id,
        "file_id": file_id,
        "status": status,
        "base_model": base_model,
    }


def _store_job(job_id: str, file_id: str, base_model: str, status: str, training_pairs: int):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            INSERT INTO {_FINETUNE_TABLE}
                (openai_job_id, openai_file_id, base_model, status, training_pairs)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (openai_job_id) DO UPDATE SET
                status = EXCLUDED.status,
                updated_at = NOW()
        """, (job_id, file_id, base_model, status, training_pairs))
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error("_store_job failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def _update_job(job_id: str, status: str, fine_tuned_model_id: Optional[str] = None, error_message: Optional[str] = None):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            UPDATE {_FINETUNE_TABLE}
            SET status = %s,
                fine_tuned_model_id = COALESCE(%s, fine_tuned_model_id),
                error_message = COALESCE(%s, error_message),
                updated_at = NOW()
            WHERE openai_job_id = %s
        """, (status, fine_tuned_model_id, error_message, job_id))
        conn.commit()
        cur.close()
    except Exception as e:
        logger.error("_update_job failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def check_job_status(job_id: str) -> dict:
    """Check the current status of a fine-tuning job."""
    client = _get_openai_client()
    job = client.fine_tuning.jobs.retrieve(job_id)
    status = job.status
    fine_tuned_model = getattr(job, "fine_tuned_model", None)
    error = getattr(job, "error", None)
    error_msg = str(error) if error else None

    _update_job(job_id, status, fine_tuned_model, error_msg)

    if fine_tuned_model:
        _persist_model_id_to_router(fine_tuned_model)

    return {
        "job_id": job_id,
        "status": status,
        "fine_tuned_model": fine_tuned_model,
        "error": error_msg,
    }


def _persist_model_id_to_router(model_id: str):
    """
    Update the ModelRouter PRECISION tier with the fine-tuned model ID.
    """
    try:
        from void_engine.aljabr_transpiler import get_model_router, TASK_PRECISION
        router = get_model_router()
        router.save_tier_config(TASK_PRECISION, model_id, None, 0.0003)
        logger.info("ModelRouter PRECISION tier updated to fine-tuned model: %s", model_id)
    except Exception as e:
        logger.error("Failed to update ModelRouter with fine-tuned model ID: %s", e)


def poll_until_complete(job_id: str, poll_interval: int = 60, max_polls: int = 120) -> dict:
    """
    Poll a fine-tuning job until it reaches a terminal state.
    Returns the final status dict.
    """
    terminal_states = {"succeeded", "failed", "cancelled"}
    for i in range(max_polls):
        result = check_job_status(job_id)
        status = result["status"]
        logger.info("Poll %d/%d — job=%s status=%s", i + 1, max_polls, job_id, status)
        if status in terminal_states:
            return result
        time.sleep(poll_interval)
    return check_job_status(job_id)


def get_latest_fine_tuned_model() -> Optional[str]:
    """
    Return the most recently succeeded fine-tuned model ID, or None.
    """
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT fine_tuned_model_id FROM {_FINETUNE_TABLE}
            WHERE status = 'succeeded' AND fine_tuned_model_id IS NOT NULL
            ORDER BY updated_at DESC LIMIT 1
        """)
        row = cur.fetchone()
        cur.close()
        return row[0] if row else None
    except Exception as e:
        logger.debug("get_latest_fine_tuned_model: table not yet available — %s", e)
        return None
    finally:
        conn.close()


def list_jobs(limit: int = 20) -> list:
    """Return recent fine-tuning job records."""
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT openai_job_id, openai_file_id, base_model, fine_tuned_model_id,
                   status, training_pairs, error_message, created_at, updated_at
            FROM {_FINETUNE_TABLE}
            ORDER BY created_at DESC LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        return [
            {
                "openai_job_id": r[0],
                "openai_file_id": r[1],
                "base_model": r[2],
                "fine_tuned_model_id": r[3],
                "status": r[4],
                "training_pairs": r[5],
                "error_message": r[6],
                "created_at": r[7].isoformat() if r[7] else None,
                "updated_at": r[8].isoformat() if r[8] else None,
            }
            for r in rows
        ]
    except Exception as e:
        logger.warning("list_jobs failed: %s", e)
        return []
    finally:
        conn.close()


def count_jsonl_lines(jsonl_path: str) -> int:
    """Count non-empty lines in a JSONL file (i.e., training pair count)."""
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


def run_full_pipeline(
    jsonl_path: str,
    training_pairs: int = 0,
    poll: bool = True,
    poll_interval: int = 60,
) -> dict:
    """
    Full pipeline: upload → submit → poll → return result.

    training_pairs is auto-counted from the JSONL file if not provided (0),
    ensuring accurate admin metrics.
    """
    init_finetune_tables()
    if training_pairs == 0:
        training_pairs = count_jsonl_lines(jsonl_path)
        logger.info("Auto-counted training pairs from JSONL: %d", training_pairs)
    file_id = upload_training_file(jsonl_path)
    job_info = submit_finetune_job(file_id, training_pairs=training_pairs)
    job_id = job_info["job_id"]

    if not poll:
        return job_info

    result = poll_until_complete(job_id, poll_interval=poll_interval)
    return {**job_info, **result}


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Adriana fine-tuning pipeline")
    subparsers = parser.add_subparsers(dest="command")

    submit_p = subparsers.add_parser("submit", help="Submit a fine-tuning job")
    submit_p.add_argument("--data", required=True, help="Path to JSONL training file")
    submit_p.add_argument("--no-poll", action="store_true", help="Don't wait for completion")
    submit_p.add_argument("--poll-interval", type=int, default=60)

    status_p = subparsers.add_parser("status", help="Check job status")
    status_p.add_argument("--job-id", required=True)

    list_p = subparsers.add_parser("list", help="List recent jobs")
    list_p.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if args.command == "submit":
        init_finetune_tables()
        result = run_full_pipeline(
            args.data,
            poll=not args.no_poll,
            poll_interval=args.poll_interval,
        )
        print(json.dumps(result, indent=2))

    elif args.command == "status":
        result = check_job_status(args.job_id)
        print(json.dumps(result, indent=2))

    elif args.command == "list":
        init_finetune_tables()
        jobs = list_jobs(args.limit)
        print(json.dumps(jobs, indent=2, default=str))

    else:
        parser.print_help()
