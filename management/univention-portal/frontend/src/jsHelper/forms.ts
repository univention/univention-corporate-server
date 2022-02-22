/*
 * Copyright 2021 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */

// TODO move functionality into individual widgets (?)

import _ from '@/jsHelper/translate';

type WidgetType = 'TextBox' | 'PasswordBox' | 'DateBox' | 'ComboBox' | 'RadioBox' | 'ImageUploader' | 'LocaleInput' | 'CheckBox' | 'MultiInput' | 'LinkWidget' | 'MultiSelect';

interface OptionsDefinition {
  id: string,
  label: string,
}

type Validator = (widget, value) => string;

export interface WidgetDefinition {
  type: WidgetType,
  name: string,
  label: string,
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
}

export function isEmpty(widget, value): boolean {
  switch (widget.type) {
    case 'TextBox':
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
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
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
    case 'LocaleInput':
    case 'CheckBox':
    case 'MultiSelect':
    case 'LinkWidget':
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

export function validate(widget, value): void {
  function required(_widget, _value) {
    switch (_widget.type) {
      case 'TextBox':
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
        return _widget.required && isEmpty(_widget, _value) ? _('This value is required') : '';
      default:
        return '';
    }
  }

  function getFirstInvalidMessage(_widget, _value) {
    const validators = [required, ...(_widget.validators ?? [])];
    let message = '';
    validators.some((validator) => {
      const iMessage = validator(_widget, _value);
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
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
    case 'LocaleInput':
    case 'CheckBox':
    case 'MultiSelect':
    case 'LinkWidget':
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
    validate(widget, values[widget.name]);
  });
  return allValid(widgets);
}

export function initialValue(widget, value): any {
  switch (widget.type) {
    case 'TextBox':
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
      return typeof value === 'string' ? value : '';
    case 'LocaleInput':
      // TODO typecheck of value
      return value ?? { en_US: '' };
    case 'CheckBox':
      return typeof value === 'boolean' ? value : false;
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
    case 'DateBox':
    case 'ComboBox':
    case 'PasswordBox':
    case 'RadioBox':
    case 'ImageUploader':
    case 'LocaleInput':
    case 'CheckBox':
    case 'MultiSelect':
    case 'LinkWidget':
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
