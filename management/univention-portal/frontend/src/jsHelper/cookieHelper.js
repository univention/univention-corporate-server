const setCookie = (name, value) => {
  const date = new Date();

  let cookieValue = escape(new Date(date.setFullYear(date.getFullYear())).toUTCString());
  let expiryDate = new Date(date.setFullYear(date.getFullYear() + 1)).toUTCString();

  if (name === '') {
    console.error('setCookie: Missing name! Aborted!');
    return false;
  }

  if (value === '') {
    cookieValue = '';
    expiryDate = -1;
  }

  // set cookie
  document.cookie = `${name}=${cookieValue};expires=${expiryDate}; path=/`;

  return false;
};

const getCookie = (name) => {
  const nameEQ = `${name}=`;
  const ca = document.cookie.split(';');
  let ret = '';

  for (let i = 0; i < ca.length; i += 1) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) {
      ret = c.substring(nameEQ.length, c.length);
    }
  }

  return ret;
};

const deleteCookie = (name) => {
  setCookie(name, '', -1);
};

export {
  setCookie,
  getCookie,
  deleteCookie,
};
