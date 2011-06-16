//******************************************************************************
// ------ DTree Tree-menu Data --------------------------------------------
//******************************************************************************

if ( ( typeof( window[ 'homeMenuTitle' ] ) != "undefined" ) )
{
general = new dTree('general');

general.header('&nbsp;&nbsp;<a target="main" href="main.html">' + homeMenuTitle + '</a>','side/home.gif',32,'side/title.gif','#AFB1C3',homeMenuOpen)

general.add(0,-1);
general.add(1,0,'Documentation','docs/index.html','','','side/icons/info.gif');

document.write(general);
}

/////////////////////////////////////////////////////////////////////////////////////

if ( ( typeof( window[ 'monitMenuTitle' ] ) != "undefined" ) )
{
monitoring = new dTree('monitoring');

monitoring.header('&nbsp;&nbsp;<a thref="#">' + monitMenuTitle + '</a>','side/monitoring.gif',32,'side/title.gif','#AFB1C3',monitMenuOpen)

monitoring.add(0,-1);
monitoring.add(1,0,'Tactical Overview',cgipath + 'tac.cgi','','','side/icons/monitoring.gif');
monitoring.add(2,0,'Service Detail',cgipath + 'status.cgi?host=all','','','side/icons/monitoring.gif');
monitoring.add(3,0,'Host Detail',cgipath + 'status.cgi?hostgroup=all&style=hostdetail','','','side/icons/monitoring.gif');
monitoring.add(100,0,"<nobr><input type='hidden' name='navbarsearch' value='1'><input type='text' name='host' value='hostname' size=10 style='font-size:10'></nobr>",'','','','side/icons/search.gif');
monitoring.add(4,0,'Host Group',cgipath + 'status.cgi?hostgroup=all&style=overview','','','side/icons/folder.gif','side/icons/folder_open.gif');
	monitoring.add(5,4,'Summary',cgipath + 'status.cgi?hostgroup=all&style=summary','','','side/icons/monitoring.gif');
	monitoring.add(6,4,'Grid',cgipath + 'status.cgi?hostgroup=all&style=grid','','','side/icons/monitoring.gif');
monitoring.add(7,0,'Service Group',cgipath + 'status.cgi?servicegroup=all&style=overview','','','side/icons/folder.gif','side/icons/folder_open.gif');
	monitoring.add(8,7,'Summary',cgipath + 'status.cgi?servicegroup=all&style=summary','','','side/icons/monitoring.gif');
	monitoring.add(9,7,'Grid',cgipath + 'status.cgi?servicegroup=all&style=grid','','','side/icons/monitoring.gif');
monitoring.add(10,0,'Status Map',cgipath + 'statusmap.cgi?host=all','','','side/icons/map.gif');
monitoring.add(11,0,'Problems','','','','side/icons/folder.gif','side/icons/folder_open.gif');
	monitoring.add(12,11,'Service',cgipath + 'status.cgi?host=all&servicestatustypes=28','','','side/icons/error.gif');
	monitoring.add(13,11,'Host',cgipath + 'status.cgi?hostgroup=all&style=hostdetail&hoststatustypes=12','','','side/icons/error.gif');
	monitoring.add(14,11,'Network Outages',cgipath + 'outages.cgi','','','side/icons/error.gif');
monitoring.add(15,0,'Comments',cgipath + 'extinfo.cgi?&type=3','','','side/icons/notes.gif');
monitoring.add(16,0,'Downtime',cgipath + 'extinfo.cgi?&type=6','','','side/icons/downtime.gif');

document.write(monitoring);
}

/////////////////////////////////////////////////////////////////////////////////////

if ( ( typeof( window[ 'reportMenuTitle' ] ) != "undefined" ) )
{
reporting = new dTree('reporting');

reporting.header('&nbsp;&nbsp;<a thref="#">' + reportMenuTitle + '</a>','side/reporting.gif',32,'side/title.gif','#AFB1C3',reportMenuOpen)

reporting.add(0,-1);
reporting.add(1,0,'Trends',cgipath + 'trends.cgi','','','side/icons/reporting.gif');
reporting.add(2,0,'Availability',cgipath + 'avail.cgi','','','side/icons/reporting.gif');
reporting.add(3,0,'Alerts','','','','side/icons/folder.gif','side/icons/folder_open.gif');
	reporting.add(4,3,'Histogram',cgipath + 'histogram.cgi','','','side/icons/reporting.gif');
	reporting.add(5,3,'History',cgipath + 'history.cgi?host=all','','','side/icons/reporting.gif');
	reporting.add(6,3,'Summary',cgipath + 'summary.cgi','','','side/icons/reporting.gif');
reporting.add(7,0,'Notifications',cgipath + 'notifications.cgi?contact=all','','','side/icons/notifications.gif');
reporting.add(8,0,'Event Log',cgipath + 'showlog.cgi','','','side/icons/notes.gif');

document.write(reporting);
}

/////////////////////////////////////////////////////////////////////////////////////

if ( ( typeof( window[ 'configMenuTitle' ] ) != "undefined" ) )
{
configuration = new dTree('configuration');

configuration.header('&nbsp;&nbsp;<a thref="#">' + configMenuTitle + '</a>','side/configuration.gif',32,'side/title.gif','#AFB1C3',configMenuOpen)

configuration.add(0,-1);
configuration.add(1,0,'Process',cgipath + 'extinfo.cgi?&type=0','','','side/icons/processes.gif');
configuration.add(2,0,'Performance',cgipath + 'extinfo.cgi?&type=4','','','side/icons/performance.gif');
configuration.add(3,0,'Scheduling Queue',cgipath + 'extinfo.cgi?&type=7','','','side/icons/queue.gif');
configuration.add(4,0,'View Config',cgipath + 'config.cgi','','','side/icons/configuration.gif');
if ( ( typeof( window[ 'nagiosQLpath' ] ) != "undefined" ) )
	configuration.add(5,0,'Nagios QL',nagiosQLpath,'','','side/icons/configuration.gif');

document.write(configuration);
}
