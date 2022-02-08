from marshmallow import fields, INCLUDE, validate
from enter_app_name.app import mm
from enter_app_name.app.utils import MissingSchema


# Returns matched schema, else raise error
def schema_handler(schema_name: str):
    schema_map = {
        'update_rpa_form': UpdateRpaFormSchema,
    }
    if schema_name in schema_map:
        return schema_map[schema_name]()
    else:
        raise MissingSchema(f'Schema {schema_name} does not exist.')


class NestedSchema(ma.Schema):
    field1 = fields.String(required=True)
    field2 = fields.Integer()


class GenericSchema(mm.Schema):
    field3 = fields.String(validate=validate.OneOf(["f10w", "f10n"]))
    field4 = fields.Mapping(required=True)
    field5 = fields.List(fields.Nested(NestedSchema))
    field6 = fields.List(fields.Mapping())
    field7 = fields.Raw(required=True)


class CrudSchema(ma.Schema):
    crud_name = fields.String(required=True)
    crud_operation = fields.String(validate=validate.OneOf(["INSERT", "UPDATE", "DELETE"]))
    query_fields = fields.Mapping(allow_none=True)
    entries = fields.Raw(required=True)


class CrudCaseEntrySchema(ma.Schema):
    set_value = fields.Raw(required=True)
    case_condition = fields.Mapping(required=True)


class CrudUpdateCaseSchema(ma.Schema):
    set_column = fields.String(required=True)
    case_entries = fields.List(fields.Nested(CrudCaseEntrySchema))