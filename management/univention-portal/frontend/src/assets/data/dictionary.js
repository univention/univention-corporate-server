import { ref } from 'vue';

function _(msg) {
  return {
    original: msg,
    translated: ref(msg),
  };
}

const catalog = {
  NOTIFICATIONS: _('Notifications'),
  LOGIN: _('Login'),
  LOGOUT: _('Logout'),
  EDIT_PORTAL: _('Edit portal'),
  STOP_EDIT_PORTAL: _('Stop edit portal'),
  SWITCH_LOCALE: _('Switch locale'),
  COOKIE_SETTINGS: _('Cookie Settings'),
  COOKIE_DESCRIPTION: _('We use cookies in order to provide you with certain functions and to be able to guarantee an unrestricted service. By clicking on "Accept", you consent to the collection of information on this portal.'),
  ACCEPT: _('Accept'),
  SUBMIT: _('Submit'),
  DISMISS_NOTIFICATION: _('Dismiss notification'),
  LOGIN_REMINDER_DESCRIPTION: _('Login <a class="notification-bubble__link" href="#">here</a> so that you can use the full range of functions of UCS.'),
  ADD_CATEGORY: _('Add category'),
};

export { catalog };