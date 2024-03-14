from helpers.generator_types import *
from dataclasses import dataclass
from helpers.time_helpers import timestamp_to_string
from helpers.registry_helpers import fetch_from_registry_typed
from SharedInterfaces.RegistryModels import ItemPerson, ItemSubType, ItemDataset, ItemOrganisation, ItemModelRunWorkflowTemplate, ItemModel
import itertools
from typing import TypedDict, cast, Optional, Dict

# Report generators


@dataclass
class RowEntry:
    creator: str
    organisation: str
    start_time: str
    end_time: str
    model_run_id: str
    model_run_template_id: str
    model_run_description: str
    model_run_annotations: str
    model_and_version: str
    inputs: List[str]
    outputs: List[str]


# Create a typed dictionary for rows
RowDict = TypedDict(
    'RowDict',
    {
        'creator': str,
        'organisation': str,
        'model': str,
        'start time': str,
        'end time': str,
        'model run ID': str,
        'model run template ID': str,
        'model run description': str,
        'model run annotations': str,
        'inputs': str,
        'outputs': str,
    }
)


def ds_to_cell(item: ItemDataset) -> str:
    return f"{item.display_name} ({item.id})"


def render_creator(creator: ItemPerson) -> str:
    return f"{creator.display_name} ({creator.id})"


def render_organisation(org: ItemOrganisation) -> str:
    return f"{org.display_name} ({org.id})"


def render_annotations(annotations: Dict[str, str]) -> str:
    return ", ".join([f"{key} : {value}" for key, value in annotations.items()])


def render_model_info(model: ItemModel) -> str:
    return f"{model.display_name} ({model.id})"


def render_timestamp(timestamp: int, timezone: Timezone) -> str:
    return timestamp_to_string(timestamp=timestamp, desired_tz=timezone)


def create_row_entry_from_record(
    model_run_record: ItemModelRun,
    endpoint_context: EndpointContext,
    timezone: Timezone
) -> RowEntry:
    record = model_run_record.record

    # Resolve Creator
    creator_id = record.associations.modeller_id
    creator = cast(ItemPerson, fetch_from_registry_typed(
        endpoint=endpoint_context.endpoint,
        auth=endpoint_context.auth,
        id=creator_id,
        subtype=ItemSubType.PERSON,
    ))

    # Resolve Organisation (Optional)
    org_id = record.associations.requesting_organisation_id
    organisation: Optional[ItemOrganisation] = None
    if org_id:
        organisation = cast(ItemOrganisation, fetch_from_registry_typed(
            endpoint=endpoint_context.endpoint,
            auth=endpoint_context.auth,
            id=org_id,
            subtype=ItemSubType.ORGANISATION,
        ))

    # Resolve Model run template
    template_id = record.workflow_template_id
    template = cast(ItemModelRunWorkflowTemplate, fetch_from_registry_typed(
        endpoint=endpoint_context.endpoint,
        auth=endpoint_context.auth,
        id=template_id,
        subtype=ItemSubType.MODEL_RUN_WORKFLOW_TEMPLATE,
    ))

    # Resolve model (from model run template)
    model_id = template.software_id
    model = cast(ItemModel, fetch_from_registry_typed(
        endpoint=endpoint_context.endpoint,
        auth=endpoint_context.auth,
        id=model_id,
        subtype=ItemSubType.MODEL,
    ))

    def ds_id_to_record(id: str) -> ItemDataset:
        fetched_ds = fetch_from_registry_typed(
            endpoint=endpoint_context.endpoint,
            auth=endpoint_context.auth,
            id=id,
            subtype=ItemSubType.DATASET,
        )
        return ItemDataset.parse_obj(fetched_ds.dict())

    inputs = [ds_to_cell(ds_id_to_record(ds.dataset_id))
              for ds in record.inputs]
    outputs = [ds_to_cell(ds_id_to_record(ds.dataset_id))
               for ds in record.outputs]

    return RowEntry(
        start_time=render_timestamp(record.start_time, timezone),
        end_time=render_timestamp(record.end_time, timezone),
        creator=render_creator(creator),
        organisation=render_organisation(organisation) if organisation else "",
        model_run_template_id=template.id,
        model_run_id=model_run_record.id,
        model_run_description=record.description or "",
        model_run_annotations=render_annotations(
            record.annotations) if record.annotations else "",
        model_and_version=render_model_info(model=model, template=template),
        inputs=inputs,
        outputs=outputs
    )


def row_entry_to_csv_row(entry: RowEntry) -> List[CSVRow]:
    # encode header info for record
    header_row: RowDict = {
        'creator': entry.creator,
        'organisation': entry.organisation,
        'model': entry.model_and_version,
        'start time': entry.start_time,
        'end time': entry.end_time,
        'model run ID': entry.model_run_id,
        'model run template ID': entry.model_run_template_id,
        'model run description': entry.model_run_description,
        'model run annotations': entry.model_run_annotations,
        'inputs': "",
        'outputs': "",
    }

    # process inputs/outputs
    inputs = entry.inputs
    outputs = entry.outputs

    # inject first
    if len(inputs) > 0:
        header_row['inputs'] = inputs[0]
    if len(outputs) > 0:
        header_row['outputs'] = outputs[0]

    # max index of input/output
    max_index = max(len(inputs), len(outputs))

    # body rows
    body_rows: List[RowDict] = []

    # from 1 up
    for index in range(1, max_index):
        input = ""
        output = ""
        if index < len(inputs):
            input = inputs[index]
        if index < len(outputs):
            output = outputs[index]
        body_rows.append({
            'creator': "",
            'organisation': "",
            'model': "",
            'start time': "",
            'end time': "",
            'model run ID': "",
            'model run template ID': "",
            'model run description': "",
            'model run annotations': "",
            'inputs': input,
            'outputs': output,
        })

    # have to cast typed dict -> mapping here - keeps mypy happy
    all_rows: List[CSVRow] = [cast(CSVRow, header_row)]
    all_rows.extend(map(lambda x: cast(CSVRow, x), body_rows))
    return all_rows


def generator(runs: ModelRunsType, endpoint_context: EndpointContext, timezone: Timezone) -> CSVType:
    rows: List[RowEntry] = list(
        map(lambda run: create_row_entry_from_record(
            model_run_record=run,
            endpoint_context=endpoint_context,
            timezone=timezone
        ), runs))

    return list(itertools.chain.from_iterable(map(row_entry_to_csv_row, rows)))
