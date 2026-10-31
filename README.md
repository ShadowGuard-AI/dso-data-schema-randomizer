![Banner](banner.png)

# dso-data-schema-randomizer
Generates random, but structurally valid, schema for various data formats (JSON, XML, CSV) to replace real schemas with realistic, anonymized ones. Focuses on maintaining data integrity for downstream processing without revealing sensitive information. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats

## Install
`git clone https://github.com/ShadowGuardAI/dso-data-schema-randomizer`

## Usage
`./dso-data-schema-randomizer [params]`

## Parameters
- `-h`: Show help message and exit
- `-o`: No description provided
- `-l`: No description provided

## Behavior
- An output path that resolves to the input file is refused at exit 1, however it is spelled.
- Empty input (an empty CSV, an empty JSON object or list) exits non-zero with no success line and writes no output.
- In XML, each distinct original tag gets one replacement tag, reused at every occurrence, so the structure stays valid.
- Randomized CSV header names are redrawn on collision, so output header names stay unique.

## License
Copyright (c) ShadowGuardAI
