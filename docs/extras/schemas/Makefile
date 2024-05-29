%.schema.json: ../../../chatidea/config/%.py
	poetry run python3 -c "import sys; sys.path.append('../../..');"\
	"from pydantic import schema_json_of; import json;"\
	"from chatidea import config;"\
	"vars = (x for x in vars(config) if not x.startswith('_'));"\
	"assoc = dict(zip(vars, vars));"\
	"print(json.dumps(getattr(config, assoc['$*']).model_json_schema(),indent=4))" > $@

all: concept.schema.json schema.schema.json view.schema.json extras.schema.json
