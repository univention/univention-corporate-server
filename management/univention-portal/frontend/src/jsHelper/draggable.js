import { onMounted, onUpdated, ref, watch } from 'vue';

const dragdelay = (callback, wait) => {
  let waiting = false;
  return (e) => {
    if (waiting) {
      return;
    }
    callback(e);
    waiting = true;
    setTimeout(() => {
      waiting = false;
    }, wait);
  };
};

const showPlaceholder = (item) => {
  const itemId = `#placeholder-${item}`;
  const placeholderItem = document.querySelector(itemId);

  if (placeholderItem) {
    if (placeholderItem.style.display === 'none') {
      placeholderItem.style.display = 'block';
    } else {
      placeholderItem.style.display = 'none';
    }
  }
};

const hidePlaceholder = () => {
  const placeholderElement = '.dragdrop__placeholder--dotted';
  const placeholder = document.querySelectorAll(placeholderElement);

  if (placeholder && placeholder.length > 0) {
    /* eslint-disable no-param-reassign */
    placeholder.forEach((el) => {
      el.style.display = 'none';
    });
    /* eslint-enable no-param-reassign */
  }
};

const changePosition = (itemToChange, items, position) => {
  const newItems = items.filter((item) => item.id !== itemToChange.id);
  newItems.splice(position, 0, {
    ...itemToChange,
  });
  return newItems;
};

const draggingItem = ref({});
const currentDropZoneId = ref(null);
let transitioning = false;

const useDraggableContainer = ({ initialItems, dropZoneId }, context) => {
  const items = ref(initialItems.value);
  console.log('ITEMS', items);
  // update model when dropped
  watch(draggingItem, () => {
    if (draggingItem.value.id) {
      return;
    }
    context.emit('update:modelValue', items.value);
  });

  // watch(currentDropZoneId, () => {
  //   if (currentDropZoneId.value === dropZoneId.value) {
  //     return;
  //   }
  //   items.value = items.value.filter((item) => item.id !== draggingItem.value.id);
  //   console.log('items.value', items.value);
  // });

  const onItemDragOver = ({ position }) => {
    if (transitioning || draggingItem.value === {}) {
      return;
    }
    items.value = changePosition(draggingItem.value, items.value, position);
    console.log('items.value', items.value);
  };

  const containerDragOver = () => {
    if (
      transitioning ||
      draggingItem.value === {} ||
      dropZoneId.value === currentDropZoneId.value
    ) {
      return;
    }

    if (items.value.length > 0) {
      return;
    }

    currentDropZoneId.value = dropZoneId.value;
    items.value = [draggingItem.value];
  };

  const style = '';

  return {
    style,
    defaultItems: items,
    onItemDragOver,
    containerDragOver,
  };
};

const useDraggableItem = ({ item, position, dropZoneId }, context) => {
  const draggable = ref(null);
  console.log('draggable___', draggable);
  const isDragging = ref(
    item.value.id === draggingItem.value.id,
  );
  const middleY = ref(null);

  onMounted(async () => {
    let ret = true;
    setTimeout(() => {
      if (draggable.value !== null) {
        // console.log('onMounted - draggable.value: ', draggable.value);
        const box = draggable.value.getBoundingClientRect();
        middleY.value = box.top + box.height / 2;
      } else {
        ret = false;
      }
    }, 300);

    return ret;
  });

  onUpdated(() => {
    let ret = true;
    if (draggable.value !== null) {
      // console.log('onUpdated - draggable.value: ', draggable.value);
      const box = draggable.value.getBoundingClientRect();
      middleY.value = box.top + box.height / 2;
    } else {
      ret = false;
    }

    return ret;
  });

  const itemDragStart = () => {
    draggingItem.value = item.value;
    currentDropZoneId.value = dropZoneId.value;
    isDragging.value = true;
  };

  const itemDragEnd = () => {
    draggingItem.value = {};
  };

  const itemDragOver = dragdelay((e) => {
    hidePlaceholder();
    showPlaceholder(item.value.id);

    if (item.value.id === draggingItem.value.id) {
      return;
    }

    if (currentDropZoneId.value !== dropZoneId.value) {
      currentDropZoneId.value = dropZoneId.value;
    }

    hidePlaceholder();
    showPlaceholder(item.value.id);

    const offset = middleY.value - e.clientY;

    context.emit('itemDragOver', {
      position: offset > 0 ? position.value : position.value + 1,
    });
  }, 50);

  const transitionStart = () => {
    transitioning = false;
  };

  const transitionEnd = () => {
    transitioning = false;
  };

  watch(draggingItem, () => {
    console.log('DRAGGINGITEM', draggingItem);
    if (draggingItem.value.id) {
      return;
    }
    isDragging.value = false;

    hidePlaceholder();
  });

  return {
    draggable,
    isDragging,
    itemDragStart,
    itemDragOver,
    itemDragEnd,
    transitionStart,
    transitionEnd,
  };
};

export { useDraggableContainer, useDraggableItem };
