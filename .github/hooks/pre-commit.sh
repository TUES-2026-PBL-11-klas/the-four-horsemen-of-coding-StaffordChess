#!/bin/bash

echo "test"
if ! command -v gitleaks &> /dev/null; then
    echo "Error: gitleaks is not installed. Run 'sudo dnf install gitleaks'."
    exit 1
fi
echo "test1"

gitleaks protect --staged --verbose
echo "test2"
if [ $? -ne 0 ]; then
    echo "---"
    echo "hard coded stuff"
    echo "---"
    exit 1
fi

exit 0