Every code snippet can be executed in the browser dev console
while the UMC (http://ip/univention/management/) is open.

Note: The snippets are not isolated as they add variables to the global window object for easier fiddling.
You may want to refresh the page between snippets.


# Dojo - module definition and loading - `require`, `define` and `declare`

## `define`
TLDR: defines modules that can be imported in `define()` or `require()` calls.

Dojo uses the [Asynchronous Module Definition (AMD)](https://github.com/amdjs/amdjs-api/wiki/AMD) API
for defining modules.

Here is an example from `ucs/management/univention-web/js/widgets/ContainerWidget.js`:

```js
// ucs/management/univention-web/js/widgets/ContainerWidget.js
define(
    // list of dependencies
    [
	"dojo/_base/declare",
        "dojo/dom-class",
        "dijit/_WidgetBase",
        "dijit/_Container"
    ],
    // factory; in this case a function that has the loaded dependencies as parameters
    function(declare, domClass, _WidgetBase, _Container) {
      // The return value of the factory is the value of the module.
      // In this case a class declared with `declare`.
      return declare("umc.widgets.ContainerWidget", [_WidgetBase, _Container], {
          // [...]
      });
    }
);
```

## require
TLDR: import modules

`require` can be used to import modules.
Fundamentally it has the same syntax as `define`.

```js
require(
    // list of modules to import
    [
        'umc/widgets/ContainerWidget'
    ],
    // callback with dependencies as parameters
    function(ContainerWidget) {
        console.log('In callback of `require`');
        console.log('ContainerWidget module: ', ContainerWidget);
        // do stuff here
    }
)
```

If you are sure the module is already loaded you can just supply a string as argument and the return value
will be the module. Although this should only be used for debugging in the browser dev console.
In the source code, always specify your dependencies and work in the `define`, `require` callbacks.

```js
require(['dojox/fx'])
// run these lines seperately to give 'dojox/fx' time to be loaded
fx = require('dojox/fx');
// {anim: ƒ, animateProperty: ƒ, fadeTo: ƒ, fadeIn: ƒ, fadeOut: ƒ,}
```

If the module hasn't been loaded yet, you will get an error.
```js
fx = require('dojox/fx');
// Uncaught Error: undefinedModule
```

## declare

TLDR: declare Dojo classes.

`declare` allows the creation of classes with object-oriented concepts like inheritance.
It was created before the javascript `class` keyword existed.

# Dojo Widgets

## Prelude 1: `this.inherited(arguments)`

`this.inherited(arguments)` is the super call of Dojo classes
created with `declare`. The call will invoke the
same function of the parent class.

Generally `this.inherited(arguments)` should be called at the beginning or end of each lifecycle function,
the only exception being `constructor()` which is called regardless and calling
`this.inherited(arguments)` in `constructor` can cause errors.

```js
require([
    'dojo/_base/declare',
    'dijit/_WidgetBase',
], function(declare, _WidgetBase) {
    MyWidget = declare("MyWidget", [_WidgetBase], {
        buildRendering: function() {
            console.log(this.domNode);
        },
    });
});

new MyWidget({});
// logs `null` since `buildRendering` of `_WidgetBase` would normally
// create `this.domNode` but `this.inherited(arguments)` was not called.

require([
  'dojo/_base/declare',
  'dijit/_WidgetBase',
], function(declare, _WidgetBase) {
  MyWidget = declare("MyWidget", [_WidgetBase], {
    buildRendering: function() {
        this.inherited(arguments);
        console.log(this.domNode);
    },
  });
});

new MyWidget({});
// logs `<div id="MyWidget_1" widgetid="MyWidget_1"></div>
```

`this.inherited(arguments)` is not limited to lifecycle functions.

```js
require([
    'dojo/_base/declare',
    'dijit/_WidgetBase',
], function(declare, _WidgetBase) {
    MyWidget = declare("MyWidget", [_WidgetBase], {
        foo: function() {
            console.log("MyWidget::foo()");
        }
    });

    MyWidget2 = declare("MyWidget2", [MyWidget], {
        foo: function() {
            console.log("MyWidget2::foo()");
            console.log("MyWidget2: calling `this.inherited(arguments);")
            this.inherited(arguments);
        }
    });
});

new MyWidget2({}).foo();
```

## Prelude 2: setters and getters for widget properties

Properties of widgets can have corresponding setter and getter functions.
The syntax is `_setXXXAttr`, `_getXXXAttr`, where `XXX` is the name of the property capitalized.
For a property with the name `myProp`, the setter and getter functions are `_setMyPropAttr` and `_getMyPropAttr`
respectively.

One common use case is to use the setter function to update DOM nodes of the widget.

```js
require([
    'dojo/_base/declare',
    'dijit/_WidgetBase',
], function(declare, _WidgetBase) {
    MyWidget = declare("MyWidget", [_WidgetBase], {
        someString: 'some string',

        _setSomeStringAttr: function(someString) {
            this.domNode.innerText = someString;
            // important!  Call `this._set('someString', value)` with the final value,
            // or `this.someString` is not updated.
            this._set('someString', someString);
        }
    });
});

w = new MyWidget({});
w.domNode;
```

`_setXXXAttr` and `_getXXXAttr` should not be called directly. Rather the generic `set` and `get` methods should be
used which will call the setter and getter functions.

```js
w.set('someString', 'new string');
w.get('someString');

w.domNode;
```

Generally it is safer to always use `set` and `get` when working with properties of widget instances.
If a property has a setter function defined, and you just assign a value to the property,
the setter will not be called.

```js
// This will NOT cause `_setSomeStringAttr` to be called and the widget probably won't work as expected.
w.someString = 'foo';
w.domNode;
```

Setters and getters don't actually have to be functions.
[There are some shorthands for some use cases](https://dojotoolkit.org/reference-guide/1.10/quickstart/writingWidgets.html#mapping-widget-attributes-to-domnode-attributes).

```js
require([
    'dojo/_base/declare',
    'dijit/_WidgetBase',
    'put-selector/put',
], function(declare, _WidgetBase, put) {
    MyWidget = declare("MyWidget", [_WidgetBase], {

        buildRendering: function() {
            this.inherited(arguments);

            this.imgNode = put(this.domNode, 'img');
        },

        img: '/path',

        _setImgAttr: { node: 'imgNode', type: 'attribute', attribute: 'src' },
    });
});

w = new MyWidget({});
w.domNode;
```



## Lifecycle

```js
require([
    'dojo/_base/declare',
    'dojo/_base/lang',
    'dijit/_WidgetBase',
    'dojo/on',
    'put-selector/put'
], function(declare, lang, _WidgetBase, on, put) {
    MyWidget = declare("MyWidget", [_WidgetBase], {

        someArray: null,

        someNumber: 0,

        constructor: function() {
            console.log('Lifecycle function: "constructor"');

            // Here you can initialize properties with values.
            // This is important for properties that hold reference types.
            this.array = [1, 2];
        },

        postMixInProperties: function() {
          console.log('Lifecycle function: "postMixInProperties"');
          this.inherited(arguments);

          // When creating a widget instance, the caller can provide
          // values for properties:
          //
          // var myWidget = new MyWidget({
          //   someNumber: 50,
          // });
          //
          // In this function you can adjust properties before
          // the widget will be rendered in the next lifecycle function.
          //
          this.someNumber = Math.max(this.someNumber, 42);
        },

        buildRendering: function() {
            console.log('Lifecycle function: "buildRendering"');
            this.inherited(arguments);

            // In this function you can create the DOM node for this
            // widget.
            //
            // The root node is called `domNode` which is created in `_WidgetBase`.

            this.counterNode = put(this.domNode, 'div', this.someNumber);
        },

        // Not a specific lifecycle function but part of the lifecycle:
        // After `buildRendering` and before `postCreate`
        // all `_setXXXAttr` functions are called,
        // but only if they were provided as constructor parameter
        // or are none falsy.
        // See "## setters called during lifecycle only for none falsy values"
        // for a more detailed explanation.
        _setSomeNumberAttr: function(someNumber) {
            console.log("_setSomeNumberAttr(): ", someNumber);

            this.counterNode.innerText = someNumber;
            this._set('someNumber', someNumber);
        },

        postCreate: function() {
            console.log('Lifecycle function: "postCreate"');
            this.inherited(arguments);

            // In this function the DOM node is rendered and
            // you can use this function to setup behaviour of the widget.

            // e.g. adding listeners
            on(this.domNode, 'click', lang.hitch(this, function() {
                this.set('someNumber', this.someNumber + 1);
            }));

            // Note that at this point the DOM node may not be attached to the DOM yet
            // so sizing related functionality can't be done here.
            console.log("The size of this widget: ", this.domNode.getBoundingClientRect());
        },

        startup: function() {
            console.log('Lifecycle function: "startup"');

            // At this point the DOM node of the widget `this.domNode` is
            // in the dom and you can do sizing related functionality.

            console.log("The size of this widget: ", this.domNode.getBoundingClientRect());
        },

        destroy: function() {
            console.log('Lifecycle function: "destroy"');
            this.inherited(arguments);
        }
    });
});

container = new umc.widgets.ContainerWidget({
    style: "position: fixed; inset: 0; background: var(--bgc-content-body); z-index: 1000;"
});
document.body.appendChild(container.domNode);
container.startup();

// Create a widget instance with the `new` keyword.
// You can an object to set values for widget properties.
w = new MyWidget({
    someNumber: 10,
});
container.addChild(w);
```


# Stumbling blocks

## Initializing properties with reference types, outside of `constructor` lifecycle method

When you want a property of a widget to hold a reference type (e.g. arrays, Date, etc...)
you have to initialize it in the `constructor()` lifecycle function or the property value will
be shared across widget instances. Only [primitive types](https://developer.mozilla.org/en-US/docs/Glossary/Primitive)
can be initialized directly when declaring the property.

```js
require([
    'dojo/_base/declare',
    'dijit/_WidgetBase',
    'umc/widgets/Text'
], function(declare, _WidgetBase, Text) {
    MyWidget = declare("MyWidget", [_WidgetBase], {
        sharedArray: [],

        localArray: null,

        primitive: 'some initial string',

        constructor: function() {
            this.localArray = [];
        }
    });
});

w1 = new MyWidget({});
w2 = new MyWidget({});

console.log('w1 - shared array: ', w1.sharedArray);
console.log('w2 - shared array: ', w2.sharedArray);

console.log('w1 - local  array: ', w1.sharedArray);
console.log('w2 - local  array: ', w2.sharedArray);

console.log('w1 - primitive   : ', w1.primitive);
console.log('w2 - primitive   : ', w2.primitive);

console.log("# w1.sharedArray.push('val from w1');");
console.log("# w1.localArray.push('val from w1');");
console.log("# w2.sharedArray.push('val from w2');");
console.log("# w2.localArray.push('val from w2');");
console.log("# w1.primitive = 'new string for w1';");
console.log("# w2.primitive = 'new string for w2';");
w1.sharedArray.push('val from w1');
w1.localArray.push('val from w1');
w2.sharedArray.push('val from w2');
w2.localArray.push('val from w2');
w1.primitive = 'new string for w1';
w2.primitive = 'new string for w2';

console.log('w1 - shared array: ', w1.sharedArray);
console.log('w2 - shared array: ', w2.sharedArray);

console.log('w1 - local  array: ', w1.localArray);
console.log('w2 - local  array: ', w2.localArray);

console.log('w1 - primitive   : ', w1.primitive);
console.log('w2 - primitive   : ', w2.primitive);
```

## setters not called during lifecycle for falsy values

One stumbling block and potential annoyance is that
the setter functions (`_setXXXAttr`) are not called
during the creation lifecycle under certain circumstances.

If a properties initial value (including `postMixInProperties` step)
is falsy ( `false`, `0`, `null`, `undefined`, `''` (empty string), `NaN`),
the corresponding setter will not be called.


```js
// Note: the following snipped excludes `this._set('xxx', value)` in the setters only for brevity.
// You have to call it normally.

require([
    'dojo/_base/declare',
    'dijit/_WidgetBase',
], function(declare, _WidgetBase) {
    MyWidget = declare("MyWidget", [_WidgetBase], {

        zeroProp: 0,
        _setZeroPropAttr: function(value) {
            console.log('_setZeroPropAttr: ', value);
        },

        falseProp: false,
        _setFalsePropAttr: function(value) {
            console.log('_setFalsePropAttr: ', value);
        },

        nanProp: NaN,
        _setNanPropAttr: function(value) {
            console.log('_setNanPropAttr: ', value);
        },

        nullProp: null,
        _setNullPropAttr: function(value) {
            console.log('_setNullPropAttr: ', value);
        },

        undefinedProp: undefined,
        _setUndefinedPropAttr: function(value) {
            console.log('_setUndefinedPropAttr: ', value);
        },

        emptyStringProp: '',
        _setEmptyStringPropAttr: function(value) {
            console.log('_setEmptyStringPropAttr: ', value);
        },

        madeFalsyByPostMixInPropertiesProp: true,
        _setMadeFalsyByPostMixInPropertiesPropAttr: function(value) {
            console.log('_setMadeFalsyByPostMixInPropertiesPropAttr: ', value);
        },

        postMixInProperties: function() {
            this.inherited(arguments);
            this.madeFalsyByPostMixInPropertiesProp = false;
        },
    });
});

w = new MyWidget({});
// None of the setters will be called
```


Contrary, if a property is specified when creating the widget,
setters will always be called even if the value is falsy.

```js
w = new MyWidget({
    zeroProp: 0,
    falseProp: false,
    nanProp: NaN,
    nullProp: null,
    undefinedProp: undefined,
    emptyStringProp: '',
    madeFalsyByPostMixInPropertiesProp: false,
});

// Every setter is called.
```


That means that you can't solely rely on your setters
to generate the correct initial DOM state.
You have to incorporate (duplicate) that logic into
`buildRendering` if the initial value of your prop is falsy.

```js
require([
    'dojo/_base/declare',
    'dijit/_WidgetBase',
    'put-selector/put'
], function(declare, _WidgetBase, put) {
    MyWidget = declare("MyWidget", [_WidgetBase], {

        value: 0,
        _setValueAttr: function(value) {
            this.valueNode.innerHTML = this.value;
            this._set('value', value);
        },

        buildRendering: function() {
            this.inherited(arguments);

            this.valueNode = put('div#value');
            put(this.domNode, 'div $ +', 'Value is:', this.valueNode);

            // uncomment this line for the correct initial state
            // this.set('value', 0);
        },
    });
});

w = new MyWidget({});
w.domNode

// The div with id 'value' is empty instead of containing '0'
/*
<div id="MyWidget_24" widgetid="MyWidget_24">
  <div>Value is:</div>
  <div id="value"></div>
</div>
 */
```

The `div` with `id="value"` is empty instead of containing `0`.
Either don't rely on setters for the correct initial state of falsy values
or call `this.set('prop', value)` manually in `buildRendering` for falsy
initial values.
