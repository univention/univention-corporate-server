/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import PortalToolTip from '@/components/PortalToolTip';
import _ from '@/jsHelper/translate';

export default {
  title: 'Components/PortalToolTip',
  components: PortalToolTip,
};

const positionMock = {
  position: {
    top: 0,
    right: 100,
    bottom: 100,
    left: 0,
    x: 0,
    y: 0,
  }
};

const tooltipMock = {
  title: 'System and domain settings',
  description: 'Univention Management Console for admin­is­tra­ting the UCS domain and the local system',
};

const linkTypes = {
  samewindow: {
    label: _('Same tab'),
    icon: 'sidebar',
  },
  newwindow: {
    label: _('New Tab'),
    icon: 'external-link',
  },
  embedded: {
    label: _('iFrame'),
    icon: 'layout',
  },
  download: {
    label: _('Download'),
    icon: 'download',
  },
};

const Template = (args) => ({
  components: { PortalToolTip },
  setup() {
    return {args};
  },
  template: '<portal-tool-tip v-bind="args"></portal-tool-tip>',
});

export const SameTab = Template.bind({});
SameTab.args = {
  ...positionMock,
  isMobile: false,
  linkType: linkTypes.samewindow,
  ...tooltipMock
};

export const NewWindow = Template.bind({});
NewWindow.args = {
  ...positionMock,
  isMobile: false,
  ...tooltipMock,
  linkType: linkTypes.newwindow,
};

export const Embedded = Template.bind({});
Embedded.args = {
  ...positionMock,
  isMobile: false,
  ...tooltipMock,
  linkType: linkTypes.embedded,
};

export const Download = Template.bind({});
Download.args = {
  ...positionMock,
  isMobile: false,
  ...tooltipMock,
  linkType: linkTypes.download,
};


// not working properly, stylus media querys not working
export const MobileToolTip = Template.bind({});
MobileToolTip.args = {
  ...positionMock,
  isMobile: true,
  ...tooltipMock,
  linkType: linkTypes.download,
};
MobileToolTip.parameters = {
  viewport: {
    defaultViewport: "Small mobile",
  },
};