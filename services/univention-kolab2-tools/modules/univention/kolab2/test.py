#!/usr/bin/python2.4

import event

s = '''<?xml version="1.0" encoding="UTF-8"?>
<event version="1.0">
<uid>040000008200E00074C5B7101A82E0080000000000000000000000000000000000000000544DF9E59501314FB319AB960AE706F0</uid>
<body>Test  
</body>
<creation-date>2008-11-13T08:04:27Z</creation-date>
<last-modification-date>2008-12-08T15:02:44Z</last-modification-date>
<sensitivity>public</sensitivity>
<product-id>Bynari Insight Connector 3.0</product-id>
<summary>TEST1</summary>
<location> Bremen</location>
<start-date>2008-11-13T08:30:00Z</start-date>
<end-date>2008-11-13T09:00:00Z</end-date>
<organizer>
<display-name>Mustermann</display-name>
<smtp-address>mustermann@univention.local</smtp-address>
</organizer>
<attendee>
<display-name>&apos;max.mustermann@univention-hb.de&apos;</display-name>
<smtp-address>max.mustermann@univention-hb.de</smtp-address>
<role>required</role>
<status>none</status>
</attendee>
<attendee>
<display-name>Mustermann, Max (Unternehmen)</display-name>
<smtp-address>Mmustermann@univention.local</smtp-address>
<role>required</role>
<status>none</status>
</attendee>
<show-time-as>busy</show-time-as>
<color-label>none</color-label>
</event>'''
d = event.Kolab2Event()
d.parse( s )
d.attendee1_display_name = 'BLA'
print d._doc.toprettyxml()
