<?php

$conf['spell']['driver'] = 'aspell';
$conf['utils']['gnupg'] = '/usr/bin/gpg';

$conf['hooks']['mbox_redirect'] = true;
$conf['hooks']['mbox_icon'] = true;
$conf['hooks']['display_folder'] = true;

$conf['sentmail']['driver'] = 'none';

// Uncomment in order to allow your users to select the type of mailer they wish to use.
// $conf['user']['force_view'] = null;
// $conf['user']['select_view'] = true;
