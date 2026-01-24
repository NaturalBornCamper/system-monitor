# System Monitor Display

## `setStatus` (visual status badge)

The UI shows a small status badge in the top‑right. It’s used for quick on‑screen diagnostics when you don’t have the console open.

### What it does
- `setStatus('ok', '')` hides the badge
- `setStatus('warn', '...')` shows a **warning** badge (auto‑hides after 10s)
- `setStatus('error', '...')` shows an **error** badge (stays until cleared)

### How to use it (from DevTools console)
```js
setStatus('warn', 'BAD DATA cpu-load=NaN');
setStatus('error', 'DISCONNECTED');
setStatus('ok', '');
```

### When it’s triggered automatically
- **BAD JSON**: incoming message could not be parsed even after sanitizing
- **BAD DATA <id>=<value>**: a sensor value is `NaN`/`Infinity` and the UI falls back to the last known good value
- **DISCONNECTED**: websocket error or close
