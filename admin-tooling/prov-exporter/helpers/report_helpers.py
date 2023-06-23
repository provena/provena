from enum import Enum
from typing import Dict, Optional
import typer
import csv
from helpers.generator_types import *

# import generators here
from helpers.generators.basic_report import generator as basic_report
from helpers.generators.detailed_report import generator as detailed_report

class ReportType(str, Enum):
    """
    ReportType: An enumeration of possible report types - should have an entry
    in the report generator map 
    """
    MODEL_RUN_LISTING = "MODEL_RUN_LISTING"
    DETAILED_LISTING = "DETAILED_LISTING"


REPORT_GENERATORS: Dict[ReportType, ReportGenerator] = {
    ReportType.MODEL_RUN_LISTING: basic_report,
    ReportType.DETAILED_LISTING: detailed_report,
}


def dispatch_report_generator(model_runs: ModelRunsType, report_type: ReportType, endpoint_context: EndpointContext, timezone: str) -> CSVType:
    """
    dispatch_report_generator 

    Determines the appropriate report function and generates csv report.

    Parameters
    ----------
    model_runs : ModelRunsType
        The list of model run records
    report_type : ReportType
        The report type to generate

    Returns
    -------
    CSVType
        Resulting csv 

    Raises
    ------
    ValueError
        If no generator defined
    """
    generator_func: Optional[ReportGenerator] = REPORT_GENERATORS.get(
        report_type)
    if generator_func is None:
        raise ValueError(
            f"There is no generator function for the report type: {report_type}")

    return generator_func(model_runs, endpoint_context, timezone)


def write_csv_report(csv_report: CSVType, output_file: typer.FileTextWrite) -> None:
    """
    write_csv_report 

    Writes a csv report -> output file using a dict writer.

    Parameters
    ----------
    csv_report : CSVType
        The csv to write
    output_file : typer.FileTextWrite
        The output file

    Raises
    ------
    ValueError
        If csv is empty
    """
    if len(csv_report) == 0:
        raise ValueError("Can't generate an empty CSV report. Aborting.")

    headers = list(csv_report[0].keys())
    dict_writer = csv.DictWriter(output_file, fieldnames=headers)
    dict_writer.writeheader()
    dict_writer.writerows(csv_report)

    output_file.close()
