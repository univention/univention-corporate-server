/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';
import Tabs, { TabsHeader, TabsBody, TabItem } from '@/components/widgets/Tabs/index';

export default {
  title: 'Widgets/Tabs',
  components: Tabs,
} as Meta<typeof Tabs>;

const Template: StoryFn<typeof Tabs> = (args) => ({
  components: {
    Tabs,
    TabsHeader,
    TabsBody,
    TabItem,
  },
  setup() {
    return { args };
  },
  template: `
    <Tabs v-bind="args"
          style="max-width: none; width: 80vw; padding: 0; background: none; border-radius: 0; box-shadow: none; min-width: 0"
    >

      <TabsHeader v-slot="{activeTab, onActiveTab}">
      </TabsHeader>
      <TabsBody>
        <TabItem tab="generals">
          <div style="padding: 0 16px">
            <h2>
              Generals
            </h2>
          </div>
        </TabItem>

        <TabItem tab="groups">
          <div style="padding: 0 16px">
            <h2>
              Group
            </h2>

          </div>
        </TabItem>

        <TabItem tab="account">
          <div style="padding: 0 16px">
            <h2>
              Account settings
            </h2>

          </div>
        </TabItem>

        <TabItem tab="contacts">
          <div style="padding: 0 16px">
            <h2>
              Contacts
            </h2>

          </div>
        </TabItem>

      </TabsBody>

    </Tabs>
  `,
});

export const Basic = Template.bind({});
Basic.args = {
  tabs: [
    { key: 'generals', label: 'Generals' },
    { key: 'groups', label: 'Groups' },
    { key: 'account', label: 'Account' },
    { key: 'contacts', label: 'Contacts' },

  ],
};
