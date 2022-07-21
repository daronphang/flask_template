from marshmallow import fields, INCLUDE, validate
from enter_app_name.app import mm
from enter_app_name.app.utils import MissingSchema


# Returns matched schema, else raise error
def get_schema(schema: str):
    schema_map = {
        'TESTING_SCHEMA': TestingSchema,
        'TASK': TaskSchema,
        'CELERY_STATUS': CeleryStatusSchema,
        'GET_DPN_DATA': DPNDataSchema
    }
    if schema in schema_map:
        return schema_map[schema]()
    raise MissingSchema(f'schema {schema} does not exist')


class NestedSchema(mm.Schema):
    field1 = fields.String(required=True)
    field2 = fields.Integer()


class GenericSchema(mm.Schema):
    field3 = fields.String(validate=validate.OneOf(["f10w", "f10n"]))
    field4 = fields.Mapping(required=True)
    field5 = fields.List(fields.Nested(NestedSchema))
    field6 = fields.List(fields.Mapping())
    field7 = fields.Raw(required=True)


class TestingSchema(mm.Schema):
    test_string = fields.String(required=True)


class UserInfoSchema(mm.Schema):
    username = fields.String(required=True)
    fab = fields.String(validate=validate.OneOf(["F10W", "F10N"]))


class TaskSchema(mm.Schema):
    userinfo = fields.Nested(UserInfoSchema, required=True)
    payload = fields.Mapping(required=True)


class CeleryStatusSchema(mm.Schema):
    task_id = fields.String(required=True)
    task_name = fields.String(required=True)


class DPNDataSchema(mm.Schema):
    equip_ids = fields.List(fields.String(required=True))
    start_date = fields.String(required=True)
    end_date = fields.String(required=True)
    loadport_entrance = fields.List(fields.String(required=True))
    loadport_exit = fields.List(fields.String(required=True))

# class CrudSchema(ma.Schema):
#     crud_name = fields.String(required=True)
#     crud_operation = fields.String(validate=validate.OneOf(["INSERT", "UPDATE", "DELETE"]))
#     query_fields = fields.Mapping(allow_none=True)
#     entries = fields.Raw(required=True)


# class CrudCaseEntrySchema(ma.Schema):
#     set_value = fields.Raw(required=True)
#     case_condition = fields.Mapping(required=True)


# class CrudUpdateCaseSchema(ma.Schema):
#     set_column = fields.String(required=True)
#     case_entries = fields.List(fields.Nested(CrudCaseEntrySchema))