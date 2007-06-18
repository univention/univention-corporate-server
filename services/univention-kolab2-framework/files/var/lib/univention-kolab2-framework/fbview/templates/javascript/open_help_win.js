function open_help_win(module, topic)
{
    var win_location;
    var screen_width, screen_height;
    var win_top, win_left;
    var HelpWin;

    screen_height = 0;
    screen_width = 0;
    win_top = 0;
    win_left = 0;

    var help_win_width = 300;
    var help_win_height = 300;

    if (window.innerWidth) screen_width = window.innerWidth;
    if (window.innerHeight) screen_height = window.innerHeight;

    url = '<?php echo Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') . '/services/help/', true) ?>';
    if (url.indexOf('?') == -1) {
        glue = '?';
    } else {
        glue = '<?php echo ini_get('arg_separator.output') ?>';
    }
    url += glue + 'module=' + module;
    glue = '<?php echo ini_get('arg_separator.output') ?>';
    if (topic != null) {
        if (topic == "") {
            url += glue + 'show=topics';
        } else {
            url += glue + 'topic=' + topic;
        }
    }

    win_top = screen_height - help_win_height - 20;
    win_left = screen_width - help_win_width - 20;
    HelpWin = window.open(url, 'HelpWindow',
        'resizable,width=' + help_win_width + ',height=' + help_win_height + ',top=' + win_top + ',left=' + win_left
    );
    HelpWin.focus();
}
