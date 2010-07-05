/**
 * Component for filtering a table or any list of children based on
 * the dynamic value of a text input. It requires the prototype.js
 * library.
 *
 * You should define the CSS class .QuickFinderNoMatch to say what
 * happens to items that don't match the criteria. A reasonable
 * default would be display:none.
 *
 * This code is heavily inspired by Filterlicious by Gavin
 * Kistner. The filterlicious JavaScript file did not have a license;
 * however, most of Gavin's code is under the license defined by
 * http://phrogz.net/JS/_ReuseLicense.txt, so I'm including that URL
 * and Gavin's name as acknowledgements.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 *
 * $Horde: mnemo/js/src/QuickFinder.js,v 1.1.2.2 2007-12-22 05:24:23 chuck Exp $
 */

var QuickFinder = {

    attachBehavior: function() {
        $$('input').each(function(input) {
            var filterTarget = input.readAttribute('for');
            if (!filterTarget) {
                return;
            }

            if (filterTarget.indexOf(',') != -1) {
                input.filterTargets = [];
                var targets = filterTarget.split(',');
                for (var i = 0; i < targets.length; ++i) {
                    var t = $(targets[i]);
                    if (t) {
                        input.filterTargets.push(t);
                    }
                }
                if (!input.filterTargets.length) {
                    return;
                }
            } else {
                input.filterTargets = [ $(filterTarget) ];
                if (!input.filterTargets[0]) {
                    return;
                }
            }

            filterEmpty = input.readAttribute('empty');
            if (filterEmpty) {
                input.filterEmpty = $(filterEmpty);
            }

            input.observe('keyup', QuickFinder.onKeyUp);

            for (var i = 0, i_max = input.filterTargets.length; i < i_max; i++) {
                input.filterTargets[i].immediateDescendants().each(function(line) {
                    var filterText = line.filterText || line.readAttribute('filterText');
                    if (!filterText) {
                        line.filterText = line.innerHTML.stripTags();
                    }
                    line.filterText = line.filterText.toLowerCase();
                });
            }

            QuickFinder.filter(input);
        });
    },

    onKeyUp: function(e) {
        input = e.element();
        if (input.filterTargets) {
            QuickFinder.filter(input);
        }
    },

    filter: function(input) {
        var val = input.value.toLowerCase();
        var matched = 0;
        for (var i = 0, i_max = input.filterTargets.length; i < i_max; i++) {
            input.filterTargets[i].immediateDescendants().each(function(line) {
                var filterText = line.filterText;
                if (filterText.indexOf(val) == -1) {
                    line.addClassName('QuickFinderNoMatch');
                } else {
                    ++matched;
                    line.removeClassName('QuickFinderNoMatch');
                }
            });
        }

        try {
            if (input.filterEmpty) {
                (matched == 0) ? input.filterEmpty.show() : input.filterEmpty.hide();
            }
        } catch (e) {}
    }

}

document.observe('dom:loaded', QuickFinder.attachBehavior);
