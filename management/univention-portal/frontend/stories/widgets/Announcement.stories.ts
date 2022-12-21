import { Meta, StoryFn } from '@storybook/vue3';

import Announcement from '../../src/components/widgets/Announcement.vue';

export default {
  title: 'Widgets/Announcement',
  components: Announcement,
  parameters: {
    layout: 'centered',
  },
  argTypes: {
    type: {
      control: {
        type: 'select',
        options: ['success', 'warning', 'error'],
      },
    },
  },
} as Meta<typeof Announcement>;

// Base Template
const Template: StoryFn<typeof Announcement> = (args) => ({
  components: { Announcement },
  setup() {
    return { args };
  },
  template: `
  <div>
    <announcement v-bind='args' />
  </div>`
});

export const Basic = Template.bind({});
Basic.args = {
  type: 'success',
  severity: 'info',
  title:{
    'en': 'My Title',
  },
  message:{
    'en': 'My Message',
  },
  name: 'unique_announcement',
  sticky: false
};
