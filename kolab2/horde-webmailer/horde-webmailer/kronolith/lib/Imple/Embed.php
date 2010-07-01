<?php
/**
 * Ansel_XRequest_Embed:: Class for embedding a small gallery widget in external
 * websites. Meant to be called via a single script tag, therefore this will
 * always return nothing but valid javascript.
 *
 * $Horde: kronolith/lib/Imple/Embed.php,v 1.5.2.6 2009-01-06 15:24:46 jan Exp $
 *
 * Copyright 2008-2009 The Horde Project (http://www.horde.org/)
 *
 * @author Michael J. Rubinsky <mrubinsk@horde.org>
 *
 * @package Ansel
 */
class Imple_Embed extends Imple {

    /**
     * Override the parent method since it uses Horde::addScriptFile()
     *
     */
    function attach()
    {
        //noop
    }


    /**
     * Handles the output of the embedded widget. This must always be valid
     * javascript.
     * <pre>
     * The following arguments are required:
     *   view      => the view (block) we want
     *   container => the DOM node to populate with the widget
     *   calendar  => the share_name for the requested calendar
     *
     * The following are optional (and are not used for all views)
     *   months     => the number of months to include
     *   maxevents     => the maximum number of events to show
     *
     * @param array $args  Arguments for this view.
     */
    function handle($args)
    {
        /* First, determine the type of view we are asking for */
        $view = $args['view'];

        /* The DOM container to put the HTML in on the remote site */
        $container = $args['container'];

        /* The share_name of the calendar to display */
        $calendar = $args['calendar'];

        /* Deault to showing only 1 month when we have a choice */
        $count_month = (!empty($args['months']) ? $args['months'] : 1);

        /* Default to no limit for the number of events */
        $max_events = (!empty($args['maxevents']) ? $args['maxevents'] : 0);

        if (!empty($args['css']) && $args['css'] == 'none') {
            $nocss = true;
        }

        /* Load the registry with no session control */
        $registry = &Registry::singleton(HORDE_SESSION_NONE);


        /* Build the block parameters */
        $params = array('calendar' => $calendar,
                        'maxevents' => $max_events,
                        'months' => $count_month);

        /* Call the Horde_Block api to get the calendar HTML */
        $title = $registry->call('horde/blockTitle', array('kronolith', $view, $params));
        $results = $registry->call('horde/blockContent', array('kronolith', $view, $params));

        /* Some needed paths */
        // @TODO: Is this going to be merged to FW_3? If so, need to keep this
        // in Kronolith's js path - otherwise we can change it to Horde's
        $js_path = $registry->get('jsuri', 'kronolith');
        $pturl = Horde::url($js_path . '/prototype.js', true);

        /* Local js */
        $jsurl = Horde::url($js_path . '/embed.js', true);

        /* Horde's js */
        $hjs_path = $registry->get('jsuri', 'horde');
        $hjsurl = Horde::url($hjs_path . '/horde-embed.js', true);

        /* CSS */
        if (empty($nocss)) {
            $cssurl = Horde::url($registry->get('themesuri', 'kronolith') . '/embed.css', true);
            $hcssurl = Horde::url($registry->get('themesurl', 'horde') . '/embed.css', true);
        } else {
            $cssurl= '';
        }

        /* Escape the text and put together the javascript to send back */
        $results = addslashes('<div class="kronolith_embedded"><div class="title">' . $title . '</div>' . $results . '</div>');
        $html = <<<EOT
        //<![CDATA[
        if (typeof kronolith == 'undefined') {
            if (typeof Horde_ToolTips == 'undefined') {
                document.write('<script type="text/javascript" src="$hjsurl"></script>');
                document.write('<link type="text/css" rel="stylesheet" href="$hcssurl" />');
            }
            if (typeof Prototype == 'undefined') {
                document.write('<script type="text/javascript" src="$pturl"></script>');
            }
            kronolith = new Object();
            kronolithNodes = new Array();
            document.write('<script type="text/javascript" src="$jsurl"></script>');
            document.write('<link type="text/css" rel="stylesheet" href="$cssurl" />');
        }
        kronolithNodes[kronolithNodes.length] = '$container';
        kronolith['$container'] = "$results";
        //]]>
EOT;

        /* Send it */
        header('Content-Type: text/javascript');
        echo $html;
        exit;
    }

}
