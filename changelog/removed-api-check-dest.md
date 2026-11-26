- `xippios.cashctrl.api` no longer exports `check_dest`, the package's own check of a
  download's `dest`. Core's `check_dest(dest, *, source=None)`, exported from
  `xippios.core`, takes its place, and the file tasks call it before their first request.
  (https://github.com/xippios/sdk-core/issues/481)
