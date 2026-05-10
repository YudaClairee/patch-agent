from pydantic import BaseModel, ConfigDict


class DashboardRead(BaseModel):
    repository_count: int
    active_run_count: int        
    succeeded_run_count: int
    today_run_count: int         
    daily_run_quota: int         

    model_config = ConfigDict(from_attributes=True)
