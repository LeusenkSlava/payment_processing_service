from src.outbound.rabbit_mq.tasks.outbox_relay_worker import run_outbox_relay_loop
from src.outbound.rabbit_mq.tasks.stale_processing_reaper_loop import (
    run_stale_processing_reaper_loop,
)

BACKGROUND_WORKERS = {
    "outbox_relay": run_outbox_relay_loop,
    "stale_processing_reaper": run_stale_processing_reaper_loop,
}
