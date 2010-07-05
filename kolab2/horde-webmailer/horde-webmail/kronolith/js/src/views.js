var eventTabs = null;
var Views = {

    hash: $H(),
    keys: [],

    get: function(key)
    {
        return this.hash.get(key);
    },

    push: function(key, val)
    {
        this.hash.set(key, val);
        this.keys.push(key);
        if (this.hash.size() > 10) {
            this.hash.unset(this.keys.pop());
        }
    },

    invalidate: function()
    {
        this.hash = $H();
        this.keys = [];
    }

};

function ShowView(view, time, cache)
{
    if (Object.isUndefined(Ajax.Updater)) {
        return true;
    }

    if (Object.isUndefined(cache)) {
        cache = true;
    }

    // Build the request URL for later use, and as a hash key.
    var params = $H({ view: view });
    if (typeof time == 'object') {
        params.update(time);
    } else {
        params.set('timestamp', time);
    }

    var url = KronolithVar.view_url + (KronolithVar.view_url.include('?') ? '&' : '?') + params.toQueryString();

    // Look for cached views.
    if (Views.get(url)) {
        $('page').update(Views.get(url));
        _ShowView();
    } else {
        // Add the Loading ... notice.
        $('page').appendChild(new Element('DIV', { id: 'pageLoading' }).update(KronolithText.loading));
        $('pageLoading').clonePosition('page');
        new Effect.Opacity('pageLoading', { from: 0.0, to: 0.5 });

        // Update the page div.
        if (cache) {
            new Ajax.Updater('page', url, { onComplete: function() { Views.push(url, $('page').innerHTML); _ShowView(); } });
        } else {
            new Ajax.Updater('page', url, { onComplete: _ShowView });
        }
    }

    return false;
}

function _ShowView()
{
    if (Object.isFunction(stripeAllElements)) {
        stripeAllElements();
    }
    if (typeof ToolTips == 'object') {
        ToolTips.out();
        ToolTips.attachBehavior();
    }

    var titleDiv = $('view_title');
    if (titleDiv && titleDiv.firstChild && titleDiv.firstChild.nodeValue) {
        var title = KronolithVar.page_title + titleDiv.firstChild.nodeValue;
        try {
            document.title = title;
            if (parent.frames.horde_main) {
                parent.document.title = title;
            }
        } catch (e) {}
    }

    var viewVars = $('view_vars');
    if (viewVars) {
        kronolithView = viewVars.readAttribute('view');
        kronolithTimestamp = viewVars.readAttribute('timestamp');
        kronolithPrintLink = viewVars.readAttribute('print');
    }
}

function ShowTab(tab)
{
    if (eventTabs == null) {
        eventTabs = $('page').select('.tabset ul li');
    }

    eventTabs.each(function(c) {
        var t = $(c.id.substring(3));
        if (!t) {
            return;
        }
        if (c.id == 'tab' + tab) {
            c.addClassName('activeTab');
            t.show();
        } else {
            c.removeClassName('activeTab');
            t.hide();
        }
    });

    return false;
}
