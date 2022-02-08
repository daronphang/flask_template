## Payload Documentation

### Purpose

Serves to facilitate integration between services when making API calls to endpoints.

endpoint prefix /api/v1

### Heartbeat

methods: GET
endpoint: /heartbeat

### Query

methods: POST
endpoint: /query

For querying binary data, add 'pickle_helper' key in sql_utils.

### Crud Operations

methods: POST
endpoint /crud_v1

```json
{
  "userinfo": {
    "username": "",
    "fab": ""
  },
  "payload": {
    "crud_name": "",
    "crud_operation": "", // INSERT, UPDATE, DELETE
    "query_fields": "", // See query format below
    "entries": [
      {
        "keys": "to be added here" // see entries format below
      }
    ]
  }
}
```

#### Query Format

If query is not needed, can pass as null. Bare minimum need to provide 'AND' for sql_operator if passing single query.

```json
// query_fields format
{
    "[sql_operator]": {
        "[equality]": {
            "[fields]": ""
        }
    }
}

// Example

{
    "AND": {
        "=": {"id": 1, "name": "John"},
        ">": {"salary": 100}
    },
    "OR": {
        "=": {"id": 1, "name": "John"}
    },
    "BETWEEN": {
        "id": [1, 5]
    },
    "IN": {
        "id": [1, 5]
    }
}
```

#### Entries Format (INSERT/UPDATE)

Each entry MUST have the same column fields.

```json
// INSERT

{
  "entries": [
    {
      "col1": "john",
      "col2": 1000
    },
    {
      "col1": "annabelle",
      "col2": 500
    }
  ]
}

// UPDATE (without CASE WHEN)
{
    "entries": {
        "col1": "hello",
        "col2": "world"
    }
}

// UPDATE (CASE WHEN condition) - allows multiple COLUMNS and ROWS to be updated
{
    "entries": [
        {
            "set_column": "username",
            "case_entries": [
                {
                    "set_value": "john",
                    "case_condition": {
                        "AND": {
                            "=": {"id": "1095023", "username": "John"}
                        }
                    }
                },
                {
                    "set_value": "anna",
                    "case_condition": {
                        "AND": {
                            "=": {"id": "12345"}
                        }
                    }
                }
            ]
        },
        {
            "set_column": "area",
            "case_entries": [
                {
                    "set_value": "diffusion",
                    "case_condition": {
                        "AND": {
                            "=": {"id": "1095023", "username": "John"}
                        }
                    }
                },
                {
                    "set_value": "wet process",
                    "case_condition": {
                        "AND": {
                            "=": {"id": "12345"}
                        }
                    }
                }
            ]
        },
    ]
}
```
