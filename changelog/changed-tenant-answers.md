- `.copier-answers.yml` records three answers of sdk-template v0.4.0 ahead of its adoption:
  `write_server: true`, `tenant_param: org` and `has_reference_data: false`. The first two
  are the shape the package has by hand today: the adoption then renders the two servers'
  entry points, their `--org` binding, the tests' strip of other organisations' keys and the
  live run's key from them. The third has the adoption drop the reference scaffold, since
  the package packages no list. Nothing a caller uses changes here.
  (https://github.com/xippios/sdk-cashctrl/issues/105)
