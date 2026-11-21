- `xippios.cashctrl.params` and `xippios.cashctrl.enums` are gone: they held no list,
  `PACKAGED_LISTS` empty and no enumeration, since the package packages none, and no
  task, tool or route used them. A caller that imported either drops the import, and a
  value set upstream documents is a `Literal` type in `xippios.cashctrl.models`.
  (https://github.com/xippios/sdk-cashctrl/issues/111)
