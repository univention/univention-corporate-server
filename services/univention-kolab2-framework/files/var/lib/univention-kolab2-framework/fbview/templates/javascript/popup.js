function popup(url, width, height)
{
    if (!width) {
        width = 600;
    }
    if (!height) {
        height = 500;
    }

    var now = new Date();
    var name = now.getTime();
    param = "toolbar=no,location=no,status=yes,scrollbars=yes,resizable=yes,width=" + width + ",height=" + height + ",left=0,top=0";
    eval("name = window.open(url, name, param)");
    if (!eval("name.opener")) {
        eval("name.opener = self");
    }

    return name;
}
