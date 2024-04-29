import { OverrideDetector, OverrideDetectorList } from "./JsonDetailView";
import {
  TRUNCATION_LIMIT,
  truncationOverride,
  uriOverride,
  urlOverride,
} from "./JsonRendererOverrides";

/**
    This file contains detectors against specific value types. 

    These detectors take a name and value and return an override, if any.

    This enables bulk application of styling overrides based on common properties. 

    E.g. URL detection, renames of fields etc
 */

const urlDetector: OverrideDetector<string> = (name: string, value: string) => {
  /**
        Detects if there is a URL by looking for HTTP
     */
  if (value.startsWith("http")) {
    return urlOverride;
  }
  return undefined;
};

const truncationDetector: OverrideDetector<string> = (
  name: string,
  value: string,
) => {
  /**
        Detects if truncation is required by checking for length > limit
     */
  if (value.length > TRUNCATION_LIMIT) {
    return truncationOverride;
  }
  return undefined;
};

const uriNameDetector: OverrideDetector<string> = (
  name: string,
  value: string,
) => {
  /**
        Detects if uri -> URI rename required by checking for substring
     */
  if (name.indexOf("uri") !== -1) {
    return uriOverride;
  }
  return undefined;
};

export const STRING_AUTO_DETECTORS: OverrideDetectorList<string> = [
  urlDetector,
  uriNameDetector,
  truncationDetector,
];
export const NUMBER_AUTO_DETECTORS: OverrideDetectorList<number> = [];
export const BOOLEAN_AUTO_DETECTORS: OverrideDetectorList<boolean> = [];
export const OBJECT_AUTO_DETECTORS: OverrideDetectorList<object> = [];
