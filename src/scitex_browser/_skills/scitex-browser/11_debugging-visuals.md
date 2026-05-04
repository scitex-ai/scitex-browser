---
description: |
  [TOPIC] Debugging Visuals
  [DETAILS] Debugging Visuals — see file body for details.
tags: [scitex-browser-debugging-visuals]
---

# Debugging Visuals

Inject CSS/JS overlays into a Playwright page so humans can follow what
the automation is doing. Both sync and async variants are provided; the
async ones run in the event-loop-friendly Playwright API.

## One-time injection

```python
await inject_visual_effects_async(page)
```

Call once per page (or after navigation). All later `show_*` helpers
depend on the injected script.

## Cursor / click

* `show_cursor_at(page, x, y)` — render a visible cursor dot at viewport coordinates
* `show_click_effect(page, x, y)` — ripple animation at coordinates

## Step banners

* `show_step(page, "Login")` — top-of-page banner for current step
* `show_test_result(page, passed=True)` — final PASS/FAIL banner

## Grid + element highlight

* `show_grid_async(page, step=100)` — overlay a pixel grid (debug layout)
* `highlight_element_async(page, selector)` — outline a selector

## Console capture

```python
logs = setup_console_interceptor(page)
# ... run test ...
rich = collect_console_logs_detailed(page)
print(format_logs_devtools_style(rich))
```

## Failure artifacts

`save_failure_artifacts(page, out_dir)` dumps screenshot + full HTML +
console trace. `create_failure_capture_fixture(...)` is the pytest
plug-in form.
