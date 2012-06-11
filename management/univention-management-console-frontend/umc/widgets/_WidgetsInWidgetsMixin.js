/*
 * Copyright 2011-2012 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets._WidgetsInWidgetsMixin");

//
// This code is taken from the site:
// http://higginsforpresident.net/2010/01/widgets-within-widgets/
//

dojo.declare("umc.widgets._WidgetsInWidgetsMixin", null, {
    // summary:
    //    The Foundation widget for our things. Includes _Widget and _Templated with some custom addin methods.

    adopt: function(/* Function */Class, /* Object? */props, /* DomNode? */node){
        // summary: Instantiate some new item from a passed Class, with props with an optional srcNode (node)
        //  reference. Also tracks this widget as if it were a child to be destroyed when this parent widget
        //  is removed.
        //
        // Class: Function
        //      The class to instantiate. Cannot be a string. Use dojo.getObject to get a full class object if you
        //      must.
        //
        // props: Object?
        //      An optional object mixed into the constructor of said Class.
        //
        // node: DomNode?
        //      An optional srcNodeRef to use with dijit._Widget. This thinger will be instantiated using
        //      this passed node as the target if passed. Otherwise a new node is created and you must placeAt() your
        //      instance somewhere in the dom for it to be useful.
        //
        // example:
        //  |    this.adopt(my.ui.Button, { onClick: function(){} }).placeAt(this.domNode);
        //
        // example:
        //  |   var x = this.adopt(my.ui.Button).placeAt(this.domNode);
        //  |   x.connect(this.domNode, "onclick", "fooBar");
        //
        //  example:
        //  If you *must* new up a thinger and only want to adopt it once, use _addItem instead:
        //  |   var t;
        //  |   if(4 > 5){ t = new my.ui.Button(); }else{ t = new my.ui.OtherButton() }
        //  |   this._addItem(t);

        var x = new Class(props, node);
        this._addItem(x);
        return x; // my.Widget
    },

    _addItem: function(/* dijit._Widget... */){
        // summary: Add any number of programatically created children to this instance for later cleanup.
        // private, use `adopt` directly.
        this._addedItems = this._addedItems || [];
        this._addedItems.push.apply(this._addedItems, arguments);
    },

    orphan: function(/* dijit._Widget */widget, /* Boolean? */destroy){
        // summary: remove a single item from this instance when we destroy it. It is the parent widget's job
        // to properly destroy an orphaned child.
        //
        // widget:
        //      A widget reference to remove from this parent.
        //
        // destroy:
        //      An optional boolean used to force immediate destruction of the child. Pass any truthy value here
        //      and the child will be orphaned and killed.
        //
        // example:
        //  Clear out all the children in an array, but do not destroy them.
        //  |   dojo.forEach(this._thumbs, this.orphan, this);
        //
        // example:
        //  Create and destroy a button cleanly:
        //  |   var x = this.adopt(my.ui.Button, {});
        //  |   this.orphan(x, true);
        //
        this._addedItems = this._addedItems || [];
        var i = dojo.indexOf(this._addedItems, widget);
        if (i >= 0) {
			this._addedItems.splice(i, 1);
		}
        if (destroy) {
			this._kill(widget);
		}
    },

    _kill: function(w){
        // summary: Private helper function to properly destroy a widget instance.
        if (w && w.destroyRecursive){
            w.destroyRecursive();
        }
		else if (w && w.destroy){
            w.destroy();
        }
    },

    destroy: function(){
        // summary: override the default destroy function to account for programatically added children.
        dojo.forEach(this._addedItems, this._kill);
        this.inherited(arguments);
    }
});

