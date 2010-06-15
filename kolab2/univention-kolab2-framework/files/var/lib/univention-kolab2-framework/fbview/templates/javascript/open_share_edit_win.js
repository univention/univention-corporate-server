function open_share_edit_win(url)
{
    var now = new Date();
    var name = "share_edit_window_" + now.getTime();
    param = "toolbar=no,location=no,status=yes,scrollbars=yes,resizable=yes,width=600,height=500,left=0,top=0";
    eval("name = window.open(url, name, param)");
    if (!eval("name.opener")) {
        eval("name.opener = self");
    }
}
