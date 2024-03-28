# Widgets

## `require`, `define` and `declare`

### `define`
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

### require
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
        // do stuff here
    }
)
```

If you are sure the module is already loaded you can just supply a string as argument and the return value
will be the module. If the module hasn't been loaded yet, you will get an error.

```js
fx = require('dojox/fx');
// Uncaught Error: undefinedModule
require(['dojo/fx'])
fx = require('dojox/fx');
// {anim: ƒ, animateProperty: ƒ, fadeTo: ƒ, fadeIn: ƒ, fadeOut: ƒ,}
```

### declare

TLDR: declare Dojo classes.

created before javascript `class` existed

like `class` it provides class based syntax, inheritence etc

also provides common functions like `inherited`TODO link to this.inherited





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
            // important!  Call `this._set('someString', value)` with the final value or
            // this.someString is not updated.
            this._set('someString', someString);
        }
    });
});

w = new MyWidget({});
```

`_setXXXAttr` and `_getXXXAttr` should not be called directly. Rather the generic `set` and `get` methods should be
used which will call the setter and getter functions.

```js
w.set('someString', 'new string');
w.get('someString');
```

Generally it is safer to always use `set` and `get` when working with properties of widget instances.
If a property has a setter function defined, and you just assign a value to the property,
the setter will not be called.

```js
// This will NOT cause `_setSomeStringAttr` to be called and the widget probably won't work as expected.
w.someString = 'foo';
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
console.log(w.domNode);
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
        // all `_setXXXAttr` functions are called.
        _setSomeNumberAttr: function(someNumber) {
            console.log("_setSomeNumberAttr(): ", someNumber);

            this.counterNode.innerText = this.someNumber;
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

            // Note that at this point the DOM node is not attached to the DOM yet
            // so sizing related functionality can't be done here.
            console.log("The size of this widget: ", this.domNode.getBoundingClientRect());
        },
    });
});

w = new MyWidget({});
```


# Caveats

## Initializing properties with reference types outside of `constructor` lifecycle method


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

## setters called during lifecycle only for none null values





# Debugging

## MyWidget is not a constructor

Some syntax error
