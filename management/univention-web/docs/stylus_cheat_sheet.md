# Stylus

From a birds eye view stylus is fairly similar to Sass or Less if you are familiar with them.

Stylus is a language that is compiled into CSS. It offers concepts like reusable functions, iterations, conditions
and more.

The following examples show basic concepts of stylus. For a full overview please read the [stylus docs](https://stylus-lang.com/docs/).

## Nesting and parent reference

In CSS, if you have a parent with multiple children, you have to
write multiple blocks (rules):

```css
.parent .child-1 {
    background: red;
}

.parent .child-2 {
    background: green;
}
```

In stylus, we can simplify this with nesting:

```stylus
.parent
  .child-1
    background: red

  .child-2
    background: green
```

We can also reference the parent itself with the `&` character which allows grouping all styling
related to a class in one block:

```stylus
.element
  background: red

  &:hover
    background: green

  &--small
    transform: scale(0.5)
```

which will compile to:

```css
.element {
    background: red;
}

.element:hover {
    background: green;
}

.element--small {
    transform: scale(0.5);
}
```

## Stumbling blocks

### Mixed whitespace causes unexpected output
when writing stylus files make sure that you use the same whitespace for indentation.
In other words don't mix spaces and tabs.

Stylus might compile without error but the result will probably be not what you expect.

Consider this stylus snippet:
```stylus
.foo
  color: black
  &.bar
      color: white
```

With the expected compiled output:
```css
.foo {
  color: black;
}

.foo.bar {
  color: white;
}
```

But if the snippet uses mixed tabs and spaces:
```text
# '>' represents a tab
# '_' represents a space

.foo
>   color: black
____&.bar
>   >   color: white
```

stylus will compile without error but the output will be:
```css
.foo {
  color: black;
}

.bar {
  color: white;
}
```

We lost the parent - child relationship between `.foo` and `.bar`.
