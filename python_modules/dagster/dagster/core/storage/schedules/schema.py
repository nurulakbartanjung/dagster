import sqlalchemy as db

ScheduleStorageSqlMetadata = db.MetaData()

ScheduleTable = db.Table(
    "schedules",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("schedule_origin_id", db.String(255), unique=True),
    db.Column("repository_origin_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("schedule_body", db.String),
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
)

ScheduleTickTable = db.Table(
    "schedule_ticks",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("schedule_origin_id", db.String(255), index=True),
    db.Column("status", db.String(63)),
    # utc timezone - make an index as a breaking change for 0.10.0
    # (https://github.com/dagster-io/dagster/issues/2956)
    db.Column("timestamp", db.types.TIMESTAMP),
    db.Column("tick_body", db.String),
    # The create and update timestamps are not used in framework code, are are simply
    # present for debugging purposes.
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
)

JobTable = db.Table(
    "jobs",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("job_origin_id", db.String(255), unique=True),
    db.Column("repository_origin_id", db.String(255)),
    db.Column("status", db.String(63)),
    db.Column("job_type", db.String(63), index=True),
    db.Column("job_body", db.String),
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
)

JobTickTable = db.Table(
    "job_ticks",
    ScheduleStorageSqlMetadata,
    db.Column("id", db.Integer, primary_key=True, autoincrement=True),
    db.Column("job_origin_id", db.String(255), index=True),
    db.Column("status", db.String(63)),
    db.Column("type", db.String(63)),
    db.Column("run_key", db.String),
    db.Column("timestamp", db.types.TIMESTAMP),
    db.Column("tick_body", db.String),
    db.Column("create_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
    db.Column("update_timestamp", db.DateTime, server_default=db.text("CURRENT_TIMESTAMP")),
)

db.Index("idx_job_tick_run_key", JobTickTable.c.job_origin_id, JobTickTable.c.run_key)
db.Index("idx_job_tick_status", JobTickTable.c.job_origin_id, JobTickTable.c.status)
db.Index("idx_job_tick_timestamp", JobTickTable.c.job_origin_id, JobTickTable.c.timestamp)
