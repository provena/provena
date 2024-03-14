import json
import typing

# TODO need to update these depending on input/output
input_filename = "dumps/TODO"
output_filename = "dumps/TODO"


def read() -> typing.List[typing.Dict[str, typing.Any]]:
    with open(input_filename, 'r') as f:
        return json.loads(f.read())


def write(entries: typing.List[typing.Dict[str, typing.Any]]) -> None:
    with open(output_filename, 'w') as f:
        f.write(json.dumps(entries))


def entry_filter(entry: typing.Dict[str, typing.Any]) -> bool:
    # Can modify this to filter on whatever is useful - in this case username
    return True


if __name__ == "__main__":
    entries = read()
    filtered_entries = list(filter(entry_filter, entries))
    write(filtered_entries)
