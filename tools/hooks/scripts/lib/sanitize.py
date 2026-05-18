#!/usr/bin/env python3
"""Sanitization utilities for telemetry strings.

Public API:
    sanitize_error(msg: str) -> str
    sanitize_cli(cmd: str) -> str

Both truncate to safe lengths and strip credentials, file paths, PII.
"""
from __future__ import annotations

import re

ERROR_MAX_LEN = 200
CLI_MAX_TOKENS = 3
CLI_MAX_LEN = 120

_CRED_PATTERNS = [
    re.compile(r"(?i)\b(ak|sk|pk|key|secret|password|token|credential|accesskey)\s*=\s*\S+"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-]+"),
]
_PATH_PATTERNS = [
    re.compile(r"/Users/[^/\s]+/"),
    re.compile(r"/home/[^/\s]+/"),
    re.compile(r"C:\\Users\\[^\\\s]+\\"),
]
_PII_PATTERNS = [
    re.compile(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),         # email
    re.compile(r"\b1[3-9]\d{9}\b"),                              # CN mobile
    re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),       # IPv4
    re.compile(r"\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b"),  # UUID
]


def sanitize_error(msg) -> str:
    if msg is None:
        return ""
    s = str(msg)[:ERROR_MAX_LEN * 4]  # work on a bounded prefix
    for pat in _CRED_PATTERNS:
        s = pat.sub(lambda m: m.group(0).split("=")[0] + "=***" if "=" in m.group(0) else "***", s)
    for pat in _PATH_PATTERNS:
        s = pat.sub("/<USER>/", s)
    for pat in _PII_PATTERNS:
        s = pat.sub("<REDACTED>", s)
    return s[:ERROR_MAX_LEN]


def sanitize_cli(cmd) -> str:
    """Keep only the first CLI_MAX_TOKENS shell-style tokens."""
    if cmd is None:
        return ""
    s = str(cmd).strip()[:CLI_MAX_LEN * 4]
    parts = s.split()
    return " ".join(parts[:CLI_MAX_TOKENS])[:CLI_MAX_LEN]


if __name__ == "__main__":
    # Self-tests, run manually with: python3 sanitize.py
    cases_err = [
        ("InvalidAccessKeyId: AccessKey ak=ABC123 not found",
         "InvalidAccessKeyId: AccessKey ak=*** not found"),
        ("Error reading /Users/alice/secret.pem",
         "Error reading /<USER>/secret.pem"),
        ("Send to user@example.com failed",
         "Send to <REDACTED> failed"),
        ("Connection to 192.168.1.1 timeout",
         "Connection to <REDACTED> timeout"),
    ]
    for input_, expected in cases_err:
        got = sanitize_error(input_)
        assert got == expected, f"sanitize_error({input_!r}) = {got!r}, expected {expected!r}"

    cases_cli = [
        ("aliyun ecs DescribeInstances --region cn-hangzhou", "aliyun ecs DescribeInstances"),
        ("aliyun oss ls", "aliyun oss ls"),
        ("aliyun", "aliyun"),
    ]
    for input_, expected in cases_cli:
        got = sanitize_cli(input_)
        assert got == expected, f"sanitize_cli({input_!r}) = {got!r}, expected {expected!r}"

    print("sanitize.py: all self-tests passed")
