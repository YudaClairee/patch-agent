import { Badge, Button, Card, FileRow, SectionHeading } from "@patch/ui";
import { CheckCircle2, XCircle } from "lucide-react";
import type { SetActiveProps } from "../wireframe-data";

export function DiffReview({ setActive }: SetActiveProps) {
  return (
    <div className="grid gap-5 xl:grid-cols-[320px_1fr]">
      <div className="space-y-5">
        <Card className="p-5">
          <SectionHeading title="Summary" />
          <p className="mt-4 text-base leading-6 tracking-[-0.006em] text-[var(--patch-text)]">
            P.A.T.C.H. menambahkan unit test login, memperbaiki sedikit response handling, dan menjalankan verifikasi.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            <Badge tone="inverse">pytest passed</Badge>
            <Badge tone="inverse">ruff passed</Badge>
          </div>
        </Card>
        <Card className="p-5">
          <SectionHeading title="Changed Files" />
          <div className="mt-5 space-y-3 text-sm">
            <FileRow path="tests/test_auth.py" additions="+82" deletions="-0" />
            <FileRow path="app/auth/routes.py" additions="+4" deletions="-1" />
          </div>
        </Card>
        <div className="grid gap-3">
          <Button onClick={() => setActive("pr")}>
            <CheckCircle2 size={15} />
            Approve & Create PR
          </Button>
          <Button variant="danger">
            <XCircle size={15} />
            Reject
          </Button>
        </div>
      </div>

      <Card surface="dark" className="overflow-hidden">
        <div className="border-b border-[var(--patch-dark-border)] px-5 py-4 text-sm font-semibold text-white">
          git diff / tests/test_auth.py
        </div>
        <pre className="h-[560px] overflow-auto bg-[var(--patch-ink)] p-5 text-xs leading-6 text-white">{`diff --git a/tests/test_auth.py b/tests/test_auth.py
new file mode 100644
index 0000000..a8f4c2b
--- /dev/null
+++ b/tests/test_auth.py
@@ -0,0 +1,82 @@
+import pytest
+from httpx import AsyncClient
+
+async def test_login_success(client: AsyncClient):
+    response = await client.post("/auth/login", json={
+        "email": "demo@patch.dev",
+        "password": "secret123"
+    })
+    assert response.status_code == 200
+    assert "access_token" in response.json()
+
+async def test_login_invalid_password(client: AsyncClient):
+    response = await client.post("/auth/login", json={
+        "email": "demo@patch.dev",
+        "password": "wrong-password"
+    })
+    assert response.status_code == 401
+    assert response.json()["detail"] == "Invalid credentials"
`}</pre>
      </Card>
    </div>
  );
}
