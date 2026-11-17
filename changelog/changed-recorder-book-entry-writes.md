- The fixture recorder records the three book entry writes on marked orders only: a
  create on orders marked `xippios-live`, and an update or a delete on an entry whose
  order is marked, which it reads before the write is sent.
  (https://github.com/xippios/sdk-cashctrl/issues/44)
