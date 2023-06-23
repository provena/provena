import json
from SharedInterfaces.RegistryAPI import *
from typing import Dict, Any
from KeycloakRestUtilities.TokenManager import Stage
import typer
from rich import print
from helpers.migrations.f1249_migration import f1249_migrator_function
from helpers.migrations.f1176_migration import f1176_migrator_function
from helpers.migrations.s3_bucket import update_s3_location
from helpers.migrations.external_access import external_access
from helpers.migrations.item_history import add_starting_history
from helpers.migrations.example_migration import example_migration as example_migration_func

app = typer.Typer(pretty_exceptions_show_locals=False)


def read_input(file: typer.FileText) -> List[Dict[str, Any]]:
    return json.loads(file.read())


def write_output(file: typer.FileTextWrite, content: List[Dict[str, Any]]) -> None:
    file.write(json.dumps(content, indent=2))
    file.close()


def remove_subtypes(items: List[Dict[str, Any]], subtypes: List[ItemSubType | str]) -> List[Dict[str, Any]]:
    count = len(items)
    filtered_items = list(filter(lambda item: not (
        item.get('item_subtype') in subtypes), items))
    removed = count - len(filtered_items)
    print(f"Removed {removed} items.")
    return filtered_items


def remove_categories(items: List[Dict[str, Any]], categories: List[ItemCategory | str]) -> List[Dict[str, Any]]:
    count = len(items)
    filtered_items = list(filter(lambda item: not (
        item.get('item_category') in categories), items))
    removed = count - len(filtered_items)
    print(f"Removed {removed} items.")
    return filtered_items


def auto_item_filter(item: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    category = item.get('item_category')
    subtype = item.get('item_subtype')

    # check cat/subtype exists
    if category is None or subtype is None:
        return False, "Category or subtype missing"

    # check it is valid
    try:
        parsed_category = ItemCategory(category)
    except Exception as e:
        return False, f"Couldn't parse {category = } as valid item category."

    try:
        parsed_subtype = ItemSubType(subtype)
    except Exception as e:
        return False, f"Couldn't parse {subtype = } as valid item subtype."

    # now get the model type from the category/subtype
    model_type: Optional[Type[ItemBase]] = MODEL_TYPE_MAP.get(
        (parsed_category, parsed_subtype))

    if model_type is None:
        return False, f"Category/Subtype combination {parsed_category}/{parsed_subtype} was invalid."

    # check if parsable as seed item or full item
    try:
        parsed_seed_item = SeededItem.parse_obj(item)
    except Exception as e:
        return False, f"Seed model validation failed, error: {e}"

    # now see if the model can be parsed as it's proper type
    try:
        model_type.parse_obj(item)
    except Exception as e:
        return False, f"Complete model validation failed with error: {e}"

    # everything seems good
    return True, None


@ app.command()
def auto_filter(
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
    report_file: typer.FileTextWrite = typer.Argument(
        ..., help="Writes a change report to the specified location."),
) -> None:
    """
    Tries to remove all invalid entries against currently installed shared interfaces. 
    """

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    # auto filter items
    success_and_messages = [auto_item_filter(
        item['item_payload']) for item in input_content]

    output_content: List[Dict[str, Any]] = []
    report_content: List[Dict[str, Any]] = []

    for item, good_err in zip(input_content, success_and_messages):
        good, err = good_err
        if good:
            output_content.append(item)
        else:
            report_content.append(
                {'item': item, 'err': err}
            )

    if len(report_content) == 0:
        print(f"No changes - writing unchanged output. No report file written")
    else:
        print(
            f"There were {len(report_content)} issues out of {len(input_content)} provided items.")
        # write output content
        print(f"Writing report to report file {report_file.name}.")
        write_output(file=report_file, content=report_content)

    # write output content
    print(f"Writing output to output file {output_file.name}.")
    write_output(
        file=output_file,
        content=output_content
    )


@ app.command()
def filter_items(
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
    remove_subtype: List[ItemSubType] = typer.Option(
        [],
        help="Provide a list of ItemSubType(s) which should be removed from the output"
    ),
    remove_category: List[ItemCategory] = typer.Option(
        [],
        help="Provide a list of ItemCategory(s) which should be removed from the output"
    ),
    remove_invalid_subtype: List[str] = typer.Option(
        [],
        help="Provide a list of ItemSubType(s) which should be removed from the output. " +
        "This may be an invalid string."
    ),
    remove_invalid_category: List[str] = typer.Option(
        [],
        help="Provide a list of ItemCategory(s) which should be removed from the output. " +
        "This may be an invalid string."
    )
) -> None:

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    all_subtypes = remove_subtype + remove_invalid_subtype
    if len(all_subtypes) > 0:
        print(f"Removing subtypes: {all_subtypes}")
        input_content = remove_subtypes(input_content, all_subtypes)

    all_categories = remove_category + remove_invalid_category
    if len(all_categories) > 0:
        print(f"Removing categories: {all_categories}")
        input_content = remove_categories(input_content, all_categories)

    # write output content
    print(f"Writing output to output file {output_file.name}.")
    write_output(
        file=output_file,
        content=input_content
    )


@ app.command()
def update_bucket_name(
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
    old_bucket_name: str = typer.Argument(
        ..., help=f"The name of the current S3 bucket"
    ),
    new_bucket_name: str = typer.Argument(
        ..., help=f"The name of the new S3 bucket"
    ),
) -> None:

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    # modify the items
    input_content = [update_s3_location(
        old_item=item, old_bucket_name=old_bucket_name, new_bucket_name=new_bucket_name) for item in input_content]

    write_output(
        file=output_file,
        content=input_content
    )


@ app.command()
def add_access_info(
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
) -> None:

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    # modify the items
    input_content = [external_access(
        old_item=item) for item in input_content]

    write_output(
        file=output_file,
        content=input_content
    )


@ app.command()
def history_migration(
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
) -> None:

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    # modify the items
    input_content = [add_starting_history(
        old_item=item) for item in input_content]

    write_output(
        file=output_file,
        content=input_content
    )


@ app.command()
def f1249_migration(
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
) -> None:
    """
    Adds the ethics/consent fields to person and dataset.
    Also adds the indigenous knowledge and export controls to datasets.
    """

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    # modify the items
    input_content = [f1249_migrator_function(
        old_item=item) for item in input_content]

    print(f"Writing output to specified output file {output_file.name}.")
    write_output(
        file=output_file,
        content=input_content
    )


@ app.command()
def example_migration(
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
) -> None:

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    # modify the items
    input_content = [example_migration_func(
        old_item=item) for item in input_content]

    write_output(
        file=output_file,
        content=input_content
    )


@ app.command()
def f1249_f1247_migration(
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
) -> None:
    """
    Adds the ethics/consent fields to person and dataset.
    Also adds the indigenous knowledge and export controls to datasets.
    """

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    # modify the items (f1249)
    input_content = [f1249_migrator_function(
        old_item=item, parse=False) for item in input_content]

    # modify the items (f1247)
    input_content = [add_starting_history(
        old_item=item) for item in input_content]

    print(f"Writing output to specified output file {output_file.name}.")
    write_output(
        file=output_file,
        content=input_content
    )


@ app.command()
def f1176_migration(
    stage: Stage = typer.Argument(
        # "..."" to specify required option.
        ...,
        help=f"The Stage to migrate registry items on. This is not used for any endpoints - just as a check.",
    ),
    input_file: typer.FileText = typer.Argument(
        ..., help="The location of the dump file to process as input. Include file extension."),
    output_file: typer.FileTextWrite = typer.Argument(
        ..., help="The location to write the output file to. Include file extension."),
) -> None:
    """
    Adds the owner_username field + 
    References the publisher and author organisations from data store records -> Person 
    Needs to know the stage to help with determining the IDs of the organisations in data store records
    """

    # input content
    print(f"Reading input from specified input file {input_file.name}.")
    input_content = read_input(input_file)

    # modify the items (f1176)
    input_content = [f1176_migrator_function(
        stage=stage, old_item=item, parse=True) for item in input_content]

    print(f"Writing output to specified output file {output_file.name}.")
    write_output(
        file=output_file,
        content=input_content
    )
