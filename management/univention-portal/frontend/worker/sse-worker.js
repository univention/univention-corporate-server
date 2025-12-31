/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

var eventSource = (function () {
  let instance;
  function createEventSource() {
    const eventSource = new EventSource('/univention/logout-sse');
    return eventSource;
  }

  return {
    getEventSource: function() {
      if (!instance) {
        instance = createEventSource();
      }

      return instance;
    }
  }
})();

onconnect = (e) => {
  const port = e.ports[0];
  const eventSourceInstance = eventSource.getEventSource()

  eventSourceInstance.addEventListener('message', (event) => {
    if (event.data === 'logout') {
      port.postMessage('logout')
    }
  });
}
