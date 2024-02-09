/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import { Meta, StoryFn } from '@storybook/vue3';

import MultiChoice from '../../src/components/widgets/MultiChoice.vue';

export default {
  title: 'Widgets/MultiChoice',
  components: MultiChoice,
  parameters: {
    layout: 'centered',
  },
} as Meta<typeof MultiChoice>;

// Base Template
const Template: StoryFn<typeof MultiChoice> = (args) => ({
  components: { MultiChoice },
  setup() {
    return { args };
  },
  template: '<div style="width: 500px; padding: 1rem;"><MultiChoice v-bind="args" /></div>',
});

export const Array = Template.bind({});
Array.args = {
  name: 'MultiChoice',
  label: 'My MultiChoice',
  modelValue: ['Sun 2-3'],
  lists: ['Sun 2-3', 'Sun 3-4', 'Sun 4-5', 'Sun 5-6', 'Sun 6-7', 'Sun 7-8', 'Sun 8-9', 'Sun 9-10', 'Sun 10-11'],
};

export const Collection = Template.bind({});
Collection.args = {
  name: 'MultiChoice',
  label: 'My MultiChoice',
  modelValue: [
    { id: 2, name: 'test 2', foo: 'bar hhhh' },
    { id: '3', name: 'test  string ID 3', foo: 'bar ccc' },
  ],
  lists: [
    { id: 2, name: 'test 2', foo: 'bar hhhh' },
    { id: '3', name: 'test  string ID 3', foo: 'bar ccc' },
    { id: '4', name: 'test string ID 4', foo: 'bar xxx' },
    { id: null, name: 'test null ID', foo: 'bar asdasd' },
    { id: undefined, name: 'test undefined ID', foo: 'bar hhh' },
    { id: 11, name: 'dupplicate test 11', foo: 'bar yy' },
    { id: 11, name: 'dupplicate test 11', foo: 'bar xx' },
  ],
};
