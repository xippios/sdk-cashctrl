- A write whose answer is not JSON raises `ValidationError` with core's text, which names
  why after `is not JSON`, as in `cashctrl: response from /journal/create.json is not JSON:
  Expecting value at line 1 column 1 (char 0)`, where the text of 0.4.0 ended at
  `is not JSON`. The text changed with 0.5.0, whose notes left it out, and the class, `raw`
  and `source` are unchanged. (https://github.com/xippios/sdk-cashctrl/issues/131)
