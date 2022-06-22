/*
 * Copyright 2022 Univention GmbH
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

import { WidgetDefinition } from '@/jsHelper/forms';

interface BackendWidgetDefinition {
  // multivalue: boolean, not used atm
  // size: string, not used atm
  // syntax: string, not used atm
  editable: boolean,
  readonly: boolean,
  type: string,
  syntax: string,
  id: string,
  label: string,
  required: boolean,
  staticValues?: any[],
  subtypes?: BackendWidgetDefinition[],
  description: string,
}

export function sanitizeBackendWidget(widget: BackendWidgetDefinition): WidgetDefinition {
  const w: any = {
    // TODO unhandled fields that come from command/passwordreset/get_user_attributes_descriptions
    // multivalue: false
    // size: "TwoThirds"
    // syntax: "TwoThirdsString"
    type: widget.type,
    name: widget.id ?? '',
    label: widget.label ?? '',
    required: widget.required ?? false,
    readonly: !(widget.editable ?? true) || (widget.readonly ?? false),
    description: widget.description,
  };
  if (widget.type === 'ImageUploader') {
    w.extraLabel = w.label;
  }
  if (widget.type === 'ComboBox') {
    w.options = widget.staticValues;
  }
  if (widget.type === 'MultiInput') {
    w.extraLabel = w.label;
    w.subtypes = widget.subtypes?.map((subtype) => sanitizeBackendWidget(subtype));
  }

  // syntax specific adjustments
  if (widget.syntax === 'jpegPhoto') {
    // it says the syntax is 'jpegPhoto' but pngs will be converted in the backend so they can still be uploaded
    w.accept = 'image/png,image/jpeg';
  }
  return w;
}

interface ValidationObject {
  isValid: boolean | boolean[],
  message: string | string[],
}

interface ValidationData {
  [key: string]: ValidationObject,
}

export function setBackendInvalidMessage(widgets: WidgetDefinition[], invalidData: ValidationData): void {
  widgets.forEach((widget) => {
    const validationObj = invalidData[widget.name];
    if (validationObj !== undefined) {
      switch (widget.type) {
        case 'MultiInput':
          // TODO test if non array can come from backend
          if (Array.isArray(validationObj.message)) {
            widget.invalidMessage = {
              all: '',
              values: validationObj.message,
            };
          } else {
            widget.invalidMessage = {
              all: validationObj.message,
              values: [],
            };
          }
          break;
        default:
          widget.invalidMessage = validationObj.message as string;
          break;
      }
    }
  });
}

function getWidget(name: string, widgets: WidgetDefinition[]) {
  return widgets.find((_w) => _w.name === name);
}

export function sanitizeFrontendValues(values: Record<string, unknown>, widgets: WidgetDefinition[]) {
  const sanitized: Record<string, unknown> = JSON.parse(JSON.stringify(values));
  widgets.forEach((widget) => {
    const value = sanitized[widget.name];
    if (widget.type === 'ImageUploader') {
      if (typeof value === 'string' && value.startsWith('data:')) {
        const data = value.split(',')[1];
        if (data) {
          sanitized[widget.name] = data;
        } else {
          delete sanitized[widget.name];
        }
      } else {
        delete sanitized[widget.name];
      }
    }
    if (widget.type === 'MultiInput') {
      if (Array.isArray(value)) {
        sanitized[widget.name] = value.reduce((arr, arrValue) => {
          if (Array.isArray(arrValue)) {
            if (arrValue.some((v) => !!v)) {
              arr.push(arrValue);
            }
          } else if (arrValue) {
            arr.push(arrValue);
          }
          return arr;
        }, []);
      }
    }
  });
  return sanitized;
}

// copy pasted from ucs/management/univention-web/js/widgets/Image.js
function getImageType(base64String: string): string {
  // check the signature of the first bytes...
  // for jpeg it is (in hex): hex pattern: FF D8 FF
  if (base64String.indexOf('/9j/4') === 0) {
    return 'jpeg';
  }
  // the first 8 bytes (in hex) should be matched: 89 50 4E 47 0D 0A 1A 0A
  // note that base64 encodes 6 bits per character...
  if (base64String.indexOf('iVBORw0KGg') === 0) {
    return 'png';
  }
  if (base64String.indexOf('R0lGODdh') === 0 || base64String.indexOf('R0lGODlh') === 0) {
    return 'gif';
  }
  // check whether file starts with '<svg', '<SVG', '<xml', or '<XML'...
  // as simple check that should work for most cases
  if (base64String.indexOf('PHN2Z') === 0 || base64String.indexOf('PFNWR') === 0 || base64String.indexOf('PFhNT') || base64String.indexOf('PHhtb')) {
    return 'svg+xml';
  }
  return 'unknown';
}

export function sanitizeBackendValues(values: Record<string, unknown>, widgets: WidgetDefinition[]) {
  const sanitized: Record<string, unknown> = JSON.parse(JSON.stringify(values));
  widgets.forEach((widget) => {
    if (widget.type === 'ImageUploader') {
      const value = sanitized[widget.name];
      if (typeof value === 'string' && !value.startsWith('data:')) {
        sanitized[widget.name] = `data:image/${getImageType(value)};base64,${value}`;
      }
    }
  });
  return sanitized;
}
