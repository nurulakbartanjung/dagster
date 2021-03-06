from collections import namedtuple
from enum import Enum

from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.host_representation.origin import ExternalJobOrigin
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class JobStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


@whitelist_for_serdes
class SensorJobData(namedtuple("_SensorJobData", "last_completed_timestamp")):
    def __new__(cls, last_completed_timestamp=None):
        return super(SensorJobData, cls).__new__(
            cls, check.opt_float_param(last_completed_timestamp, "last_completed_timestamp"),
        )


@whitelist_for_serdes
class ScheduleJobData(namedtuple("_ScheduleJobData", "cron_schedule start_timestamp")):
    def __new__(cls, cron_schedule, start_timestamp=None):
        return super(ScheduleJobData, cls).__new__(
            cls,
            check.str_param(cron_schedule, "cron_schedule"),
            # Time in UTC at which the user started running the schedule (distinct from
            # `start_date` on partition-based schedules, which is used to define
            # the range of partitions)
            check.opt_float_param(start_timestamp, "start_timestamp"),
        )


def check_job_data(job_type, job_specific_data):
    check.inst_param(job_type, "job_type", JobType)
    if job_type == JobType.SCHEDULE:
        check.inst_param(job_specific_data, "job_specific_data", ScheduleJobData)
    elif job_type == JobType.SENSOR:
        check.opt_inst_param(job_specific_data, "job_specific_data", SensorJobData)
    else:
        check.failed(
            "Unexpected job type {}, expected one of JobType.SENSOR, JobType.SCHEDULE".format(
                job_type
            )
        )

    return job_specific_data


@whitelist_for_serdes
class JobState(namedtuple("_JobState", "origin job_type status job_specific_data")):
    def __new__(cls, origin, job_type, status, job_specific_data=None):
        return super(JobState, cls).__new__(
            cls,
            check.inst_param(origin, "origin", ExternalJobOrigin),
            check.inst_param(job_type, "job_type", JobType),
            check.inst_param(status, "status", JobStatus),
            check_job_data(job_type, job_specific_data),
        )

    @property
    def name(self):
        return self.origin.job_name

    @property
    def job_name(self):
        return self.origin.job_name

    @property
    def repository_origin_id(self):
        return self.origin.external_repository_origin.get_id()

    @property
    def job_origin_id(self):
        return self.origin.get_id()

    def with_status(self, status):
        check.inst_param(status, "status", JobStatus)
        return JobState(
            self.origin,
            job_type=self.job_type,
            status=status,
            job_specific_data=self.job_specific_data,
        )

    def with_data(self, job_specific_data):
        check_job_data(self.job_type, job_specific_data)
        return JobState(
            self.origin,
            job_type=self.job_type,
            status=self.status,
            job_specific_data=job_specific_data,
        )


@whitelist_for_serdes
class JobTickStatus(Enum):
    STARTED = "STARTED"
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class JobTick(namedtuple("_JobTick", "tick_id job_tick_data")):
    def __new__(cls, tick_id, job_tick_data):
        return super(JobTick, cls).__new__(
            cls,
            check.int_param(tick_id, "tick_id"),
            check.inst_param(job_tick_data, "job_tick_data", JobTickData),
        )

    def with_status(self, status, **kwargs):
        check.inst_param(status, "status", JobTickStatus)
        return self._replace(job_tick_data=self.job_tick_data.with_status(status, **kwargs))

    @property
    def job_origin_id(self):
        return self.job_tick_data.job_origin_id

    @property
    def job_name(self):
        return self.job_tick_data.job_name

    @property
    def job_type(self):
        return self.job_tick_data.job_type

    @property
    def timestamp(self):
        return self.job_tick_data.timestamp

    @property
    def run_key(self):
        return self.job_tick_data.run_key

    @property
    def status(self):
        return self.job_tick_data.status

    @property
    def run_id(self):
        return self.job_tick_data.run_id

    @property
    def error(self):
        return self.job_tick_data.error


@whitelist_for_serdes
class JobTickData(
    namedtuple(
        "_JobTickData", "job_origin_id job_name job_type status timestamp run_id error run_key",
    )
):
    def __new__(
        cls,
        job_origin_id,
        job_name,
        job_type,
        status,
        timestamp,
        run_id=None,
        error=None,
        run_key=None,
    ):
        """
        This class defines the data that is serialized and stored in ``JobStorage``. We depend
        on the job storage implementation to provide job tick ids, and therefore
        separate all other data into this serializable class that can be stored independently of the
        id

        Arguments:
            job_origin_id (str): The id of the job target for this tick
            job_name (str): The name of the job for this tick
            job_type (JobType): The type of this job for this tick
            status (JobTickStatus): The status of the tick, which can be updated
            timestamp (float): The timestamp at which this job evaluation started

        Keyword Arguments:
            run_id (str): The run created by the tick.
            error (SerializableErrorInfo): The error caught during job execution. This is set
                only when the status is ``JobTickStatus.Failure``
            run_key (Optional[str]): A string that uniquely identifies a pipeline execution
        """

        _validate_job_tick_args(job_type, status, run_id, error)
        return super(JobTickData, cls).__new__(
            cls,
            check.str_param(job_origin_id, "job_origin_id"),
            check.str_param(job_name, "job_name"),
            check.inst_param(job_type, "job_type", JobType),
            check.inst_param(status, "status", JobTickStatus),
            check.float_param(timestamp, "timestamp"),
            run_id,  # validated in _validate_job_tick_args
            error,  # validated in _validate_job_tick_args
            check.opt_str_param(run_key, "run_key"),
        )

    def with_status(self, status, run_id=None, error=None, timestamp=None, run_key=None):
        check.inst_param(status, "status", JobTickStatus)
        return JobTickData(
            job_origin_id=self.job_origin_id,
            job_name=self.job_name,
            job_type=self.job_type,
            status=status,
            timestamp=timestamp if timestamp is not None else self.timestamp,
            run_id=run_id if run_id is not None else self.run_id,
            error=error if error is not None else self.error,
            run_key=run_key if run_key is not None else self.run_key,
        )


def _validate_job_tick_args(job_type, status, run_id=None, error=None):
    check.inst_param(job_type, "job_type", JobType)
    check.inst_param(status, "status", JobTickStatus)

    if status == JobTickStatus.SUCCESS:
        check.str_param(run_id, "run_id")
        check.invariant(error is None, desc="Job tick status is SUCCESS, but error was provided")
    elif status == JobTickStatus.FAILURE:
        check.inst_param(error, "error", SerializableErrorInfo)
    else:
        check.invariant(error is None, "Job tick status was not FAILURE but error was provided")


class JobTickStatsSnapshot(
    namedtuple(
        "JobTickStatsSnapshot", ("ticks_started ticks_succeeded ticks_skipped ticks_failed"),
    )
):
    def __new__(
        cls, ticks_started, ticks_succeeded, ticks_skipped, ticks_failed,
    ):
        return super(JobTickStatsSnapshot, cls).__new__(
            cls,
            ticks_started=check.int_param(ticks_started, "ticks_started"),
            ticks_succeeded=check.int_param(ticks_succeeded, "ticks_succeeded"),
            ticks_skipped=check.int_param(ticks_skipped, "ticks_skipped"),
            ticks_failed=check.int_param(ticks_failed, "ticks_failed"),
        )
