The Univention Directory Listener shutdown handling has been made signal-safe to avoid segmentation faults when terminating while embedded Python handler code is active.
