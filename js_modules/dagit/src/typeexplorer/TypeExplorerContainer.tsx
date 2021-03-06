import {gql, useQuery} from '@apollo/client';
import * as React from 'react';

import {Loading} from 'src/Loading';
import {PipelineExplorerPath} from 'src/PipelinePathUtils';
import {TypeExplorer} from 'src/typeexplorer/TypeExplorer';
import {
  TypeExplorerContainerQuery,
  TypeExplorerContainerQueryVariables,
} from 'src/typeexplorer/types/TypeExplorerContainerQuery';
import {usePipelineSelector} from 'src/workspace/WorkspaceContext';

interface ITypeExplorerContainerProps {
  explorerPath: PipelineExplorerPath;
  typeName: string;
}

export const TypeExplorerContainer: React.FunctionComponent<ITypeExplorerContainerProps> = ({
  explorerPath,
  typeName,
}) => {
  const pipelineSelector = usePipelineSelector(explorerPath.pipelineName);
  const queryResult = useQuery<TypeExplorerContainerQuery, TypeExplorerContainerQueryVariables>(
    TYPE_EXPLORER_CONTAINER_QUERY,
    {
      fetchPolicy: 'cache-and-network',
      variables: {
        pipelineSelector,
        dagsterTypeName: typeName,
      },
    },
  );
  return (
    <Loading queryResult={queryResult}>
      {(data) => {
        if (
          data.pipelineOrError &&
          data.pipelineOrError.__typename === 'Pipeline' &&
          data.pipelineOrError.dagsterTypeOrError &&
          data.pipelineOrError.dagsterTypeOrError.__typename === 'RegularDagsterType'
        ) {
          return <TypeExplorer type={data.pipelineOrError.dagsterTypeOrError} />;
        } else {
          return <div>Type Not Found</div>;
        }
      }}
    </Loading>
  );
};

export const TYPE_EXPLORER_CONTAINER_QUERY = gql`
  query TypeExplorerContainerQuery(
    $pipelineSelector: PipelineSelector!
    $dagsterTypeName: String!
  ) {
    pipelineOrError(params: $pipelineSelector) {
      __typename
      ... on Pipeline {
        id
        dagsterTypeOrError(dagsterTypeName: $dagsterTypeName) {
          __typename
          ... on RegularDagsterType {
            ...TypeExplorerFragment
          }
        }
      }
    }
  }
  ${TypeExplorer.fragments.TypeExplorerFragment}
`;
