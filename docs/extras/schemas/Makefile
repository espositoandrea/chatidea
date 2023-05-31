%.schema.json: ../../../chatidea/config/%.py
	poetry run python3 -c "import sys; sys.path.append('../../..');"\
	"from pydantic import schema_json_of;"\
	"from chatidea import config;"\
	"vars = (x for x in vars(config) if not x.startswith('_'));"\
	"assoc = dict(zip(vars, vars));"\
	"print(getattr(config, assoc['$*']).schema_json(indent=4))" > $@

all: concept.schema.json schema.schema.json view.schema.json
