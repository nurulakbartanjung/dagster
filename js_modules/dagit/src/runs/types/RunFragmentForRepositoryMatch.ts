// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: RunFragmentForRepositoryMatch
// ====================================================

export interface RunFragmentForRepositoryMatch_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface RunFragmentForRepositoryMatch_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunFragmentForRepositoryMatch {
  __typename: "PipelineRun";
  id: string;
  pipeline: RunFragmentForRepositoryMatch_pipeline;
  pipelineSnapshotId: string | null;
  repositoryOrigin: RunFragmentForRepositoryMatch_repositoryOrigin | null;
}
