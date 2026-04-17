function getTypeFromHTMLInput(form, fieldName) {
  const field = form.elements[fieldName];
  if (field) {
    return field.type;
  }
  return null;
}
const typeMappings = {
  text: (value) => value.toString(),
  number: (value) => Number(value),
  date: (value) => new Date(value),
  datetime: (value) => new Date(value),
  email: (value) => value.toString(),
  password: (value) => value.toString(),
  tel: (value) => value.toString(),
  url: (value) => value.toString(),
  checkbox: (value) => value === 'true' || value === 'on',
  radio: (value) => value.toString(),
  range: (value) => Number(value),
};

function convertValues(data, form) {
  const convertedData = {};

  for (const key in data) {
    const value = data[key];
    const type = getTypeFromHTMLInput(form, key);

    if (type && typeMappings[type]) {
      convertedData[key] = typeMappings[type](value);
    } else {
      convertedData[key] = value;
    }
  }

  return convertedData;
}

function transformKeys(obj) {
  const transformed = {};

  for (const key in obj) {
    const parts = key.split('.');
    let current = transformed;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];

      if (part.includes('[')) {
        const [prop, value] = part.split('[');
        const cleanValue = value.replace(']', '');
        current[prop] = current[prop] || {};
        current = current[prop];
        if (current[cleanValue] === undefined) {
            current[cleanValue] = [];
        }
        current[cleanValue].push(obj[key]);
      } else {
        if (!current[part]) {
          current[part] = {};
        }
        if (i === parts.length - 1) {
          current[part] = obj[key];
        }
        current = current[part];
      }
    }
  }

  return transformed;
}


htmx.defineExtension('json-enc', {
    onEvent: function (name, evt) {
        if (name === "htmx:configRequest") {
            evt.detail.headers['Content-Type'] = "application/json";
        }
    },

    encodeParameters : function(xhr, parameters, elt) {
        xhr.overrideMimeType('text/json');

        return (JSON.stringify(transformKeys(convertValues(parameters, elt))));
    }
});
