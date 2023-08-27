"""Un-editable platform wrapper which invokes user code."""
import traceback

from flask import json
from flask import jsonify
from task import run

VALUE_NAME = [
    'stringValue', 'intValue', 'doubleValue', 'booleanValue', 'protoValue'
]
ARRAY_VALUE_NAME = {
    'stringArray': 'stringValues',
    'intArray': 'intValues',
    'doubleArray': 'doubleValues',
    'booleanArray': 'booleanValues',
    'protoArray': 'protoValues'
}
VALUE_TYPE_URL = 'type.googleapis.com/google.protobuf.Value'
CLOUD_FUNCTION_EXCEPTION_KEY = 'CloudFunctionException'
CLOUD_FUNCTION_LOGGING_KEY = 'CloudFunctionLogging'


class _Event(object):
  """Event object."""

  def __init__(self, json_payload):
    self._event_params = json_payload.get('eventParameters', dict())
    self._task_params = json_payload.get('taskParameters', dict())
    self._log = []
    print('Event param is ' + str(self._event_params))
    print('Task param is ' + str(self._task_params))

  def set(self, key, value):
    """Set the event parameters key-value.

    Args:
      key: parameter key.
      value: parameter value.
    """
    new_param = self._create_param(key, value)
    param = self._get_param_by_key(key)
    if param is None:
      if 'parameters' not in self._event_params:
        self._event_params['parameters'] = []
      self._event_params['parameters'].append(new_param)
    else:
      param['value'] = new_param['value']

  def _create_param(self, key, value):
    """Create a new parameter with given key value pair.

    Args:
      key: parameter key.
      value: parameter value.

    Returns:
      parameter.
    """
    new_param = {}
    new_param['key'] = key
    if isinstance(value, str):
      new_param['value'] = {'stringValue': value}
    elif isinstance(value, int):
      new_param['value'] = {'intValue': value}
    elif isinstance(value, float):
      new_param['value'] = {'doubleValue': value}
    elif isinstance(value, bool):
      new_param['value'] = {'booleanValue': value}
    elif isinstance(value, dict):
      if 'type@' in value:
        new_param['value'] = {'protoValue': value}
      else:
        new_param['value'] = {
            'protoValue': {
                '@type': 'type.googleapis.com/google.protobuf.Value',
                'value': value
            }
        }
    elif isinstance(value, list):
      if not value:
        raise RuntimeError('Cannot create a param with empty list')
      if any(not isinstance(val, type(value[0])) for val in value):
        print('Not all elements in the list have the same type')
        new_param['value'] = {
            'protoValue': {
                '@type': 'type.googleapis.com/google.protobuf.Value',
                'value': value
            }
        }
      elif isinstance(value[0], str):
        new_param['value'] = {'stringArray': {'stringValues': value}}
      elif isinstance(value[0], int):
        new_param['value'] = {'intArray': {'intValues': value}}
      elif isinstance(value[0], float):
        new_param['value'] = {'doubleArray': {'doubleValues': value}}
      elif isinstance(value[0], bool):
        new_param['value'] = {'booleanArray': {'booleanValues': value}}
      elif isinstance(value[0], dict):
        if all('@type' in val and val['@type'] == value[0]['@type']
               for val in value):
          new_param['value'] = {'protoArray': {'protoValues': value}}
        else:
          new_param['value'] = {
              'protoValue': {
                  '@type': 'type.googleapis.com/google.protobuf.Value',
                  'value': value
              }
          }
      else:
        raise RuntimeError('The type ' + str(type(value[0])) +
                           ' in the list is not supported')
    else:
      raise RuntimeError('Value ' + str(value) + ' has the type ' +
                         str(type(value)) + ' that is not supported')
    return new_param

  def get(self, key):
    """Get the event parameter value for specified key.

    Args:
      key: parameter key.

    Returns:
      Parameter value.
    """
    param = self._get_param_by_key(key)
    if param is None:
      raise RuntimeError('Can not find param with key ' + key)
    return self._get_param_value(param)

  def _get_param_by_key(self, key):
    """Get the parameter for specified key.

    Args:
      key: parameter key.

    Returns:
      Parameter.
    """
    param = self._get_param_by_key_from_params(key, self._task_params)
    if param is None:
      return self._get_param_by_key_from_params(key, self._event_params)
    value = self._get_param_value(param)
    if isinstance(value, str) and len(value) > 2 and value.startswith(
        '$') and value.endswith('$'):
      return self._get_param_by_key_from_params(value[1:-1], self._event_params)
    return param

  def _get_param_by_key_from_params(self, key, params):
    """Get the parameter for specified key from event parameters.

    Args:
      key: parameter key.
      params: event parameters.

    Returns:
      Parameter.
    """
    if not isinstance(params, dict) or 'parameters' not in params:
      return None
    for param in params['parameters']:
      if param['key'] == key:
        return param
    return None

  def _get_param_value(self, param):
    """Get the parameter value for specified parameter.

    Args:
      param: parameter.

    Returns:
      Parameter value.
    """
    value = param['value']
    if len(value) != 1:
      raise RuntimeError('param does not have size of 1')
    for value_name in VALUE_NAME:
      if value_name in value:
        if value_name == 'protoValue' and value[value_name][
            '@type'] == VALUE_TYPE_URL:
          return value[value_name]['value']
        return value[value_name]
    for array_value_name in ARRAY_VALUE_NAME:
      if array_value_name in value:
        return value[array_value_name][ARRAY_VALUE_NAME[array_value_name]]
    raise RuntimeError('Cannot get value from param ' + str(param))

  def set_error(self):
    """Set the cloud function error to event parameters in order for user to see on IP."""

    self.set(CLOUD_FUNCTION_EXCEPTION_KEY, traceback.format_exc())

  def log(self, message):
    self._log.append(str(message))

  def get_response(self):
    """Get the response that can be returned to IP.

    Returns:
      The response text or any set of values that can be turned into a
      Response object using
      `make_response
      <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    if self._log:
      self.set(CLOUD_FUNCTION_LOGGING_KEY, self._log)
    res = {
        'eventParameters': self._event_params,
    }
    return jsonify(**json.loads(json.htmlsafe_dumps(res)))


def execute_function(request):
  """Entry point of the cloud function.

  Args:
    request (flask.Request): HTTP request object.

  Returns:
    The response text or any set of values that can be turned into a
    Response object using
    `make_response
    <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
  """
  try:
    request_json = request.get_json(silent=True)
    event = _Event(request_json)
    run(event)
  except:
    event.set_error()
  return event.get_response()