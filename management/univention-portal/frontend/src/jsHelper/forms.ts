/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// TODO move functionality into individual widgets (?)

import _ from '@/jsHelper/translate';

type WidgetType = 'ComplexInput' | 'TextBox' | 'TextArea' | 'PasswordBox' | 'DateBox' | 'ComboBox' | 'RadioBox' | 'ImageUploader' | 'LocaleInput' | 'CheckBox' | 'MultiInput' | 'LinkWidget' | 'MultiSelect' | 'NumberSpinner' | 'TimeBox';

interface OptionsDefinition {
  id: string,
  label: string,
}

type Validator = (widget, value, widgets, values) => string;

export interface WidgetDefinition {
  type: WidgetType,
  name: string,
  label: string,
  extraLabel?: string,
  ariaLabel?: string,
  invalidMessage?: string | { all: string, values: string[] },
  required?: boolean,
  readonly?: boolean,
  options?: OptionsDefinition[],
  validators?: Validator[],
  index?: number,
  subtypes?: WidgetDefinition[],
  tabindex?: number,
  disabled?: boolean,
  canShowPassword?: boolean,
  description?: string,
  [attribute: string]: any, // for native HTML attributes
}

export interface WidgetTimeBox extends WidgetDefinition {
  step: number,
}

export function isEmpty(widget, value): boolean {
  switch (widget.type) {
    case 'TextBox':
    case 'TextArea':
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
    case 'NumberSpinner':
    case 'TimeBox':
      return value === '';
    case 'MultiInput':
      return value.every((row) => {
        if (Array.isArray(row)) {
          return row.every((rowValue, idx) => isEmpty(widget.subtypes[idx], rowValue));
        }
        return isEmpty(widget.subtypes[0], row);
      });
    case 'LocaleInput':
      return value.en_US === '' || value.en_US === undefined;
    case 'MultiSelect':
    case 'LinkWidget':
      // TODO check for empty row(s)?
      return value.length === 0;
    case 'CheckBox':
      return !value;
    default:
      return false;
  }
}

export function isValid(widget): boolean {
  if (widget.invalidMessage === undefined) {
    return true;
  }
  switch (widget.type) {
    case 'TextBox':
    case 'TextArea':
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
    case 'LocaleInput':
    case 'CheckBox':
    case 'MultiSelect':
    case 'LinkWidget':
    case 'NumberSpinner':
    case 'TimeBox':
      return widget.invalidMessage === '';
    case 'MultiInput':
      return widget.invalidMessage.all === '' &&
        widget.invalidMessage.values.every((message) => {
          if (Array.isArray(message)) {
            return message.every((_message, idx) => isValid({
              type: widget.subtypes[idx].type,
              invalidMessage: _message,
            }));
          }
          return isValid({
            type: widget.subtypes[0].type,
            invalidMessage: message,
          });
        });
    default:
      return true;
  }
}

export function allValid(widgets): boolean {
  return widgets.every((widget) => isValid(widget));
}

export function validate(widget, value, widgets, values): void {
  function required(_widget, _value) {
    switch (_widget.type) {
      case 'TextBox':
      case 'TextArea':
      case 'DateBox':
      case 'ComboBox':
      case 'PasswordBox':
      case 'MultiInput':
      case 'RadioBox':
      case 'ImageUploader':
      case 'LocaleInput':
      case 'MultiSelect':
      case 'LinkWidget':
      case 'CheckBox':
      case 'NumberSpinner':
      case 'TimeBox':
        return _widget.required && isEmpty(_widget, _value) ? _('This value is required') : '';
      default:
        return '';
    }
  }

  function getFirstInvalidMessage(_widget, _value) {
    const validators = [required, ...(_widget.validators ?? [])];
    let message = '';
    validators.some((validator) => {
      const iMessage = validator(_widget, _value, widgets, values);
      if ((iMessage ?? '') !== '') {
        message = iMessage;
        return true;
      }
      return false;
    });
    return message;
  }

  switch (widget.type) {
    case 'TextBox':
    case 'TextArea':
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
    case 'LocaleInput':
    case 'CheckBox':
    case 'MultiSelect':
    case 'LinkWidget':
    case 'TimeBox':
    case 'NumberSpinner':
      widget.invalidMessage = getFirstInvalidMessage(widget, value);
      break;
    case 'MultiInput':
      widget.invalidMessage = {
        all: getFirstInvalidMessage(widget, value),
        values: value.map((row) => {
          if (Array.isArray(row)) {
            return row.map((vv, idx) => getFirstInvalidMessage(widget.subtypes[idx], vv));
          }
          return getFirstInvalidMessage(widget.subtypes[0], row);
        }),
      };
      break;
    default:
      break;
  }
}

export function validateAll(widgets, values): boolean {
  widgets.forEach((widget) => {
    validate(widget, values[widget.name], widgets, values);
  });
  return allValid(widgets);
}

export function initialValue(widget, value): any {
  switch (widget.type) {
    case 'TextBox':
    case 'TextArea':
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
    case 'TimeBox':
      return typeof value === 'string' ? value : '';
    case 'LocaleInput':
      // TODO typecheck of value
      return value ?? { en_US: '' };
    case 'CheckBox':
      return typeof value === 'boolean' ? value : false;
    case 'NumberSpinner':
      return typeof value === 'number' ? value : false;
    case 'MultiInput':
      if (!Array.isArray(value)) {
        const row = widget.subtypes.map((subtype) => initialValue(subtype, null));
        if (row.length === 1) {
          return row;
        }
        return [row];
      }
      return value.map((v) => {
        if (Array.isArray(v)) {
          return v.map((vv, idx) => initialValue(widget.subtypes[idx], vv));
        }
        return initialValue(widget.subtypes[0], v);
      });
    // case 'MultiSelect':
    //  return TODO
    // case 'LinkWidget':
    //  return TODO
    default:
      return value;
  }
}

export function invalidMessage(widget): string {
  if (widget.invalidMessage === undefined) {
    return '';
  }
  switch (widget.type) {
    case 'TextBox':
    case 'TextArea':
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
    case 'LocaleInput':
    case 'CheckBox':
    case 'MultiSelect':
    case 'NumberSpinner':
    case 'LinkWidget':
    case 'TimeBox':
      return widget.invalidMessage;
    case 'MultiInput':
      return widget.invalidMessage.all;
    default:
      return '';
  }
}

export function validateInternalName(_widget: any, value: string): string {
  const regex = new RegExp('(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)');
  if (!regex.test(value)) {
    return _('Internal name must not contain anything other than digits, letters or dots, must be at least 2 characters long, and start and end with a digit or letter!');
  }
  return '';
}
