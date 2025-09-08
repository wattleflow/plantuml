# Wattlelfow Workflow Tools - plantuml.py

The tool reads a `source` file, parse it and prints PlantUML text to stdout.

Currently supports: 
- `sql` - sql script
- `py` - python code

## Usage
```bash
python -m tools.plamtuml <path/to/file.sql> [--log-level NOTSET|INFO|DEBUG|WARNING|ERROR]
```
## Examples
- outputs PlantUML code in `stdout`
- using `--log-level` DEBUG message

```bash
python plantuml.py tools/doc/test.sql --log-level DEBUG
python plantuml.py tools/plantuml.py --log-level DEBUG
```
**Stores `stdout` to `.puml` file and render svg with PlantUML**

```bash
# redirect stdout to schema.puml
python -m tools.plamtuml schema.sql > schema.puml

# generates .png/.svg
plantuml schema.puml
```

## Prerequisites
Install with **conda**
- `plantuml`
- `graphviz` 
- `nodejs`

```bash
conda install -c conda-forge openjdk=17 graphviz plantuml nodejs
```

## Install plantuml `VSCode extension` with conda
```bash
code --install-extension plantuml-1.0.0.vsix

# or localy if you built your own version
code --install-extension ~/plugin/vscode-plantuml/plantuml-1.0.0.vsix
```

## Setting PlantUML in VSCode
```bash
code --install-extension plantuml-1.0.0.vsix

#  ili 
code --install-extension ~/projects/plugins/vscode-plantuml/plantuml-1.0.0.vsix
```

**Must add following to**: `.vscode/setting.json` in your project

```json
    "plantuml.exportFormat": "png",
    "plantuml.render": "Local",
    "plantuml.java": "/home/username/miniconda3/envs/plantuml/bin/java",
    "plantuml.jar": "/home/username/miniconda3/envs/plantuml/lib/plantuml.jar",
    "plantuml.commandArgs": []
```
