/**
 * Provides the javascript for the search.php script
 *
 * $Horde: imp/js/src/search.js,v 1.4.2.2 2008-05-20 16:33:02 slusarz Exp $
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

function toggleAll(checked)
{
    $('search').getInputs(null, 'search_folders[]').each(function(e) {
        e.checked = checked;
    });
}

function dateCheck(field)
{
    var m = $('search_' + field + '_month'), d = $('search_' + field + '_day'), y = $('search_' + field + '_year');

    if (m.selectedIndex == 0) {
        m.selectedIndex = search_month;
    }

    if (d.selectedIndex == 0) {
        d.selectedIndex = search_day;
    }

    if (y.value == "") {
        y.value = search_year;
    }
}

function formCheck()
{
    if (not_search &&
        (!$('preselected_folders') || !$F('preselected_folders'))) {
        if (!Form.getInputs('search', null, 'search_folders[]').detect(function(e) { return e.checked; })) {
            alert(IMP.text.search_select);
            return false;
        }
    }

    $('actionID').setValue('do_search');
    return true;
}

function search_reset()
{
    $('actionID').setValue('reset_search');
    $('search').submit();
    return true;
}

function saveCache()
{
    $('edit_query').setValue($F('save_cache'));
    $('search').submit();
}

function delete_field(i)
{
    $('delete_field_id').setValue(i);
    $('actionID').setValue('delete_field');
    $('search').submit();
    return true;
}

function show_subscribed(i)
{
    $('show_subscribed_only').setValue(i);
    $('search').submit();
    return false
}
