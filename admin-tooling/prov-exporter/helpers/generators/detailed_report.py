from helpers.generator_types import *
from dataclasses import dataclass
from helpers.time_helpers import timestamp_to_string
from helpers.registry_helpers import fetch_from_registry_typed
from ProvenaInterfaces.RegistryModels import ItemPerson, ItemSubType, ItemDataset, ItemOrganisation, ItemModelRunWorkflowTemplate, ItemModel
import itertools
from typing import TypedDict, cast, Optional, Dict, Tuple, Set

# Report generators


@dataclass
class RowEntry:
    # associations
    agent: str
    agent_name: str
    agent_id: str
    organisation: str
    organisation_name: str
    organisation_id: str

    # start/end time
    start_time: str
    end_time: str

    # model information
    model_combined: str
    model_name: str
    model_id: str
    model_version: str

    # model run information
    model_run_id: str
    model_run_template_id: str
    model_run_description: str
    # list of (k,v) tuples
    model_run_annotations: List[Tuple[str, str]]

    # inputs and outputs
    input_names: List[str]
    input_ids: List[str]
    output_names: List[str]
    output_ids: List[str]


# Create a typed dictionary for rows - we may need to extend to include annotation columns
BaseRowDict = TypedDict(
    'BaseRowDict',
    {
        'agent': str,
        'agent name': str,
        'agent id': str,
        'organisation': str,
        'organisation name': str,
        'organisation id': str,
        'model': str,
        'model name': str,
        'model id': str,
        'model version': str,
        'start time': str,
        'end time': str,
        'model run id': str,
        'model run template id': str,
        'model run description': str,
        'input id': str,
        'input name': str,
        'output id': str,
        'output name': str,
    }
)


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

    dataset_record_map = {ds.dataset_id: ds_id_to_record(
        ds.dataset_id) for ds in record.inputs + record.outputs}

    input_ids = [dataset_record_map[ds.dataset_id].id
                 for ds in record.inputs]
    output_ids = [dataset_record_map[ds.dataset_id].id
                  for ds in record.outputs]
    input_names = [dataset_record_map[ds.dataset_id].display_name
                   for ds in record.inputs]
    output_names = [dataset_record_map[ds.dataset_id].display_name
                    for ds in record.outputs]

    return RowEntry(
        start_time=render_timestamp(record.start_time, timezone=timezone),
        end_time=render_timestamp(record.end_time, timezone=timezone),
        agent=render_creator(creator),
        agent_name=creator.display_name,
        agent_id=creator.id,
        organisation=render_organisation(organisation) if organisation else "",
        organisation_name=organisation.display_name if organisation else "",
        organisation_id=organisation.id if organisation else "",
        model_run_template_id=template.id,
        model_run_id=model_run_record.id,
        model_run_description=record.description or "",
        model_run_annotations=[(k, v)
                               for k, v in (record.annotations or {}).items()],
        model_combined=render_model_info(model=model, template=template),
        model_name=model.display_name,
        model_version=model_run_record.model_version or "",
        model_id=model.id,
        input_ids=input_ids,
        output_ids=output_ids,
        input_names=input_names,
        output_names=output_names,
    )


def row_entry_to_csv_row(entry: RowEntry) -> List[CSVRow]:
    # body rows
    rows: List[BaseRowDict] = []

    # process inputs/outputs
    input_ids = entry.input_ids
    output_ids = entry.output_ids
    input_names = entry.input_names
    output_names = entry.output_names

    # max length - always create at least one row
    max_length = max(max(len(input_ids), len(output_ids)), 1)

    # always create at least one row
    for index in range(max(max_length, 1)):
        # work out possible inputs/outputs
        possible_input_id = input_ids[index] if len(
            input_ids) > index else None
        possible_output_id = output_ids[index] if len(
            output_ids) > index else None
        possible_input_name = input_names[index] if len(
            input_names) > index else None
        possible_output_name = output_names[index] if len(
            output_names) > index else None

        # create entry
        row: BaseRowDict = {
            'agent': entry.agent,
            'agent name': entry.agent_name,
            'agent id': entry.agent_id,
            'organisation': entry.organisation,
            'organisation name': entry.organisation_name,
            'organisation id': entry.organisation_id,
            'model': entry.model_combined,
            'model name': entry.model_name,
            'model id': entry.model_id,
            'model version': entry.model_version,
            'start time': entry.start_time,
            'end time': entry.end_time,
            'model run id': entry.model_run_id,
            'model run template id': entry.model_run_template_id,
            'model run description': entry.model_run_description,
            'input id': possible_input_id or "",
            'output id': possible_output_id or "",
            'input name': possible_input_name or "",
            'output name': possible_output_name or "",
        }
        rows.append(row)

    # have to cast typed dict -> mapping here - keeps mypy happy
    all_rows = list(map(lambda x: cast(CSVRow, x), rows))

    # convert typed base dict to regular dictionary
    all_rows = list(
        map(lambda entry: {k: v for k, v in entry.items()}, all_rows))

    # now add annotation columns
    for current_row in all_rows:
        for k, v in (entry.model_run_annotations or []):
            current_row[k] = v

    return all_rows


def generator(runs: ModelRunsType, endpoint_context: EndpointContext, timezone: Timezone) -> CSVType:
    rows: List[RowEntry] = list(
        map(lambda run: create_row_entry_from_record(
            model_run_record=run,
            endpoint_context=endpoint_context,
            timezone=timezone
        ), runs))

    # this contains a set of rows with possibly variable headers - normalise dictionaries
    base_rows_list: List[CSVRow] = list(
        itertools.chain.from_iterable(map(row_entry_to_csv_row, rows)))

    # create set of headers
    header_set: Set[str] = set()
    for r in base_rows_list:
        keys = r.keys()
        header_set.update(keys)

    # now update all entries
    for r in base_rows_list:
        for key in header_set:
            if key not in r:
                r[key] = ""

    # and return
    return base_rows_list
