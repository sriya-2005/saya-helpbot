# docs/

Drop your PDF manuals directly in this folder (no subfolders — the loader
only scans the top level of `docs/`).

Example:
```
docs/
├── reconx_manual.pdf
├── onboarding_guide.pdf
└── admin_settings.pdf
```

After adding, removing, or replacing PDFs here, call:
```
POST http://localhost:8000/reload
```
...to make the backend pick up the changes without restarting the server.

Notes:
- Scanned PDFs with no real text layer (i.e. just images of pages) won't
  produce any searchable text — they'd need OCR first, which this version
  doesn't do.
- Password-protected/corrupted PDFs are skipped automatically; check the
  server logs if a PDF you added doesn't show up in the chunk count.
