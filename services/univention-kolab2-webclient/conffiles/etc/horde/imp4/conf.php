<?php
// Warning: This file is auto-generated and might be overwritten by
//          univention-baseconfig.
//          Please edit the following file instead:
// Warnung: Diese Datei wurde automatisch generiert und kann durch
//          univention-baseconfig überschrieben werden.
//          Bitte bearbeiten Sie an Stelle dessen die folgende Datei:
//
// 	/etc/univention/templates/files/etc/horde/imp4/conf.php
//
$conf['utils']['spellchecker'] = '/usr/bin/aspell';
$conf['utils']['gnupg'] = '/usr/bin/gpg';
$conf['utils']['gnupg_keyserver'] = array('wwwkeys.pgp.net');
$conf['utils']['gnupg_timeout'] = '10';
$conf['utils']['openssl_binary'] = '/usr/bin/openssl';
$conf['menu']['apps'] = array();
$conf['user']['select_sentmail_folder'] = false;
$conf['user']['allow_resume_all_in_drafts'] = false;
$conf['user']['allow_folders'] = true;
$conf['user']['allow_resume_all'] = false;
$conf['user']['allow_view_source'] = true;
$conf['user']['alternate_login'] = false;
$conf['user']['redirect_on_logout'] = false;
$conf['user']['select_view'] = true;
$conf['server']['change_server'] = false;
$conf['server']['change_port'] = false;
$conf['server']['change_protocol'] = false;
$conf['server']['change_smtphost'] = false;
$conf['server']['change_smtpport'] = false;
$conf['server']['server_list'] = 'none';
$conf['server']['fixed_folders'] = array();
$conf['server']['sort_limit'] = '0';
$conf['server']['cache_folders'] = true;
$conf['server']['token_lifetime'] = 1800;
$conf['server']['cachejs'] = 'none';
$conf['server']['cachecss'] = 'none';
$conf['mailbox']['show_attachments'] = false;
$conf['mailbox']['show_preview'] = false;
$conf['mailbox']['show_xpriority'] = false;
$conf['fetchmail']['show_account_colors'] = false;
$conf['fetchmail']['size_limit'] = '4000000';
$conf['msgsettings']['filtering']['words'] = './config/filter.txt';
$conf['msgsettings']['filtering']['replacement'] = '****';
$conf['spam']['reporting'] = false;
$conf['notspam']['reporting'] = false;
$conf['print']['add_printedby'] = false;
$conf['msg']['prepend_header'] = true;
$conf['msg']['append_trailer'] = false;
$conf['compose']['allow_cc'] = true;
$conf['compose']['allow_bcc'] = true;
$conf['compose']['allow_receipts'] = true;
$conf['compose']['special_characters'] = true;
$conf['compose']['use_vfs'] = false;
$conf['compose']['link_all_attachments'] = false;
$conf['compose']['link_attachments_notify'] = true;
$conf['compose']['link_attachments'] = true;
$conf['compose']['add_maildomain_to_unexpandable'] = false;
$conf['compose']['attach_size_limit'] = '0';
$conf['compose']['attach_count_limit'] = '0';
$conf['compose']['reply_limit'] = 200000;
$conf['hooks']['vinfo'] = false;
$conf['hooks']['postlogin'] = false;
$conf['hooks']['postsent'] = false;
$conf['hooks']['signature'] = false;
$conf['hooks']['trailer'] = false;
$conf['hooks']['fetchmail_filter'] = false;
$conf['hooks']['mbox_redirect'] = true;
$conf['hooks']['mbox_icon'] = true;
$conf['hooks']['spam_bounce'] = false;
$conf['hooks']['msglist_format'] = false;
$conf['maillog']['use_maillog'] = true;
$conf['sentmail']['driver'] = 'none';
$conf['tasklist']['use_tasklist'] = true;
$conf['notepad']['use_notepad'] = true;
