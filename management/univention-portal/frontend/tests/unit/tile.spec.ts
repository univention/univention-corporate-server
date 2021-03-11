import PortalTile from '@/components/PortalTile.vue';
import { mount } from '@vue/test-utils';

/*
    This is just a simple test to check if a Tile renders.
    Not terribly useful but a good starter. The most basic
    form of component testing is just to mount one and then
    test it's behaviour. In the future when the tile also has
    an edit function, this can be used to develop test driven.
*/
test('Test tile rendering', () => {
  const wrapper = mount(PortalTile, {
    props: {
      title: 'Test Title',
      link: 'https://test.com',
    },

  });

  // Assert the rendered text of the component
  expect(wrapper.text()).toContain('Test Title');

  // fetch an element by a smartly placed data attribute
  expect(wrapper.get('[data-test="tileLink"]').attributes('class')).toBe(
    'portal-tile',
  );
});
