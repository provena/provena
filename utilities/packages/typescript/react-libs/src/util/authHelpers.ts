export interface ResourceAccess {
  readMetadata: boolean;
  writeMetadata: boolean;
  admin: boolean;
}

const checkAccessRole = (
  userRoles: string[],
  acceptableRoles: string[],
): boolean => {
  var found = false;
  for (const possibleRole of acceptableRoles) {
    if (userRoles.indexOf(possibleRole) !== -1) {
      found = true;
      break;
    }
  }
  return found;
};

const readMetadataRoles: string[] = [
  "metadata-read",
  "metadata-write",
  "admin",
];
const writeMetadataRoles: string[] = ["metadata-write", "admin"];
const adminRoles: string[] = ["admin"];

export const deriveResourceAccess = (
  roles: string[] | undefined,
): ResourceAccess | undefined => {
  if (roles === undefined) {
    return undefined;
  }
  return {
    readMetadata: checkAccessRole(roles, readMetadataRoles),
    writeMetadata: checkAccessRole(roles, writeMetadataRoles),
    admin: checkAccessRole(roles, adminRoles),
  } as ResourceAccess;
};

export interface DatasetAccess {
  readMetadata: boolean;
  writeMetadata: boolean;
  admin: boolean;
  readData: boolean;
  writeData: boolean;
}

const dataReadRoles: string[] = [
  "dataset-data-read",
  "dataset-data-write",
  "admin",
];
const dataWriteRoles: string[] = ["dataset-data-write", "admin"];

export const deriveDatasetAccess = (
  roles: string[] | undefined,
): DatasetAccess | undefined => {
  if (roles === undefined) {
    return undefined;
  }
  return {
    readMetadata: checkAccessRole(roles, readMetadataRoles),
    writeMetadata: checkAccessRole(roles, writeMetadataRoles),
    admin: checkAccessRole(roles, adminRoles),
    readData: checkAccessRole(roles, dataReadRoles),
    writeData: checkAccessRole(roles, dataWriteRoles),
  } as DatasetAccess;
};
