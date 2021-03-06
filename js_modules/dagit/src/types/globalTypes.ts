// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum AssetStoreOperationType {
  GET_ASSET = "GET_ASSET",
  SET_ASSET = "SET_ASSET",
}

export enum ComputeIOType {
  STDERR = "STDERR",
  STDOUT = "STDOUT",
}

export enum EvaluationErrorReason {
  FIELDS_NOT_DEFINED = "FIELDS_NOT_DEFINED",
  FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",
  MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS",
  RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH",
  SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR",
}

export enum JobStatus {
  RUNNING = "RUNNING",
  STOPPED = "STOPPED",
}

export enum JobTickStatus {
  FAILURE = "FAILURE",
  SKIPPED = "SKIPPED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum LocationStateChangeEventType {
  LOCATION_DISCONNECTED = "LOCATION_DISCONNECTED",
  LOCATION_ERROR = "LOCATION_ERROR",
  LOCATION_RECONNECTED = "LOCATION_RECONNECTED",
  LOCATION_UPDATED = "LOCATION_UPDATED",
}

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
}

export enum ObjectStoreOperationType {
  CP_OBJECT = "CP_OBJECT",
  GET_OBJECT = "GET_OBJECT",
  RM_OBJECT = "RM_OBJECT",
  SET_OBJECT = "SET_OBJECT",
}

export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  MANAGED = "MANAGED",
  NOT_STARTED = "NOT_STARTED",
  QUEUED = "QUEUED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum ScheduleStatus {
  ENDED = "ENDED",
  RUNNING = "RUNNING",
  STOPPED = "STOPPED",
}

export enum StepEventStatus {
  FAILURE = "FAILURE",
  SKIPPED = "SKIPPED",
  SUCCESS = "SUCCESS",
}

export enum StepKind {
  COMPUTE = "COMPUTE",
}

export interface AssetKeyInput {
  path: string[];
}

export interface ExecutionMetadata {
  runId?: string | null;
  tags?: ExecutionTag[] | null;
  rootRunId?: string | null;
  parentRunId?: string | null;
}

export interface ExecutionParams {
  selector: PipelineSelector;
  runConfigData?: any | null;
  mode?: string | null;
  executionMetadata?: ExecutionMetadata | null;
  stepKeys?: string[] | null;
  preset?: string | null;
}

export interface ExecutionTag {
  key: string;
  value: string;
}

export interface PartitionBackfillParams {
  selector: PartitionSetSelector;
  partitionNames: string[];
  reexecutionSteps?: string[] | null;
  fromFailure?: boolean | null;
  tags?: ExecutionTag[] | null;
}

export interface PartitionSetSelector {
  partitionSetName: string;
  repositorySelector: RepositorySelector;
}

export interface PipelineRunsFilter {
  runId?: string | null;
  pipelineName?: string | null;
  tags?: ExecutionTag[] | null;
  status?: PipelineRunStatus | null;
  snapshotId?: string | null;
}

export interface PipelineSelector {
  pipelineName: string;
  repositoryName: string;
  repositoryLocationName: string;
  solidSelection?: string[] | null;
}

export interface RepositorySelector {
  repositoryName: string;
  repositoryLocationName: string;
}

export interface ScheduleSelector {
  repositoryName: string;
  repositoryLocationName: string;
  scheduleName: string;
}

export interface SensorSelector {
  repositoryName: string;
  repositoryLocationName: string;
  sensorName: string;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
