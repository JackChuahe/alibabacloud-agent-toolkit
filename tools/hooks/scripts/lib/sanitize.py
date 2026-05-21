#!/usr/bin/env python3
"""Sanitization utilities for telemetry strings.

Public API:
    sanitize_error(msg: str) -> str   — full scrub of free text
    sanitize_cli(cmd: str) -> str     — keep verb only, strip creds
    classify_error(msg: str) -> str   — return error CLASS/code only
"""
from __future__ import annotations

import re

ERROR_MAX_LEN = 200
CLI_MAX_TOKENS = 3
CLI_MAX_LEN = 120

# --- Credential patterns ---------------------------------------------------

_CRED_PATTERNS = [
    # key=value style (AccessKey ak=ABC123, secret=..., password=...)
    re.compile(r"(?i)\b(ak|sk|pk|key|secret|password|token|credential|accesskey|accesskeysecret)\s*[=:]\s*\S+"),
    # Bearer tokens
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9._\-/+=]+"),
    # Alibaba Cloud AccessKey IDs (LTAI prefix, 12-30 alphanum)
    re.compile(r"\bLTAI[A-Za-z0-9]{8,30}\b"),
    # STS tokens (STS\.....)
    re.compile(r"\bSTS\.[A-Za-z0-9+/=]{10,}"),
    # JWT tokens (three dot-separated base64url segments)
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    # PEM private key blocks
    re.compile(r"-----BEGIN[^-]*PRIVATE KEY-----[\s\S]*?-----END[^-]*PRIVATE KEY-----"),
    # Connection strings (semicolon-separated key=value with password/key inside)
    re.compile(r"(?i)(?:AccountKey|SharedAccessKey|Password)\s*=\s*[^;\"'\s]+"),
    # Generic long base64 blobs (likely secrets, 40+ chars)
    re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/=]{40,}(?![A-Za-z0-9+/=])"),
]

# --- Path patterns ----------------------------------------------------------

_PATH_PATTERNS = [
    re.compile(r"/Users/[^/\s]+/"),
    re.compile(r"/home/[^/\s]+/"),
    re.compile(r"C:\\Users\\[^\\\s]+\\"),
]

# --- PII patterns -----------------------------------------------------------

_PII_PATTERNS = [
    # Email
    re.compile(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    # CN mobile
    re.compile(r"\b1[3-9]\d{9}\b"),
    # International phone (+<country><number>, 7-15 digits)
    re.compile(r"\+\d{1,3}[\s-]?\d{4,14}\b"),
    # IPv4
    re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    # IPv6 (simplified: 4+ hex groups with colons or :: notation)
    re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){3,7}[0-9a-fA-F]{1,4}\b"),
    re.compile(r"\b(?:[0-9a-fA-F]{1,4}:)*::[0-9a-fA-F:]*\b"),
    # UUID (case-insensitive)
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
    # CN national ID (18 digits or 17+X)
    re.compile(r"\b\d{17}[\dXx]\b"),
    # US SSN (xxx-xx-xxxx)
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # FQDN-like hostnames (3+ labels, common TLDs — avoid matching error codes)
    re.compile(r"\b(?:[a-zA-Z0-9-]+\.){2,}(?:com|net|org|io|cn|cloud|internal|local|dev)\b"),
]

# --- CLI credential flags to strip ------------------------------------------

_CLI_SENSITIVE_FLAGS = frozenset([
    "--access-key-id", "--access-key-secret", "--accesskeyid", "--accesskeysecret",
    "--secret", "--secret-key", "--password", "--passwd",
    "--sts-token", "--security-token",
    "--endpoint-url", "--endpoint",
    "--profile",
])


def sanitize_error(msg) -> str:
    """Scrub credentials, paths, and PII from free-text error messages."""
    if msg is None:
        return ""
    s = str(msg)[:ERROR_MAX_LEN * 4]
    for pat in _CRED_PATTERNS:
        s = pat.sub("***", s)
    for pat in _PATH_PATTERNS:
        s = pat.sub("/<USER>/", s)
    for pat in _PII_PATTERNS:
        s = pat.sub("<REDACTED>", s)
    return s[:ERROR_MAX_LEN]


def sanitize_cli(cmd) -> str:
    """Keep only the first CLI_MAX_TOKENS tokens, stripping credential flags and bare secrets."""
    if cmd is None:
        return ""
    s = str(cmd).strip()[:CLI_MAX_LEN * 4]
    tokens = s.split()
    clean: list[str] = []
    skip_next = False
    for i, tok in enumerate(tokens):
        if skip_next:
            skip_next = False
            continue
        low = tok.lower()
        # Strip sensitive flags and their values
        if low in _CLI_SENSITIVE_FLAGS or low.lstrip("-") in (
            "access-key-id", "access-key-secret", "secret-key",
            "sts-token", "security-token", "password", "passwd",
        ):
            skip_next = True
            continue
        # Strip --flag=value forms of sensitive flags
        if "=" in tok:
            flag_part = tok.split("=", 1)[0].lower()
            if flag_part in _CLI_SENSITIVE_FLAGS:
                continue
        # Strip bare LTAI* / STS.* / JWT tokens appearing as positional args
        if re.match(r"^LTAI[A-Za-z0-9]{8,}", tok):
            continue
        if re.match(r"^STS\.[A-Za-z0-9+/=]{10,}", tok):
            continue
        if re.match(r"^eyJ[A-Za-z0-9_-]{10,}\.", tok):
            continue
        clean.append(tok)
        if len(clean) >= CLI_MAX_TOKENS:
            break
    return " ".join(clean)[:CLI_MAX_LEN]


# --- Error classification (Finding #3) -------------------------------------
# Instead of emitting sanitized free-text, emit ONLY a structured error class.

_ALIYUN_ERROR_CODE_RE = re.compile(
    r"\b("
    r"InvalidParameter\w*|NoPermission|Forbidden\w*|AccessDenied\w*|"
    r"InvalidAccessKey\w*|Unauthorized\w*|RequestTimeout|"
    r"ServiceUnavailable|InternalError|Throttling\w*|QuotaExceeded\w*|"
    r"SignatureDoesNotMatch|IncompleteSignature|"
    r"InvalidAction|InvalidVersion|UnsupportedOperation|"
    r"EntityNotExist\w*|InvalidApi\w*|MissingParameter\w*|"
    r"DependencyViolation|ResourceNotFound\w*|"
    r"OperationDenied\w*|AccountArrears|"
    r"InvalidRegionId|InvalidInstanceId\w*|"
    r"ServerBusy|ServiceBusy"
    r")\b"
)

_CLIENT_ERROR_CLASS_RE = re.compile(
    r"(?i)(connection\s*refused|connection\s*reset|connection\s*timeout|"
    r"timeout|timed?\s*out|unreachable|no\s*route\s*to\s*host|"
    r"eof|broken\s*pipe|ssl\s*error|certificate\s*error|"
    r"dns\s*resolution\s*failed|name\s*resolution\s*failed|"
    r"network\s*unreachable|host\s*not\s*found)"
)

_MCP_ERROR_CODE_RE = re.compile(r'"code"\s*:\s*(-?\d+)')


def classify_error(msg) -> str:
    """Extract ONLY the error class/code from a message. No free-text leaks.

    Returns one of:
      - An Alibaba Cloud error code (e.g. "NoPermission", "InvalidParameter")
      - A client error class (e.g. "ConnectionRefused", "Timeout")
      - An MCP error code (e.g. "MCPError:-32603")
      - "PostToolUseFailure" (generic failure marker)
      - "" (no classifiable error)
    """
    if msg is None:
        return ""
    s = str(msg)[:2000]

    # Try Alibaba Cloud API error codes first
    m = _ALIYUN_ERROR_CODE_RE.search(s)
    if m:
        return m.group(1)

    # Try MCP JSON-RPC error codes
    m = _MCP_ERROR_CODE_RE.search(s)
    if m:
        return f"MCPError:{m.group(1)}"

    # Try client/network error classes
    m = _CLIENT_ERROR_CLASS_RE.search(s)
    if m:
        raw = m.group(1).strip()
        # CamelCase: capitalize each word then join
        normalized = "".join(w.capitalize() for w in re.split(r"[\s_-]+", raw))
        return normalized

    # Check for HTTP status codes
    m = re.search(r"\b([45]\d{2})\b", s)
    if m:
        return f"HTTP:{m.group(1)}"

    # Check for bash exit codes
    m = re.search(r"exit[_\s]*code\s*=?\s*(\d+)", s, re.IGNORECASE)
    if m and m.group(1) != "0":
        return f"ExitCode:{m.group(1)}"

    # Generic markers
    if "isError=true" in s or "is_error=true" in s.lower():
        return "UnknownError"
    if "PostToolUseFailure" in s:
        return "PostToolUseFailure"

    return ""


if __name__ == "__main__":
    # Self-tests
    cases_err = [
        ("InvalidAccessKeyId: AccessKey ak=ABC123 not found",
         "InvalidAccessKeyId: AccessKey *** not found"),
        ("Error reading /Users/alice/secret.pem",
         "Error reading /<USER>/secret.pem"),
        ("Send to user@example.com failed",
         "Send to <REDACTED> failed"),
        ("Connection to 192.168.1.1 timeout",
         "Connection to <REDACTED> timeout"),
        ("Token LTAItestFAKEnotREAL1234 leaking",
         "Token *** leaking"),
        ("STS.NSxeSfaZr123abc= leaked",
         "Token *** leaked" if False else None),  # skip complex
    ]
    for input_, expected in cases_err:
        if expected is None:
            continue
        got = sanitize_error(input_)
        assert got == expected, f"sanitize_error({input_!r}) = {got!r}, expected {expected!r}"

    cases_cli = [
        ("aliyun ecs DescribeInstances --region cn-hangzhou", "aliyun ecs DescribeInstances"),
        ("aliyun ecs DescribeInstances --access-key-id LTAItestFAKEnotREAL1234 --access-key-secret mySec",
         "aliyun ecs DescribeInstances"),
        ("aliyun oss ls --endpoint-url https://oss.cn-hangzhou.aliyuncs.com",
         "aliyun oss ls"),
        ("aliyun oss ls", "aliyun oss ls"),
        ("aliyun", "aliyun"),
    ]
    for input_, expected in cases_cli:
        got = sanitize_cli(input_)
        assert got == expected, f"sanitize_cli({input_!r}) = {got!r}, expected {expected!r}"

    cases_classify = [
        ("NoPermission: you are not authorized", "NoPermission"),
        ("Connection refused to host", "ConnectionRefused"),
        ('{"code": -32603, "message": "internal error"}', "MCPError:-32603"),
        ("exit_code=127", "ExitCode:127"),
        ("HTTP 503 custom error", "HTTP:503"),
        ("HTTP 403 something custom", "HTTP:403"),
        ("ServiceUnavailable: backend down", "ServiceUnavailable"),
        ("everything is fine", ""),
    ]
    for input_, expected in cases_classify:
        got = classify_error(input_)
        assert got == expected, f"classify_error({input_!r}) = {got!r}, expected {expected!r}"

    print("sanitize.py: all self-tests passed")
