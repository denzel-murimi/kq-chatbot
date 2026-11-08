"""
Test the contextualization logic with a stubbed Groq client (no key/network).
Verifies: no-history passthrough, a real rewrite, error fallback, empty-output
fallback, and that only the recent history is used.

Run:  PYTHONPATH=. python scripts/try_contextualize.py
"""
from __future__ import annotations

import sys
import types

import app.contextualize as ctx


class _Resp:
    def __init__(self, content):
        msg = types.SimpleNamespace(content=content)
        self.choices = [types.SimpleNamespace(message=msg)]


class _FakeClient:
    """Returns a preset rewrite, or raises if told to."""
    def __init__(self, rewrite=None, raise_exc=False):
        self.rewrite = rewrite
        self.raise_exc = raise_exc
        self.last_user_content = None
        self.calls = 0

        parent = self
        class _Completions:
            def create(self, **kw):
                parent.calls += 1
                if parent.raise_exc:
                    raise RuntimeError("groq down")
                parent.last_user_content = kw["messages"][-1]["content"]
                return _Resp(parent.rewrite)
        self.chat = types.SimpleNamespace(completions=_Completions())


def use(client):
    ctx._client = lambda: client  # bypass the lru_cache'd real client


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL':4} {label}")
    return cond


def main():
    ok = True

    # 1. no history -> original, no model call
    c = _FakeClient(rewrite="SHOULD NOT BE USED")
    use(c)
    out = ctx.contextualize("where can I find that form?", [])
    ok &= check("no history returns original, no call", out == "where can I find that form?" and c.calls == 0)

    # 2. real follow-up -> uses the rewrite
    history = [
        {"role": "user", "text": "Can my son who's 7 travel alone?"},
        {"role": "bot", "text": "Yes. KQ requires children aged 5-14 to use the unaccompanied minor service and complete the Unaccompanied Minor Form."},
    ]
    c = _FakeClient(rewrite="Where can I find the Kenya Airways Unaccompanied Minor Form?")
    use(c)
    out = ctx.contextualize("where can I find that form?", history)
    ok &= check("follow-up is rewritten to standalone", out == "Where can I find the Kenya Airways Unaccompanied Minor Form?")
    ok &= check("history and latest message were sent to the model",
               "Unaccompanied Minor Form" in c.last_user_content and "where can I find that form?" in c.last_user_content)

    # 3. model error -> fall back to original
    c = _FakeClient(raise_exc=True)
    use(c)
    out = ctx.contextualize("where can I find that form?", history)
    ok &= check("model error falls back to original", out == "where can I find that form?")

    # 4. empty output -> fall back to original
    c = _FakeClient(rewrite="   ")
    use(c)
    out = ctx.contextualize("and the fee?", history)
    ok &= check("empty rewrite falls back to original", out == "and the fee?")

    # 5. only recent history used (MAX_HISTORY)
    long_history = [{"role": "user", "text": f"msg {i}"} for i in range(20)]
    c = _FakeClient(rewrite="ok")
    use(c)
    ctx.contextualize("latest", long_history)
    ok &= check("only the most recent turns are included",
               "msg 19" in c.last_user_content and "msg 0" not in c.last_user_content)

    print("\n" + ("ALL PASS" if ok else "SOME FAILED"))


if __name__ == "__main__":
    main()