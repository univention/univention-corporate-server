/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import ChooseTabs from '@/components/ChooseTabs';
import _ from '@/jsHelper/translate';
import { store } from '@/store/';
import univentionLogo from './../assets/choose-tabs/univention-logo.png';
import wikipediaLogo from './../assets/choose-tabs/wikipedia-logo.png';
import storybookLogo from './../assets/choose-tabs/storybook-logo.svg';


export default {
  title: 'Components/ChooseTabs',
  components: ChooseTabs,
};
store.dispatch('activity/setLevel', ['modal']);
const Mock = {
  tabs: [{
    tabLabel: 'Univention Corporate Server',
    logo: wikipediaLogo,
    iframeLink: 'https://en.wikipedia.org/wiki/Univention_Corporate_Server'
  },
  {
    tabLabel: 'Univention Blog: Corporate Server 5.0-2',
    logo: univentionLogo,
    iframeLink: 'https://www.univention.de/blog-de/aus-der-entwicklung/2022/06/ucs-5-0-2-point-release/'
  },
  {
    tabLabel: 'Open Source',
    logo: wikipediaLogo,
    iframeLink: 'https://en.wikipedia.org/wiki/Open_source'
  },
  {
    tabLabel: 'Build component driven UIs faster',
    logo: storybookLogo,
    iframeLink: 'https://storybook.js.org/'
  }],
  scrollPosition: 0,
 };

Mock.tabs.forEach((tab) => {
  store.dispatch('tabs/addTab', tab);
});
store.dispatch('tabs/setActiveTab', 1);


const Template = (args) => ({
  components: { ChooseTabs },
  setup() {
    return {args};
  },
  template: '<choose-tabs v-bind="args" />',
  store: store,
});

export const FirstTabActive = Template.bind({});

