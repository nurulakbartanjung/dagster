import datetime
import warnings
from collections import OrderedDict

import pendulum
from croniter import croniter
from dagster import check
from dagster.core.definitions.job import JobType
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.snap import ExecutionPlanSnapshot
from dagster.core.utils import toposort

from .external_data import (
    ExternalJobData,
    ExternalPartitionSetData,
    ExternalPipelineData,
    ExternalRepositoryData,
    ExternalScheduleData,
)
from .handle import JobHandle, PartitionSetHandle, PipelineHandle, RepositoryHandle
from .pipeline_index import PipelineIndex
from .represented import RepresentedPipeline


class ExternalRepository:
    """
    ExternalRepository is a object that represents a loaded repository definition that
    is resident in another process or container. Host processes such as dagit use
    objects such as these to interact with user-defined artifacts.
    """

    def __init__(self, external_repository_data, repository_handle):
        self.external_repository_data = check.inst_param(
            external_repository_data, "external_repository_data", ExternalRepositoryData
        )
        self._pipeline_index_map = OrderedDict(
            (
                external_pipeline_data.pipeline_snapshot.name,
                PipelineIndex(
                    external_pipeline_data.pipeline_snapshot,
                    external_pipeline_data.parent_pipeline_snapshot,
                ),
            )
            for external_pipeline_data in external_repository_data.external_pipeline_datas
        )
        self._handle = check.inst_param(repository_handle, "repository_handle", RepositoryHandle)

        self._job_map = OrderedDict(
            (external_job_data.name, external_job_data)
            for external_job_data in external_repository_data.external_job_datas
        )

    @property
    def name(self):
        return self.external_repository_data.name

    def get_pipeline_index(self, pipeline_name):
        return self._pipeline_index_map[pipeline_name]

    def has_pipeline(self, pipeline_name):
        return pipeline_name in self._pipeline_index_map

    def get_pipeline_indices(self):
        return self._pipeline_index_map.values()

    def has_external_pipeline(self, pipeline_name):
        return pipeline_name in self._pipeline_index_map

    def get_external_schedule(self, schedule_name):
        return ExternalSchedule(
            self.external_repository_data.get_external_schedule_data(schedule_name), self._handle
        )

    def get_external_schedules(self):
        return [
            ExternalSchedule(external_schedule_data, self._handle)
            for external_schedule_data in self.external_repository_data.external_schedule_datas
        ]

    def get_external_sensor(self, sensor_name):
        job_data = self.external_repository_data.get_external_job_data(sensor_name)
        if job_data.job_type != JobType.SENSOR:
            check.failed("Could not find sensor named " + sensor_name)

        return ExternalSensor(job_data, self._handle)

    def get_external_sensors(self):
        return [
            ExternalSensor(external_job_data, self._handle)
            for external_job_data in self.external_repository_data.external_job_datas
            if external_job_data.job_type == JobType.SENSOR
        ]

    def get_external_jobs(self):
        external = []
        for external_job_data in self.external_repository_data.external_job_datas:
            if external_job_data.job_type == JobType.SENSOR:
                external.append(ExternalSensor(external_job_data, self._handle))
            elif external_job_data.job_type == JobType.SCHEDULE:
                external.append(ExternalSchedule(external_job_data, self._handle))
        return external

    def has_external_job(self, job_name):
        return job_name in self._job_map

    def get_external_job(self, job_name):
        external_job_data = self._job_map[job_name]
        if external_job_data.job_type == JobType.SENSOR:
            return ExternalSensor(external_job_data, self._handle)
        if external_job_data.job_type == JobType.SCHEDULE:
            return ExternalSchedule(external_job_data, self._handle)
        return None

    def get_external_partition_set(self, partition_set_name):
        return ExternalPartitionSet(
            self.external_repository_data.get_external_partition_set_data(partition_set_name),
            self._handle,
        )

    def get_external_partition_sets(self):
        return [
            ExternalPartitionSet(external_partition_set_data, self._handle)
            for external_partition_set_data in self.external_repository_data.external_partition_set_datas
        ]

    def get_full_external_pipeline(self, pipeline_name):
        check.str_param(pipeline_name, "pipeline_name")
        return ExternalPipeline(
            self.external_repository_data.get_external_pipeline_data(pipeline_name),
            repository_handle=self.handle,
            pipeline_index=self.get_pipeline_index(pipeline_name),
        )

    def get_all_external_pipelines(self):
        return [self.get_full_external_pipeline(pn) for pn in self._pipeline_index_map]

    @property
    def handle(self):
        return self._handle

    def get_external_origin(self):
        return self.handle.get_external_origin()

    def get_python_origin(self):
        return self.handle.repository_location_handle.get_repository_python_origin(self.name,)

    def get_external_origin_id(self):
        """
        A means of identifying the repository this ExternalRepository represents based on
        where it came from.
        """
        return self.get_external_origin().get_id()


class ExternalPipeline(RepresentedPipeline):
    """
    ExternalPipeline is a object that represents a loaded pipeline definition that
    is resident in another process or container. Host processes such as dagit use
    objects such as these to interact with user-defined artifacts.
    """

    def __init__(self, external_pipeline_data, repository_handle, pipeline_index=None):
        check.inst_param(repository_handle, "repository_handle", RepositoryHandle)
        check.inst_param(external_pipeline_data, "external_pipeline_data", ExternalPipelineData)
        check.opt_inst_param(pipeline_index, "pipeline_index", PipelineIndex)

        if pipeline_index is None:
            pipeline_index = PipelineIndex(
                external_pipeline_data.pipeline_snapshot,
                external_pipeline_data.parent_pipeline_snapshot,
            )

        super(ExternalPipeline, self).__init__(pipeline_index=pipeline_index)
        self._external_pipeline_data = external_pipeline_data
        self._repository_handle = repository_handle
        self._active_preset_dict = {ap.name: ap for ap in external_pipeline_data.active_presets}
        self._handle = PipelineHandle(self._pipeline_index.name, repository_handle)

    @property
    def name(self):
        return self._pipeline_index.pipeline_snapshot.name

    @property
    def description(self):
        return self._pipeline_index.pipeline_snapshot.description

    @property
    def solid_names_in_topological_order(self):
        return self._pipeline_index.pipeline_snapshot.solid_names_in_topological_order

    @property
    def external_pipeline_data(self):
        return self._external_pipeline_data

    @property
    def repository_handle(self):
        return self._repository_handle

    @property
    def solid_selection(self):
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.solid_selection
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    @property
    def solids_to_execute(self):
        return (
            self._pipeline_index.pipeline_snapshot.lineage_snapshot.solids_to_execute
            if self._pipeline_index.pipeline_snapshot.lineage_snapshot
            else None
        )

    @property
    def active_presets(self):
        return list(self._active_preset_dict.values())

    @property
    def solid_names(self):
        return self._pipeline_index.pipeline_snapshot.solid_names

    def has_solid_invocation(self, solid_name):
        check.str_param(solid_name, "solid_name")
        return self._pipeline_index.has_solid_invocation(solid_name)

    def has_preset(self, preset_name):
        check.str_param(preset_name, "preset_name")
        return preset_name in self._active_preset_dict

    def get_preset(self, preset_name):
        check.str_param(preset_name, "preset_name")
        return self._active_preset_dict[preset_name]

    @property
    def available_modes(self):
        return self._pipeline_index.available_modes

    def has_mode(self, mode_name):
        check.str_param(mode_name, "mode_name")
        return self._pipeline_index.has_mode_def(mode_name)

    def root_config_key_for_mode(self, mode_name):
        check.opt_str_param(mode_name, "mode_name")
        return self.get_mode_def_snap(
            mode_name if mode_name else self.get_default_mode_name()
        ).root_config_key

    def get_default_mode_name(self):
        return self._pipeline_index.get_default_mode_name()

    @property
    def tags(self):
        return self._pipeline_index.pipeline_snapshot.tags

    @property
    def computed_pipeline_snapshot_id(self):
        return self._pipeline_index.pipeline_snapshot_id

    @property
    def identifying_pipeline_snapshot_id(self):
        return self._pipeline_index.pipeline_snapshot_id

    @property
    def handle(self):
        return self._handle

    def get_origin(self):
        # Returns a PipelinePythonOrigin - maintained for backwards compatibility since this
        # is called in several run launchers to start execution
        warnings.warn(
            "ExternalPipeline.get_origin() is deprecated. Use get_python_origin() if you want "
            "an origin to use for pipeline execution, or get_external_origin if you want an origin "
            "to load an ExternalPipeline."
        )
        return self.get_python_origin()

    def get_python_origin(self):
        repository_python_origin = self.repository_handle.repository_location_handle.get_repository_python_origin(
            self.repository_handle.repository_name,
        )
        return PipelinePythonOrigin(self.name, repository_python_origin)

    def get_external_origin(self):
        return self.handle.get_external_origin()

    def get_external_origin_id(self):
        return self.get_external_origin().get_id()

    @property
    def pipeline_snapshot(self):
        return self._pipeline_index.pipeline_snapshot


class ExternalExecutionPlan:
    """
    ExternalExecution is a object that represents an execution plan that
    was compiled in another process or persisted in an instance.
    """

    def __init__(self, execution_plan_snapshot, represented_pipeline):
        self.execution_plan_snapshot = check.inst_param(
            execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot
        )
        self.represented_pipeline = check.inst_param(
            represented_pipeline, "represented_pipeline", RepresentedPipeline
        )

        self._step_index = {step.key: step for step in self.execution_plan_snapshot.steps}

        check.invariant(
            execution_plan_snapshot.pipeline_snapshot_id
            == represented_pipeline.identifying_pipeline_snapshot_id
        )

        self._step_keys_in_plan = (
            set(execution_plan_snapshot.step_keys_to_execute)
            if execution_plan_snapshot.step_keys_to_execute
            else set(self._step_index.keys())
        )

        self._deps = None
        self._topological_steps = None
        self._topological_step_levels = None

    @property
    def step_keys_in_plan(self):
        return list(self._step_keys_in_plan)

    def has_step(self, key):
        check.str_param(key, "key")
        return key in self._step_index

    def get_step_by_key(self, key):
        check.str_param(key, "key")
        return self._step_index[key]

    def get_steps_in_plan(self):
        return [self._step_index[sk] for sk in self._step_keys_in_plan]

    def key_in_plan(self, key):
        return key in self._step_keys_in_plan

    # Everything below this line is a near-copy of the equivalent methods on
    # ExecutionPlan. We should resolve this, probably eventually by using the
    # snapshots to support the existing ExecutionPlan methods.
    # https://github.com/dagster-io/dagster/issues/2462
    def execution_deps(self):
        if self._deps is None:
            deps = OrderedDict()

            for key in self._step_keys_in_plan:
                deps[key] = set()

            for key in self._step_keys_in_plan:
                step = self._step_index[key]
                for step_input in step.inputs:
                    deps[step.key].update(
                        {
                            output_handle.step_key
                            for output_handle in step_input.upstream_output_handles
                        }.intersection(self._step_keys_in_plan)
                    )
            self._deps = deps

        return self._deps

    def topological_steps(self):
        if self._topological_steps is None:
            self._topological_steps = [
                step for step_level in self.topological_step_levels() for step in step_level
            ]

        return self._topological_steps

    def topological_step_levels(self):
        if self._topological_step_levels is None:
            self._topological_step_levels = [
                [self._step_index[step_key] for step_key in sorted(step_key_level)]
                for step_key_level in toposort(self.execution_deps())
            ]

        return self._topological_step_levels


class ExternalSchedule:
    def __init__(self, external_schedule_data, handle):
        self._external_schedule_data = check.inst_param(
            external_schedule_data, "external_schedule_data", ExternalScheduleData
        )
        self._handle = JobHandle(
            self._external_schedule_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self):
        return self._external_schedule_data.name

    @property
    def cron_schedule(self):
        return self._external_schedule_data.cron_schedule

    @property
    def execution_timezone(self):
        return self._external_schedule_data.execution_timezone

    @property
    def solid_selection(self):
        return self._external_schedule_data.solid_selection

    @property
    def pipeline_name(self):
        return self._external_schedule_data.pipeline_name

    @property
    def mode(self):
        return self._external_schedule_data.mode

    @property
    def partition_set_name(self):
        return self._external_schedule_data.partition_set_name

    @property
    def environment_vars(self):
        return self._external_schedule_data.environment_vars

    @property
    def handle(self):
        return self._handle

    def get_external_origin(self):
        return self.handle.get_external_origin()

    def get_external_origin_id(self):
        return self.get_external_origin().get_id()

    # ScheduleState that represents the state of the schedule
    # when there is no row in the schedule DB (for example, when
    # the schedule is first created in code)
    def get_default_job_state(self):
        from dagster.core.scheduler.job import JobState, JobStatus, ScheduleJobData

        return JobState(
            self.get_external_origin(),
            JobType.SCHEDULE,
            JobStatus.STOPPED,
            ScheduleJobData(self.cron_schedule, start_timestamp=None),
        )

    def execution_time_iterator(self, start_timestamp):
        check.float_param(start_timestamp, "start_timestamp")

        timezone_str = (
            self.execution_timezone if self.execution_timezone else pendulum.now().timezone.name
        )

        start_datetime = pendulum.from_timestamp(start_timestamp, tz=timezone_str)

        date_iter = croniter(self.cron_schedule, start_datetime)

        # Go back one iteration so that the next iteration is the first time that is >= start_datetime
        # and matches the cron schedule
        date_iter.get_prev(datetime.datetime)

        while True:
            next_date = pendulum.instance(date_iter.get_next(datetime.datetime)).in_tz(timezone_str)

            # During DST transitions, croniter returns datetimes that don't actually match the
            # cron schedule, so add a guard here
            if croniter.match(self.cron_schedule, next_date):
                yield next_date


class ExternalSensor:
    def __init__(self, external_job_data, handle):
        self._external_job_data = check.inst_param(
            external_job_data, "external_job_data", ExternalJobData,
        )
        check.param_invariant(external_job_data.job_type == JobType.SENSOR, "external_job_data")
        self._handle = JobHandle(
            self._external_job_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self):
        return self._external_job_data.name

    @property
    def pipeline_name(self):
        return self._external_job_data.pipeline_name

    @property
    def solid_selection(self):
        return self._external_job_data.solid_selection

    @property
    def mode(self):
        return self._external_job_data.mode

    def get_external_origin(self):
        return self._handle.get_external_origin()

    def get_external_origin_id(self):
        return self.get_external_origin().get_id()

    def get_default_job_state(self):
        from dagster.core.scheduler.job import JobState, JobStatus

        return JobState(self.get_external_origin(), JobType.SENSOR, JobStatus.STOPPED)


class ExternalPartitionSet:
    def __init__(self, external_partition_set_data, handle):
        self._external_partition_set_data = check.inst_param(
            external_partition_set_data, "external_partition_set_data", ExternalPartitionSetData
        )
        self._handle = PartitionSetHandle(
            external_partition_set_data.name, check.inst_param(handle, "handle", RepositoryHandle)
        )

    @property
    def name(self):
        return self._external_partition_set_data.name

    @property
    def solid_selection(self):
        return self._external_partition_set_data.solid_selection

    @property
    def mode(self):
        return self._external_partition_set_data.mode

    @property
    def pipeline_name(self):
        return self._external_partition_set_data.pipeline_name
