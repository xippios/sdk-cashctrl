- A server bound with `--org` refuses a call that still names `org`, before the tool runs,
  where it ran the tool for the bound organisation: `error: InvalidRequestError: org: Not
  an argument of this tool; it takes ...`, naming the arguments the tool takes. A client of
  a bound server leaves `org` out, as the tools' schemas already said.
  (https://github.com/xippios/sdk-core/issues/84,
  https://github.com/xippios/sdk-cashctrl/issues/61)
