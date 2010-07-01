/**
 * Javascript library for working with XmlHttpRequest objects and
 * Horde.
 *
 * $Horde: horde/js/src/httpclient.js,v 1.4.2.1 2007-12-20 15:01:30 jan Exp $
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

// Constructor for generic HTTP client.
function HTTPClient() {};

// Add methods and properties as array.
HTTPClient.prototype = {
    url: null,

    // Instance of XMLHttpRequest.
    request: null,

    // Used to make sure multiple calls are not placed with the same
    // client object while another in progress.
    callInProgress: false,

    // The user defined handler - see MyHandler below.
    userhandler: null,

    init: function(url)
    {
        this.url = url;

        try {
            // Mozilla, Safari.
            this.request = new XMLHttpRequest();
        } catch (e) {
            // IE.
            var MSXML_XMLHTTP_PROGIDS = [
                "MSXML2.XMLHTTP.4.0",
                "MSXML2.XMLHTTP.3.0",
                "MSXML2.XMLHTTP",
                "Microsoft.XMLHTTP"
                ];
            var success = false;
            for (var i = 0; i < MSXML_XMLHTTP_PROGIDS.length && !success; i++) {
                try {
                    this.request = new ActiveXObject(MSXML_XMLHTTP_PROGIDS[i]);
                    success = true;
                } catch (e) {}
            }
            if (!success) {
                throw "Unable to create XMLHttpRequest.";
            }
        }
    },

    // Handler argument is a user defined object to be called.
    asyncGET: function(handler)
    {
        // Degrade or some such.
        if (!this.request) {
            return false;
        };

        // Prevent multiple calls
        if (this.callInProgress) {
            throw "Call in progress";
        };

        this.callInProgress = true;

        this.userhandler = handler;

        // Open an async request - third argument makes it
        // asynchronous.
        this.request.open('GET', this.url, true);

        // Have to assign "this" to a variable.
        var self = this;

        // Assign a closure to the onreadystatechange callback.
        this.request.onreadystatechange = function()
        {
            self.stateChangeCallback(self);
        }

        this.request.send(null);
    },

    stateChangeCallback: function(client)
    {
        switch (client.request.readyState) {
            // Request not yet made.
            case 1:
            try {
                client.userhandler.onInit();
            } catch (e) { /* Handler method not defined. */ }
            break;

            // Contact established with server but nothing downloaded
            // yet.
            case 2:
            try {
                status = client.request.status;
                // Check for HTTP status 200.
                if (status != 200) {
                    client.userhandler.onError(
                        status,
                        client.request.statusText
                        );

                    // Abort the request.
                    client.request.abort();

                    // Call no longer in progress.
                    client.callInProgress = false;
                }
            } catch (e) {
                /* MSXMLHTTP 3.x+ doesn't populate status until
                 * readyState 4. */
            }
            break;

            // Called multiple times while download is in progress.
            case 3:
            // Notify user handler of download progress.
            try {
                // Get the total content length (useful to work
                // out how much has been downloaded).
                var contentLength;
                try {
                    contentLength =
                        client.request.getResponseHeader("Content-Length");
                } catch (e) {
                    contentLength = NaN;
                }

                // Call the progress handler with what we've got.
                client.userhandler.onProgress(
                    client.request.responseText,
                    contentLength
                    );

            } catch (e) { /* Handler method not defined. */ }
            break;

            // Download complete.
            case 4:
            try {
                client.userhandler.onLoad(client.request.responseText);
            } catch (e) {
                /* Handler method not defined. */
            } finally {
                // Call no longer in progress.
                client.callInProgress = false;
            }
            break;
        }
    }

}
