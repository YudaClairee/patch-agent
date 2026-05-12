# Logout Workflow

Sumber kontrak: `apps/frontend/markdown/api_contract.md`

## Endpoint

- Method: `POST`
- Path: `/auth/logout`
- Owner: Stream 1
- Efek backend: membersihkan auth cookie httpOnly.
- Catatan frontend: semua request auth memakai `credentials: "include"` melalui `fetchJson`.

## Alur UI

1. User menekan tombol `Log out` di `AppShell`.
2. Tombol masuk state `loading`, disabled, dan label berubah menjadi `Logging out`.
3. Frontend memanggil `patchApi.logout()`.
4. `patchApi.logout()` mengirim `POST /auth/logout` dengan cookie browser.
5. Jika backend sukses membersihkan cookie, frontend menjalankan `queryClient.clear()`.
6. User diarahkan ke route `/login`.
7. Jika backend membalas `401`, frontend tetap membersihkan cache dan redirect ke `/login` karena sesi sudah tidak valid.
8. Jika request gagal karena error lain, pesan error tampil inline dan tombol bisa dipakai ulang.

## State Handling

- `idle`: tombol aktif dengan label `Log out`.
- `loading`: tombol disabled dengan label `Logging out`.
- `error`: pesan error muncul di header shell, lalu user dapat mencoba ulang.

## File Implementasi

- `apps/frontend/src/api-contract.ts`
- `apps/frontend/src/sections/app-shell.tsx`
