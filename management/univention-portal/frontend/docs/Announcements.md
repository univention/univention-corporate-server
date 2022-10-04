# Announcements

## Creation, Modification, Deletion

#todo

## Customizing Background Color for Severity

CSS styles for the severity are defined as follows.

```css
&--info
background-color: var(--color-accent)

&--danger
background-color: var(--bgc-error)

&--success
background-color: var(--bgc-success)

&--warn
background-color: var(--bgc-warning)
```

They are using css `:root`-constants, defined in `/frontend/public/data/(light|dark).css` and can be altered there, in case they need to.

> NOTE: Please be aware, that these constants might be used elsewhere and that a change might cause unwanted side-effects!