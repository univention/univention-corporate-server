Event.observe(window, 'load', function() {
    var nodeCount = kronolithNodes.length;
    for (var n = 0; n < nodeCount; n++) {
        var j = kronolithNodes[n];
        $(j).update(kronolith[j]);
        if (typeof Horde_ToolTips != 'undefined') {
            // Need a closure here to ensure we preserve the value of j during
            // each loop iteration.
            (function() {
                var jx = j;
                Horde_ToolTips.attachBehavior(jx);
            })();
        }
    }
    Event.observe(window, 'unload', Horde_ToolTips.out.bind(Horde_ToolTips));
});