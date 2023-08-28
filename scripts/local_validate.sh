#!/bin/bash -e 

# Run the export interfaces
echo "Running interface export"
echo
./scripts/interface_management/export_interfaces.sh
echo "Done"
echo

# Check typescript tsc
echo "Running typescript checks"
echo
./scripts/testing/typescript_type_checks.sh
echo "Done"
echo

# Mypy type checks
echo "Running mypy checks"
echo
./scripts/testing/mypy_type_checks.sh
echo "Done"
echo
