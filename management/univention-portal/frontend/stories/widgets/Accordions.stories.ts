/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import MyForm from '@/components/forms/Form.vue';

import Accordions, { AccordionItem } from '@/components/widgets/Accordions';
import { Meta, StoryFn } from '@storybook/vue3';
import { ref } from 'vue';

export default {
  title: 'Widgets/Accordions',
  components: Accordions,
} as Meta<typeof Accordions>;

// Base Template
const Template: StoryFn<typeof Accordions> = (args) => ({
  components: {
    Accordions,
    AccordionItem,
    MyForm,
  },
  setup() {
    const userAccountValues = ref({
      name: 'John',
      lastName: 'Doe',
      username: 'johndoe',
      description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    });

    const personalInfoValues = ref({
      displayName: 'John Doe',
      birthdate: '1990-01-01',
    });

    const organisationValue = ref({
      organisation: 'My Organization',
      employeeNumber: '123456',
      employeeType: 'Sales Manager',
      superiors: ['John Doe', 'Jane Doe'],
    });

    return {
      args,
      userAccountValues,
      personalInfoValues,
      organisationValue,
    };
  },
  template: `
    <Accordions v-bind="args" title="Basic settings">
      <AccordionItem title="User Account">
          <my-form :widgets="[{
              type: 'TextBox',
              name: 'name',
              label: 'First Name',
            }, {
              type: 'TextBox',
              name: 'lastName',
              label: 'Last Name',
            }, {
              type: 'TextBox',
              name: 'username',
              label: 'Username',
            }, {
              type: 'TextBox',
              name: 'description',
              label: 'Description',
            }]" v-model="userAccountValues"
          />
      </AccordionItem>
      <AccordionItem title="Personal Information">
        <my-form :widgets="[{
              type: 'TextBox',
              name: 'displayName',
              label: 'Display Name',
            }, {
              type: 'DateBox',
              name: 'birthdate',
              label: 'Birthdate',
              description: 'Date of birth',
            }]" v-model="personalInfoValues"
        />
      </AccordionItem>
      <AccordionItem title="Organisation">
        <my-form :widgets="[{
              type: 'TextBox',
              name: 'organisation',
              label: 'Organisation',
            }, {
              type: 'TextBox',
              name: 'employeeNumber',
              label: 'Employee number',
            }, {
              type: 'TextBox',
              name: 'employeeType',
              label: 'Employee type',
            }, {
              type: 'MultiSelect',
              name: 'superiors',
              label: 'Superiors',
            }, ]" v-model="organisationValue"
        />
      </AccordionItem>
    </Accordions>
  `,
});

export const Basic = Template.bind({});
Basic.args = {
  title: 'Accordions Title',
};
