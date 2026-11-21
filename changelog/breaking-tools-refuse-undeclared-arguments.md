- A tool of either server refuses an argument that it does not declare, before it runs,
  and its error names the arguments the tool takes, where the argument was dropped and the
  tool ran without it. So a server bound with `--org` refuses a call that still names
  `org`, where it ran the tool for the bound organisation, and a client leaves out what
  the tool's schema does not list. (https://github.com/xippios/sdk-core/issues/84,
  https://github.com/xippios/sdk-cashctrl/issues/61)
