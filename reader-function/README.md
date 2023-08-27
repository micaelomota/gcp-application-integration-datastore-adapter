# How to use this Cloud Function Task

This Cloud Function is supposed to be used by a [Application Integration](https://cloud.google.com/application-integration) task.

## Task Parameters

| Task parameter | Type    | Required | Description                                                                                |
| -------------- | ------- | -------- | ------------------------------------------------------------------------------------------ |
| `query_kind`   | string  | yes      | The Datastore Kind to be queried                                                           |
| `query_limit`  | integer | yes      | The Datastore limit                                                                        |
| `query_filter` | string  | yes      | A list of filters separated by `;`. Check details in the next section                      |
| `result_key`   | string  | yes      | The event parameter key to inject results. We do `event.setParameter(result_key, results)` |

## Filtering

A query filter is a string in the following format `field,operator,value,type`.
You can defined multiple filters by separating it with a comma, e.g `age,>,18,integer;team,=,Barcelona,string`.

### We support all datastore types:

| type    | Description                                          |
| ------- | ---------------------------------------------------- |
| string  | Casts the value to a string.                         |
| integer | Casts the value to an integer.                       |
| double  | Casts the value to a double (floating-point number). |
| boolean | Casts the value to a boolean.                        |
| key     | Assumes the value is a valid key type.               |
| null    | Returns None to represent null/empty.                |
