import { Buffer } from "buffer";
import { ReportComponentRole } from "./provena-interfaces/AuthAPI";
export const parseJwt = (token: string) => {
  var base64Payload = token.split(".")[1];
  var payload = Buffer.from(base64Payload, "base64");
  return JSON.parse(payload.toString());
};

export const not = (
  a: readonly ReportComponentRole[],
  b: readonly ReportComponentRole[],
) => {
  return a.filter(
    (aValue) =>
      b.findIndex((bValue) => bValue.role_name != aValue.role_name) === -1,
  );
};

export const intersection = (
  a: readonly ReportComponentRole[],
  b: readonly ReportComponentRole[],
) => {
  return a.filter(
    (aValue) =>
      b.findIndex((bValue) => bValue.role_name != aValue.role_name) !== -1,
  );
};
