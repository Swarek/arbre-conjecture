# Source materials

This directory vendors the local source documents used by the research notes so
the repo remains reproducible without depending on `~/Downloads`.

## PDFs

| File | Source path at import time | SHA-256 |
| --- | --- | --- |
| `pdfs/Brucker_Osswald-1.pdf` | `/Users/mathisblanc/Downloads/Brucker_Osswald-1.pdf` | `3246d3608d89418aa76802f2a28e850a20101ff049438fd20f7fd210c979f66d` |
| `pdfs/Hsu-McConnel_PC-trees-1.pdf` | `/Users/mathisblanc/Downloads/Hsu-McConnel_PC-trees-1.pdf` | `adcd208572893597e57c4622bc120ac518a1f9b3cd60fc2f06d0c46dfd7c9f11` |
| `pdfs/Modules_PQ-tree-1.pdf` | `/Users/mathisblanc/Downloads/Modules_PQ-tree-1.pdf` | `28c425a3703194b64a02d7db057dc2b817ebfa67399771fb4c064c9d3799d212` |
| `pdfs/PC-Trees_vs._PQ-Trees__Hsu-2.pdf` | `/Users/mathisblanc/Downloads/PC-Trees_vs._PQ-Trees__Hsu-2.pdf` | `9047349a8810268eaa4bd11b9c0aee06036e1d4ad2daf874d3a1da90ecc2bcae` |
| `pdfs/Robinson_modules-1.pdf` | `/Users/mathisblanc/Downloads/Robinson_modules-1.pdf` | `7c681790e1fea4976020da721548b761a1c465974469c0e74487f2834f49ca80` |
| `pdfs/strongly-circular-sidma-1.pdf` | `/Users/mathisblanc/Downloads/strongly-circular-sidma-1.pdf` | `06984f6410e73a87539d0d90a201eb5e8e239d74842ad6fad7e998212784d230` |

## Screenshot

The screenshot path provided by the UI was a temporary file:

```text
/var/folders/yx/knynxqw926j197htt4wm7jhh0000gn/T/TemporaryItems/NSIRD_screencaptureui_YxIDQL/Screenshot 2026-05-22 at 10.55.03 PM.png
```

It is now vendored here:

| File | Source path at import time | SHA-256 |
| --- | --- | --- |
| `images/proposition_4_4_2026-05-22.png` | `/var/folders/yx/knynxqw926j197htt4wm7jhh0000gn/T/TemporaryItems/NSIRD_screencaptureui_YxIDQL/Screenshot 2026-05-22 at 10.55.03 PM.png` | `cef8d6fa5de1065658c45cb5b8072ac77957f9b21d117d4bb758e3bda9c66ad1` |
| `images/handwritten_block_gadget_2026-05-31.png` | `/var/folders/yx/knynxqw926j197htt4wm7jhh0000gn/T/TemporaryItems/NSIRD_screencaptureui_vBxMdn/Screenshot 2026-05-31 at 10.39.05 AM.png` | `79713da3d07776c4f0948d825f0ed1b4184006a9c6723bb2693b72c94e195876` |

The mathematical content shown in the screenshot, Proposition 4.4, is preserved
in `docs/source_notes.md` and covered by tests for
`passes_farthest_prop_4_4_condition`.

The 2026-05-31 handwritten screenshot is not a proof. It is summarized as an
ambiguous four-block gadget seed in
`docs/external_reviews/researcher_advances_2026-05-31.md`.
It is provenance only; the executable formalization lives in
`tools/pc_handwritten_gadget_probe.py` and the reproducible report is generated
by `make bench-handwritten-gadget`.
