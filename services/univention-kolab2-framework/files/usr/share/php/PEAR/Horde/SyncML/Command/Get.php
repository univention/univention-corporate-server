<?php

include_once 'Horde/SyncML/State.php';
include_once 'Horde/SyncML/Command.php';
include_once 'Horde/SyncML/Command/Results.php';

/**
 * The Horde_SyncML_Command_Get class.
 *
 * $Horde: framework/SyncML/SyncML/Command/Get.php,v 1.13 2004/05/26 17:41:30 chuck Exp $
 *
 * Copyright 2003-2004 Anthony Mills <amills@pyramid6.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Anthony Mills <amills@pyramid6.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_SyncML
 */
class Horde_SyncML_Command_Get extends Horde_SyncML_Command {

    function output($currentCmdID, &$output)
    {
        $state = $_SESSION['SyncML.state'];

        $status = &new Horde_SyncML_Command_Status((($state->isAuthorized()) ? RESPONSE_OK : RESPONSE_INVALID_CREDENTIALS), 'Get');
        $status->setCmdRef($this->_cmdID);

        $status->setTargetRef('./devinf11');

        $currentCmdID = $status->output($currentCmdID, $output);

        if ($state->isAuthorized()) {
            // Synthesis does not like this one.

            // $results = &new Horde_SyncML_Command_Results();
            // $results->setCmdRef($this->_cmdID);

            // DevInf returnDevInf = new DevInf((version == 0) ? "./devinf" : "./devinf11");

            // result.setData(devinf);
            // $currentCmdID = $results->output($currentCmdID, $output);
        }

        return $currentCmdID;
    }

}

// DevInf info to return. May need to send something like this back:
//
//   <Meta>
//    <Type xmlns='syncml:metinf'>
//     application/vnd.syncml-devinf+xml
//    </Type>
//   </Meta>
//   <Item>
//    <Source>
//     <LocURI>
//      ./devinf11
//     </LocURI>
//    </Source>
//    <Data>
//     <DevInf xmlns='syncml:devinf'>
//      <VerDTD>
//       1.1
//      </VerDTD>
//      <Man>
//       Synthesis AG
//      </Man>
//      <Mod>
//       Synthesis Sync Server 1.0 Demo
//      </Mod>
//      <OEM>
//       Synthesis AG
//      </OEM>
//      <SwV>
//       2.0.1.5
//      </SwV>
//      <DevId>
//       SySync Server (textdb,standalone)
//      </DevId>
//      <DevTyp>
//       server
//      </DevTyp>
//      <UTC>
//      </UTC>
//      <SupportNumberOfChanges>
//      </SupportNumberOfChanges>
//      <SupportLargeObjs>
//      </SupportLargeObjs>
//      <DataStore>
//       <SourceRef>
//        ./contacts
//       </SourceRef>
//       <DisplayName>
//        contacts
//       </DisplayName>
//       <Rx-Pref>
//        <CTType>
//         text/x-vcard
//        </CTType>
//        <VerCT>
//         2.1
//        </VerCT>
//       </Rx-Pref>
//       <Rx>
//        <CTType>
//         text/vcard
//        </CTType>
//        <VerCT>
//         3.0
//        </VerCT>
//       </Rx>
//       <Tx-Pref>
//        <CTType>
//         text/x-vcard
//        </CTType>
//        <VerCT>
//         2.1
//        </VerCT>
//       </Tx-Pref>
//       <Tx>
//        <CTType>
//         text/vcard
//        </CTType>
//        <VerCT>
//         3.0
//        </VerCT>
//       </Tx>
//       <SyncCap>
//        <SyncType>
//         1
//        </SyncType>
//        <SyncType>
//         2
//        </SyncType>
//        <SyncType>
//         4
//        </SyncType>
//        <SyncType>
//         5
//        </SyncType>
//        <SyncType>
//         6
//        </SyncType>
//       </SyncCap>
//      </DataStore>
//      <DataStore>
//       <SourceRef>
//        ./events
//       </SourceRef>
//       <DisplayName>
//        events
//       </DisplayName>
//       <Rx-Pref>
//        <CTType>
//         text/x-vcalendar
//        </CTType>
//        <VerCT>
//         1.0
//        </VerCT>
//       </Rx-Pref>
//       <Tx-Pref>
//        <CTType>
//         text/x-vcalendar
//        </CTType>
//        <VerCT>
//         1.0
//        </VerCT>
//       </Tx-Pref>
//       <SyncCap>
//        <SyncType>
//         1
//        </SyncType>
//        <SyncType>
//         2
//        </SyncType>
//        <SyncType>
//         4
//        </SyncType>
//        <SyncType>
//         5
//        </SyncType>
//        <SyncType>
//         6
//        </SyncType>
//       </SyncCap>
//      </DataStore>
//      <DataStore>
//       <SourceRef>
//        ./tasks
//       </SourceRef>
//       <DisplayName>
//        tasks
//       </DisplayName>
//       <Rx-Pref>
//        <CTType>
//         text/x-vcalendar
//        </CTType>
//        <VerCT>
//         1.0
//        </VerCT>
//       </Rx-Pref>
//       <Tx-Pref>
//        <CTType>
//         text/x-vcalendar
//        </CTType>
//        <VerCT>
//         1.0
//        </VerCT>
//       </Tx-Pref>
//       <SyncCap>
//        <SyncType>
//         1
//        </SyncType>
//        <SyncType>
//         2
//        </SyncType>
//        <SyncType>
//         4
//        </SyncType>
//        <SyncType>
//         5
//        </SyncType>
//        <SyncType>
//         6
//        </SyncType>
//       </SyncCap>
//      </DataStore>
//      <DataStore>
//       <SourceRef>
//        ./calendar
//       </SourceRef>
//       <DisplayName>
//        calendar
//       </DisplayName>
//       <Rx-Pref>
//        <CTType>
//         text/x-vcalendar
//        </CTType>
//        <VerCT>
//         1.0
//        </VerCT>
//       </Rx-Pref>
//       <Tx-Pref>
//        <CTType>
//         text/x-vcalendar
//        </CTType>
//        <VerCT>
//         1.0
//        </VerCT>
//       </Tx-Pref>
//       <SyncCap>
//        <SyncType>
//         1
//        </SyncType>
//        <SyncType>
//         2
//        </SyncType>
//        <SyncType>
//         3
//        </SyncType>
//        <SyncType>
//         4
//        </SyncType>
//        <SyncType>
//         5
//        </SyncType>
//        <SyncType>
//         6
//        </SyncType>
//       </SyncCap>
//      </DataStore>
//      <DataStore>
//       <SourceRef>
//        ./notes
//       </SourceRef>
//       <DisplayName>
//        notes
//       </DisplayName>
//       <Rx-Pref>
//        <CTType>
//         text/plain
//        </CTType>
//        <VerCT>
//         1.0
//        </VerCT>
//       </Rx-Pref>
//       <Tx-Pref>
//        <CTType>
//         text/plain
//        </CTType>
//        <VerCT>
//         1.0
//        </VerCT>
//       </Tx-Pref>
//       <SyncCap>
//        <SyncType>
//         1
//        </SyncType>
//        <SyncType>
//         2
//        </SyncType>
//        <SyncType>
//         4
//        </SyncType>
//        <SyncType>
//         5
//        </SyncType>
//        <SyncType>
//         6
//        </SyncType>
//       </SyncCap>
//      </DataStore>
//      <CTCap>
//       <CTType>
//        text/x-vcard
//       </CTType>
//       <PropName>
//        BEGIN
//       </PropName>
//       <ValEnum>
//        VCARD
//       </ValEnum>
//       <PropName>
//        END
//       </PropName>
//       <ValEnum>
//        VCARD
//       </ValEnum>
//       <PropName>
//        VERSION
//       </PropName>
//       <ValEnum>
//        2.1
//       </ValEnum>
//       <PropName>
//        REV
//       </PropName>
//       <PropName>
//        N
//       </PropName>
//       <PropName>
//        TITLE
//       </PropName>
//       <PropName>
//        ORG
//       </PropName>
//       <PropName>
//        EMAIL
//       </PropName>
//       <PropName>
//        URL
//       </PropName>
//       <PropName>
//        TEL
//       </PropName>
//       <PropName>
//        ADR
//       </PropName>
//       <PropName>
//        BDAY
//       </PropName>
//       <PropName>
//        NOTE
//       </PropName>
//       <CTType>
//        text/vcard
//       </CTType>
//       <PropName>
//        BEGIN
//       </PropName>
//       <ValEnum>
//        VCARD
//       </ValEnum>
//       <PropName>
//        END
//       </PropName>
//       <ValEnum>
//        VCARD
//       </ValEnum>
//       <PropName>
//        VERSION
//       </PropName>
//       <ValEnum>
//        3.0
//       </ValEnum>
//       <PropName>
//        REV
//       </PropName>
//       <PropName>
//        N
//       </PropName>
//       <PropName>
//        TITLE
//       </PropName>
//       <PropName>
//        ORG
//       </PropName>
//       <PropName>
//        EMAIL
//       </PropName>
//       <PropName>
//        URL
//       </PropName>
//       <PropName>
//        TEL
//       </PropName>
//       <PropName>
//        ADR
//       </PropName>
//       <PropName>
//        BDAY
//       </PropName>
//       <PropName>
//        NOTE
//       </PropName>
//       <CTType>
//        text/x-vcalendar
//       </CTType>
//       <PropName>
//        BEGIN
//       </PropName>
//       <ValEnum>
//        VCALENDAR
//       </ValEnum>
//       <ValEnum>
//        VEVENT
//       </ValEnum>
//       <ValEnum>
//        VTODO
//       </ValEnum>
//       <PropName>
//        END
//       </PropName>
//       <ValEnum>
//        VCALENDAR
//       </ValEnum>
//       <ValEnum>
//        VEVENT
//       </ValEnum>
//       <ValEnum>
//        VTODO
//       </ValEnum>
//       <PropName>
//        VERSION
//       </PropName>
//       <ValEnum>
//        1.0
//       </ValEnum>
//       <PropName>
//        TZ
//       </PropName>
//       <PropName>
//        LAST-MODIFIED
//       </PropName>
//       <PropName>
//        DCREATED
//       </PropName>
//       <PropName>
//        SUMMARY
//       </PropName>
//       <PropName>
//        DESCRIPTION
//       </PropName>
//       <PropName>
//        LOCATION
//       </PropName>
//       <PropName>
//        CATEGORIES
//       </PropName>
//       <PropName>
//        DTSTART
//       </PropName>
//       <PropName>
//        DTEND
//       </PropName>
//       <PropName>
//        ATTENDEE
//       </PropName>
//       <PropName>
//        RRULE
//       </PropName>
//       <PropName>
//        EXDATE
//       </PropName>
//       <PropName>
//        AALARM
//       </PropName>
//       <PropName>
//        DALARM
//       </PropName>
//       <PropName>
//        LOCATION
//       </PropName>
//       <PropName>
//        CATEGORIES
//       </PropName>
//       <PropName>
//        DUE
//       </PropName>
//       <PropName>
//        PRIORITY
//       </PropName>
//       <PropName>
//        STATUS
//       </PropName>
//       <PropName>
//        AALARM
//       </PropName>
//       <PropName>
//        DALARM
//       </PropName>
//      </CTCap>
//     </DevInf>
//    </Data>
//   </Item>
