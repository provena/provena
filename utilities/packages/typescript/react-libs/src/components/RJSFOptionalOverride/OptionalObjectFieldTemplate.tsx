// Sourced @ https://github.com/rjsf-team/react-jsonschema-form/blob/main/packages/mui/src/ObjectFieldTemplate/ObjectFieldTemplate.tsx
import { Checkbox, FormControlLabel } from "@mui/material";
import Grid from "@mui/material/Grid";
import {
    FormContextType,
    ObjectFieldTemplateProps,
    RJSFSchema,
    StrictRJSFSchema,
    canExpand,
    descriptionId,
    getTemplate,
    getUiOptions,
    titleId,
} from "@rjsf/utils";

interface OptionalIncludeProps {
    optionalSwitchEnabled?: boolean;
    optionalSwitchValue?: boolean;
    toggleOptionalSwitchValue?: () => void;
}

/** The `ObjectFieldTemplate` is the template to use to render all the inner properties of an object along with the
 * title and description if available. If the object is expandable, then an `AddButton` is also rendered after all
 * the properties.
 *
 * @param props - The `ObjectFieldTemplateProps` for this component
 */
export default function ObjectFieldTemplate<
    T = any,
    S extends StrictRJSFSchema = RJSFSchema,
    F extends FormContextType = any
>(props: ObjectFieldTemplateProps<T, S, F>) {
    const {
        description,
        title,
        properties,
        required,
        disabled,
        readonly,
        uiSchema,
        idSchema,
        schema,
        formData,
        onAddClick,
        registry,
    } = props;

    // Customised props
    const {
        optionalSwitchEnabled,
        optionalSwitchValue,
        toggleOptionalSwitchValue,
    } = props as unknown as OptionalIncludeProps;

    const uiOptions = getUiOptions<T, S, F>(uiSchema);
    const TitleFieldTemplate = getTemplate<"TitleFieldTemplate", T, S, F>(
        "TitleFieldTemplate",
        registry,
        uiOptions
    );
    const DescriptionFieldTemplate = getTemplate<
        "DescriptionFieldTemplate",
        T,
        S,
        F
    >("DescriptionFieldTemplate", registry, uiOptions);

    // Button templates are not overridden in the uiSchema
    const {
        ButtonTemplates: { AddButton },
    } = registry.templates;
    return (
        <>
            {title && (
                <TitleFieldTemplate
                    id={titleId<T>(idSchema)}
                    title={title}
                    required={required}
                    schema={schema}
                    uiSchema={uiSchema}
                    registry={registry}
                />
            )}
            {description && (
                <DescriptionFieldTemplate
                    id={descriptionId<T>(idSchema)}
                    description={description}
                    schema={schema}
                    uiSchema={uiSchema}
                    registry={registry}
                />
            )}
            <Grid container={true} spacing={2} style={{ marginTop: "5px" }}>
                {!!optionalSwitchEnabled && (
                    <Grid
                        item={true}
                        xs={12}
                        key={"include"}
                        style={{ marginBottom: "5px" }}
                    >
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={optionalSwitchValue}
                                    onChange={(e) => {
                                        console.log({
                                            optionalSwitchEnabled,
                                            optionalSwitchValue,
                                            toggleOptionalSwitchValue,
                                        });
                                        toggleOptionalSwitchValue &&
                                            toggleOptionalSwitchValue();
                                    }}
                                ></Checkbox>
                            }
                            label={"Include " + title + "?"}
                        ></FormControlLabel>
                    </Grid>
                )}

                {properties.map((element, index) =>
                    // Remove the <Grid> if the inner element is hidden as the <Grid>
                    // itself would otherwise still take up space.
                    element.hidden ? (
                        element.content
                    ) : (
                        <Grid
                            item={true}
                            xs={12}
                            key={index}
                            style={{ marginBottom: "10px" }}
                        >
                            {element.content}
                        </Grid>
                    )
                )}
                {canExpand<T, S, F>(schema, uiSchema, formData) && (
                    <Grid container justifyContent="flex-end">
                        <Grid item={true}>
                            <AddButton
                                className="object-property-expand"
                                onClick={onAddClick(schema)}
                                disabled={disabled || readonly}
                                uiSchema={uiSchema}
                                registry={registry}
                            />
                        </Grid>
                    </Grid>
                )}
            </Grid>
        </>
    );
}
