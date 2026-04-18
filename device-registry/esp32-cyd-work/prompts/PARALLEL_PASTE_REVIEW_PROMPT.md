# Parallel Paste Review Prompt

Goal: every time PowerShell code is pasted, inspect for:
- wrong working directory
- BOM/encoding risks
- destructive commands
- missing includes/declarations
- build/upload prerequisites
- mismatched COM port
- hidden dependency issues

Output format:
1. Safe to run / risky
2. Main risks
3. Minimal corrections
4. Expected result
