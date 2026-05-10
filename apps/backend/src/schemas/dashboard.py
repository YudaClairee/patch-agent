from pydantic import BaseModel, ConfigDict


class DashboardRead(BaseModel):
    repository_count: int
    active_run_count: int        # status in (queued, running)
    succeeded_run_count: int
    today_run_count: int         # from usage_records
    daily_run_quota: int         # from users.daily_run_quota

    model_config = ConfigDict(from_attributes=True)
