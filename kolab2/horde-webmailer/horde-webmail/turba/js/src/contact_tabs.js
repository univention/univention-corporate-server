var contactTabs = null;
function ShowTab(tab)
{
    if (contactTabs == null) {
        contactTabs = $('page').select('.tabset')[0].down();
    }

    contactTabs.select('li').each(function(item) {
        if (item.id == 'tab' + tab) {
            item.addClassName('activeTab');
            $(item.id.substring(3)).show();
        } else {
            item.removeClassName('activeTab');
            $(item.id.substring(3)).hide();
        }
    });

    return false;
}
