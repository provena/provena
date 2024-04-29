export interface BaseLoadedEntity {
  loading: boolean;
  error: boolean;
  errorMessage?: string;
  success: boolean;
}

export interface BaseLoadedEntityWithRefetch extends BaseLoadedEntity {
  refetch: () => void;
}

export interface LoadedEntity<T> extends BaseLoadedEntity {
  data?: T;
}

export interface LoadedWithRefetch<T> extends LoadedEntity<T> {
  refetch: () => void;
}
export interface UseQuerySubInterface {
  // This defines the set of properties we are interested in from the react
  // query for parsing error/status info
  isFetching: boolean;
  isError: boolean;
  error?: unknown;
  isSuccess: boolean;
}

export interface UseQuerySubInterfaceWithRefetch {
  // This defines the set of properties we are interested in from the react
  // query for parsing error/status info
  isFetching: boolean;
  isError: boolean;
  error?: unknown;
  isSuccess: boolean;
  refetch: () => void;
}

export const mapQueryToLoadedEntity = (
  queryResult: UseQuerySubInterface,
): BaseLoadedEntity => {
  return {
    loading: queryResult.isFetching,
    error: queryResult.isError,
    success: queryResult.isSuccess,
    errorMessage: queryResult.error ? (queryResult.error as string) : undefined,
  };
};

export const mapQueryToLoadedWithRefetch = (
  queryResult: UseQuerySubInterfaceWithRefetch,
): BaseLoadedEntityWithRefetch => {
  return {
    loading: queryResult.isFetching,
    error: queryResult.isError,
    success: queryResult.isSuccess,
    errorMessage: queryResult.error ? (queryResult.error as string) : undefined,
    refetch: queryResult.refetch,
  };
};

export const combineLoadStates = (
  loads: Array<BaseLoadedEntity | undefined>,
): BaseLoadedEntity => {
  const error = loads.some((i) => (i !== undefined ? i.error : false));
  const success = !loads.some((i) => (i !== undefined ? !i.success : true));
  const loading = loads.some((i) => (i !== undefined ? i.loading : false));
  const errorMessage = error
    ? loads.find((i) => {
        return i && i.errorMessage !== undefined;
      })?.errorMessage!
    : undefined;
  return {
    loading,
    success,
    error,
    errorMessage,
  };
};
