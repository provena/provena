import { TickBoxOverride } from "./TickBoxConsentOverride";
import { FieldProps } from "@rjsf/utils";

export const PersonEthicsTickConsent = (
    props: FieldProps<boolean | undefined>
) => {
    const LHContent = (
        <p>
            Have you received consent and been granted permission from the
            person to be registered in the registry?
        </p>
    );
    const RHContent = (
        <p>
            By registering a person, you consent to:{" "}
            <ol>
                <li>Having a Handle identifier being assigned to the person</li>
                <li>
                    The person being included and referenced in provenance and
                    dataset records in the information system
                </li>
                <li>
                    Enabling users of the information system to query the system
                    using the person identifier, e.g. related provenance and/or
                    data records
                </li>
            </ol>
        </p>
    );
    return (
        <TickBoxOverride
            additionalDescription={LHContent}
            errorContentOverride={RHContent}
            successContentOverride={RHContent}
            {...props}
        />
    );
};
