import {
    ReleaseAction,
    ReleasedStatus,
} from "../shared-interfaces/RegistryAPI";

export type ReleaseActionText = "REQUESTED" | "APPROVED" | "REJECTED";
export type ReleasedStatusText = "NOT RELEASED" | "PENDING" | "RELEASED";

export interface BaseReleaseStateStyle {
    // undefined for default case
    state: ReleaseAction | ReleasedStatus;
    colour: string;
    text: ReleaseActionText | ReleasedStatusText;
}

export interface ReleaseStateStyleCollection {
    request: BaseReleaseStateStyle;
    approve: BaseReleaseStateStyle;
    reject: BaseReleaseStateStyle;
    notReleased: BaseReleaseStateStyle;
    pending: BaseReleaseStateStyle;
    released: BaseReleaseStateStyle;
    default: BaseReleaseStateStyle;
}

export const releaseStateStyleConfig = (): ReleaseStateStyleCollection => {
    // ReleaseAction
    return {
        request: {
            state: "REQUEST",
            colour: "blue", //blue
            text: "REQUESTED",
        },
        approve: {
            state: "APPROVE",
            colour: "green", //green
            text: "APPROVED",
        },
        reject: {
            state: "REJECT",
            colour: "red",
            text: "REJECTED",
        },
        // ReleasedStatus
        notReleased: {
            state: "NOT_RELEASED",
            colour: "inherit",
            text: "NOT RELEASED",
        },
        pending: {
            state: "PENDING",
            colour: "blue", //blue
            text: "PENDING",
        },
        released: {
            state: "RELEASED",
            colour: "green",
            text: "RELEASED",
        },
        // Set not released to default case
        default: {
            state: "NOT_RELEASED",
            colour: "inherit",
            text: "NOT RELEASED",
        },
    };
};

export const releaseStateStylePicker = (
    state:
        | ReleaseAction
        | ReleasedStatus
        | ReleaseActionText
        | ReleasedStatusText
        | string
): BaseReleaseStateStyle => {
    // Return the colour and displaying text for each release action and release status

    const releaseStateStyles = releaseStateStyleConfig();

    if (state == "REQUEST" || state == "REQUESTED")
        return releaseStateStyles.request;
    if (state == "APPROVE" || state == "APPROVED")
        return releaseStateStyles.approve;
    if (state == "REJECT" || state == "REJECTED")
        return releaseStateStyles.reject;
    if (state == "NOT_RELEASED" || state == "NOT RELEASED")
        return releaseStateStyles.notReleased;
    if (state == "PENDING") return releaseStateStyles.pending;
    if (state == "RELEASED") return releaseStateStyles.released;

    // Default value
    return releaseStateStyles.default;
};
