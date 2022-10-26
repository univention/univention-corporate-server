This should work:

```
npm install
tsc --build .
```

When using the resulting udm.js (say by using the test.js), you may want to do this:

`node --max-http-header-size=150000 test.js`
