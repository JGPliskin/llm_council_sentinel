# Debugging White Screen (Frontend Crash)

Please follow these steps to help identify the error:

1.  **Open Developer Tools**:
    *   Key: `F12` or `Ctrl+Shift+I` (Windows).
    *   Go to the **Console** tab.
2.  **Refresh the Page**:
    *   Look for red error messages.
    *   Common errors:
        *   `Uncaught SyntaxError`: Indicates a typo in the code (likely my recent edit).
        *   `Uncaught TypeError: Cannot read properties of undefined`: Data structure mismatch.
        *   `Minified React error`: Core React crash.
3.  **Check Backend Output**:
    *   Is the backend running without error?
    *   Did the `/api/councilors` or `/api/conversations` request succeed (Network tab)?

**Hypothesis**:
I suspect a syntax error in `Stage2.jsx` (mismatched braces during my last edit) or an initialization error in `ChatInterface.jsx` where it tries to read `active_councilor_ids` from a conversation that hasn't loaded yet.
