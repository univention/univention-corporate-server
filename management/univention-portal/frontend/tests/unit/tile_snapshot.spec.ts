import { mount } from '@vue/test-utils';

import PortalTile from '@/components/PortalTile.vue';
/*
    This is just a simple test to check if a Tile renders.
    It is the same as the last example but instead of writing
    everything by hand we use snapshots.

    https://jestjs.io/docs/en/snapshot-testing
*/
test('Test tile rendering', () => {
  // Create a rendering of the component
  const wrapper = mount(PortalTile, {
    props: {
      title: 'Test Title',
      link: 'https://test.com',
    },
  });

  // Assert everything is as it was
  expect(wrapper.element).toMatchSnapshot();
});
