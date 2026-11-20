- `.copier-answers.yml` records two answers of sdk-template v0.4.0 ahead of its adoption:
  `write_server: true` and `tenant_param: org`, the shape the package has by hand today.
  The adoption then renders the write server, the organisations' registry and the live
  run's key from them, and nothing a caller uses changes here.
  (https://github.com/xippios/sdk-cashctrl/issues/105)
