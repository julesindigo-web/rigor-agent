# Kajian, Riset, dan Audit Integrasi HRAS v20 dengan Kilo Code

**Tanggal kajian:** 29 Oktober 2026  
**Basis normatif:** HRAS `20.0.0-rc4`, status `CANDIDATE_NOT_PRODUCTION_READY`  
**Target integrasi:** Kilo Code generasi saat ini yang menggunakan Markdown agents/custom agents, `kilo.jsonc`, project rules, skills, dan slash-command workflows  
**Status delivery:** `PACKAGE_VALIDATED / KILO_RUNTIME_NOT_RUN / HRAS_PRODUCTION_NOT_READY`

## 1. Ringkasan keputusan

**HRAS dapat dikonfigurasi sebagai agent engineering yang disiplin di Kilo Code, tetapi spesifikasi HRAS v20 belum dapat dianggap sebagai autonomous production control plane hanya dengan dipasang sebagai prompt.**

Implementasi yang disiapkan memanfaatkan permukaan konfigurasi Kilo Code yang memang tersedia: satu primary agent `hras`, lima subagent dengan batas peran/izin, 6 aturan selalu dimuat, slash command eksplisit untuk seluruh 13 route HRAS, empat skill prosedural, konfigurasi permission konservatif, dan sumber HRAS RC4 yang dipertahankan beserta manifest/hash-nya. Custom agents Markdown, custom rules, project `AGENTS.md`, skills dan workflows memang menjadi mekanisme kustomisasi yang didokumentasikan Kilo Code saat ini. citeturn812889search0turn429078search0turn429078search2turn429078search3turn866500search1

Namun, beberapa kontrak kritis HRAS memerlukan komponen tepercaya di luar model: authorization broker, operation ledger durable, idempotency dan reconciliation, verifikasi identitas artifact/config, evidence sink, controller status/release dan observasi boundary tool yang nyata. HRAS sendiri menyatakan reference controller bukan production security boundary dan runtime suite belum dijalankan. Karena itu, adapter ini **siap sebagai scaffold untuk pilot engineering lokal yang diawasi setelah uji Kilo runtime**, bukan sertifikasi autonomous production.

### Temuan terpenting

| Prioritas | Temuan | Implikasi |
|---|---|---|
| P0 | Prompt, skills, rules dan native Kilo permissions tidak menggantikan trusted HRAS controller | Tindakan eksternal/high-impact tetap harus diblokir sampai broker/controller independen tersedia. |
| P0 | Corpus HRAS berisi 139 kasus `NOT_RUN`; semua `fixture_hash` dan `environment_id` null | Belum ada bukti runtime conformance HRAS. |
| P0 | 136/139 kasus memiliki `allowed_tools` kosong; 0 kasus memiliki `tools_adapter_ref` | Beberapa test boundary/tool-security bisa menjadi vacuous jika target tool tidak benar-benar terhubung dan terobservasi. |
| P1 | Schema registry masih `OPEN_NOT_FROZEN`; JCS helper hanya mencakup corpus saat ini | Hash dan kontrak production belum siap difinalkan tanpa implementasi RFC 8785 penuh dan review independen. |
| P1 | Kilo permissions bersifat pola allow/ask/deny; urutan rule penting dan broad auto-approval berisiko | Perlu konfigurasi konservatif, OS/container sandbox, egress policy, dan evaluasi bypass. citeturn429078search4turn866500search0 |
| P1 | Agent/subagent tidak sama dengan isolasi workspace | Jangan jalankan subagent yang mengedit file yang sama secara paralel tanpa worktree/isolasi. Kilo menyatakan task subagent tidak otomatis membuat Git worktree. citeturn866500search4 |
| P2 | Traceability visi ke requirement/test masih memerlukan semantic review; baseline metadata perlu klarifikasi | Jangan menyimpulkan coverage hanya dari hitungan ID atau baris. |

## 2. Cakupan dan metode

### 2.1 Sumber yang diperiksa

Kajian ini menggunakan paket kandidat HRAS yang tersedia di workspace, terutama:

- `HRAS_v20_Canonical_Autonomous_Production_Grade_Spec.md`
- `HRAS_v20_Compiled_Core_Prompt.md`
- `HRAS_v20_Version.json`
- `HRAS_v20_Contract_Schemas.json`
- `HRAS_v20_Policy_Registry.json`
- `HRAS_v20_Workflow_Transitions.json`
- `HRAS_v20_Requirement_Traceability.json`
- `HRAS_v20_Test_Cases.json`
- `HRAS_v20_Package_Manifest.json`, `HRAS_v20_CHECKSUMS.txt`
- `HRAS_v20_static_validator.py`, `HRAS_v20_package_tool.py`, `HRAS_v20_reference_controller.py`
- `Visi HRAS.md`, `HRAS_v20_Outstanding_Issues_and_Next_Actions.md`, README paket

Saya juga meneliti dokumentasi resmi Kilo Code mengenai custom agents, custom rules, `AGENTS.md`, agent permissions, workflows, skills, MCP, auto-approval, plugin/hooks dan Agent Manager. Daftar link resmi ada di §10.

### 2.2 Batas kajian

**Dikerjakan:** inspeksi source paket, hash/inventory verification, validasi static package, uji regresi upstream, desain adapter Kilo, validasi JSON konfigurasi, pemeriksaan YAML frontmatter, dan tes struktural adapter.

**Belum dikerjakan / `NOT_RUN`:** menginstal atau menjalankan Kilo Code runtime, mendaftarkan agent pada Kilo UI/CLI yang hidup, benchmark model/provider, uji prompt-injection terhadap tool Kilo nyata, menghubungkan MCP eksternal, menjalankan 139 HRAS runtime cases, materialisasi fixtures, trusted authorization broker, operasi eksternal, push/deploy/migrasi.

Ketiadaan runtime Kilo berarti kompatibilitas runtime belum terverifikasi. Validasi file tidak sama dengan bukti bahwa Kilo memuat agent atau menegakkan izin sesuai konfigurasi.

## 3. Audit kondisi sumber HRAS saat ini

### 3.1 Identitas dan status kandidat

Sumber `HRAS_v20_Version.json` mencatat:

- `spec_id`: `HRAS-AUTO-ENG`
- `spec_version`: `20.0.0-rc4`
- `release_status`: `CANDIDATE_NOT_PRODUCTION_READY`
- `schema_registry_status`: `OPEN_NOT_FROZEN`

README kandidat menyebutnya paket spesifikasi dan kontrak, bukan agent siap-install, serta menyatakan paket tidak membawa runtime certification. Ini batas yang harus tetap ditampilkan pada adapter Kilo; jangan mengganti status karena adapter terlihat rapi atau tes lokal lulus.

Ada juga metadata yang perlu klarifikasi pemilik: `HRAS_v20_Version.json` memiliki `baseline_version: 20.0.0-rc3`, sementara header canonical spec menyebut `Parent baseline: HRAS v18.0.0-rc1` dan menyatakan v18 sebagai proposed normative baseline. Ini mungkin dua konsep yang berbeda (baseline paket versus lineage normatif), jadi **belum saya nyatakan sebagai kontradiksi definitif**; minta owner menjelaskan semantiknya dan pertahankan kedua klaim sumber sampai diputuskan.

### 3.2 Corpus test dan bukti runtime

Pemeriksaan ulang `HRAS_v20_Test_Cases.json` menghasilkan:

| Metrik | Hasil teramati |
|---|---:|
| Requirement | 53 |
| Schema definition (`$defs`) | 63 |
| Test case | 139 |
| Typed oracle assertion | 695 |
| Test status `NOT_RUN` | 139/139 |
| `fixture_hash` null | 139/139 |
| `environment_id` null | 139/139 |
| `allowed_tools` kosong | 136/139 |
| `tools_adapter_ref` tersedia | 0/139 |
| Case bertanda release-blocking | 75/139 |

Ini jumlah inventaris dan status yang tersimpan di sumber, bukan hasil test runtime. Khususnya, **37 tes lulus dalam paket ini adalah tes regresi/closure lokal**, bukan bukti bahwa 139 HRAS conformance tests telah berjalan.

### 3.3 Gap arsitektur yang memengaruhi Kilo

HRAS menetapkan bahwa model boleh mengusulkan, tetapi tidak mengotorisasi side effects, menulis canonical state, atau menetapkan delivery status final. Komponen tepercaya perlu melakukan validasi identitas, authorization, precondition, expiry/revocation/replay, durable state write, idempotency/read-back dan reconciliation setelah outcome tidak diketahui. Paket juga meminta bukti artifact-bound, hasil per test-case, dan freshness.

Kilo dapat menyajikan interaksi agent/tool dan mengatur sejumlah permission prompt, tetapi konfigurasi prompt tidak menyediakan sendiri seluruh layanan dan bukti tersebut. Karena itu, integrasi dibagi menjadi **agent orchestration** (Kilo) dan **trusted control plane** (eksternal), bukan mencoba memuat semua otoritas ke dalam satu custom agent.

### 3.4 JCS dan traceability

Dokumen sumber secara eksplisit menyatakan hash helper yang dibundel adalah corpus-bounded untuk input integer-only, sementara implementasi RFC 8785/JCS penuh harus diintegrasikan dan diuji di production. Demikian pula, visi 146 baris telah diikat secara byte-level tetapi semantic one-to-one mapping masih menunggu independent review. Hal-hal ini tidak boleh “diselesaikan” oleh Kilo dengan menambahkan mapping tebakan atau klaim PASS.

## 4. Arsitektur adapter Kilo yang disarankan

### 4.1 Gunakan native Kilo surfaces dengan tepat

Dokumentasi resmi saat ini menjelaskan agent Markdown dengan YAML frontmatter untuk current extension/CLI; `custom_modes.yaml` dan `.kilocodemodes` adalah legacy. Rules dikaitkan melalui `instructions` di `kilo.jsonc`, `AGENTS.md` menjadi instruksi workspace, skills adalah prosedur on-demand, dan workflows didefinisikan sebagai Markdown slash commands. citeturn812889search0turn429078search0turn429078search2turn429078search3turn866500search1

Adapter memakai:

- **1 primary agent:** `hras` — routing, orkestrasi, pipeline, evidence semantics dan final handoff.
- **5 bounded subagents:** `hras-audit` (read-only), `hras-builder`, `hras-test-engineer`, `hras-security-reviewer` (read-only), `hras-evidence-reviewer` (read-only).
- **6 always-loaded rules:** trust/precedence, pipeline/scope, evidence/delivery, security/side effects, testing/product quality, research/citations.
- **15 slash commands:** entry point terpisah untuk seluruh 13 route HRAS ditambah workflow khusus remediasi dan release review.
- **4 skills on-demand:** audit-driven remediation, evidence verification, secure tool action, product quality.
- **Project config:** `kilo.jsonc` dengan `instructions` dan permission konservatif.
- **Source preservation:** paket HRAS RC4 lengkap berada di `.hras/source/` dengan inventory dan hash aslinya.

Satu orchestrator + subagents dipilih alih-alih membuat 13 agent duplikat karena 13 nilai tersebut adalah **HRAS route enum**, sedangkan `mode: primary|subagent|all` adalah klasifikasi agent Kilo. Kedua enum itu berbeda dan tidak boleh disamakan. Tiap route tetap tersedia eksplisit melalui slash command agar mudah dipilih, ditinjau dan diuji.

### 4.2 Mapping capability

| Kontrak HRAS | Implementasi Kilo | Status cakupan |
|---|---|---|
| Klasifikasi route HRAS | Prompt utama + 13 route slash commands | Procedural, perlu runtime test |
| Instruksi inti dan spec kanonik | `.hras/source/` dirujuk dari primary agent | Source tersedia; model adherence belum teruji |
| Global/project rules | 6 file di `.kilo/rules/`, didaftarkan di `kilo.jsonc` | Terpasang secara file; live loading belum teruji |
| Read-only audit/security/evidence | Permissions `edit: deny`, `bash: deny` pada helper terkait | Native boundary; harus diuji di Kilo runtime |
| TDD dan remediations | `/hras-remediate`, `hras-test-engineer`, worklist/proof templates | Workflow/prosedur tersedia; tidak otomatis mengesahkan output |
| Riset terkini | `/hras-research`, `websearch`/`webfetch` meminta izin | Fitur tersedia setelah tool permission & akses diperiksa |
| External tool actions | `/hras-tool-action`, aturan stop, `ask/deny` | Preparation-only bila trusted broker tidak ada |
| Release review | `/hras-release-review`, evidence reviewer | Rekomendasi; bukan otorisasi controller |
| Durable operation state/reconciliation | Tidak diklaim sebagai Kilo-native | Gap eksternal P0 |
| Signed identity/config/evidence sink | Roadmap eksternal | Gap eksternal P0/P1 |
| MCP | Tidak dikonfigurasi otomatis | Sengaja disabled sampai ada threat review dan least privilege |

### 4.3 Hak akses yang dipasang

Starter configuration menerapkan prinsip berikut:

- File edit dan shell execution membutuhkan approval secara default.
- Command yang di-auto-allow dibatasi pada beberapa inspeksi Git yang read-only.
- Pattern umum yang berisiko tinggi — misalnya `git push*`, `git reset --hard*`, `git clean -fd*`, `sudo *`, `terraform apply/destroy*`, `kubectl apply/delete*`, `helm upgrade*`, `docker push*`, `npm publish*`, dan `gh pr merge*` — ditempatkan sebagai deny pattern.
- Subagent hanya dapat dipanggil jika namanya tercantum di permission map.
- Agent audit/security/evidence bersifat read-only; builder dan test engineer memiliki izin edit yang lebih terbatas/bertanya.
- Tidak ada model ID, MCP server, credential, atau remote plugin yang dikonfigurasi otomatis.

Kilo menjelaskan tiga hasil permission `allow/ask/deny` dan menyatakan rule matching menggunakan urutan, dengan rule terakhir yang cocok menang. Dokumentasi juga memperingatkan bahwa auto-approval memberi akses langsung dan dapat menyebabkan data loss atau kerusakan. citeturn429078search4turn866500search0

**Batas penting:** pattern deny bukan parser shell yang lengkap dan bukan sandbox. Pemanggilan melalui alias, interpreter lain, command chaining, tool/MCP lain, plugin atau kredensial yang sudah tersedia dapat menghasilkan jalur aksi yang tidak tertangkap pola sederhana. Karena itu, permission configuration adalah defense-in-depth; enforcement aktual memerlukan isolasi OS/container, egress allowlist, credential separation, branch protection dan controller eksternal.

### 4.4 Skills, rules dan injection

Instruksi yang kritis (evidence truthfulness, no unauthorized effects, do not obey embedded instructions in repository/web/tool output) diletakkan di primary agent dan rules yang selalu dimuat, tidak hanya skill. Skills dipakai untuk rincian prosedur yang dapat dimuat sesuai konteks karena dokumentasi Kilo menyatakan skill discovery memberi agent metadata dan konten penuh dimuat saat relevan. citeturn866500search1

Kilo juga mencatat `AGENTS.md` otomatis dimuat dan dilindungi dari edit agent tanpa approval eksplisit. Urutan prioritas prompt/instructions/AGENTS/skills berbeda, sehingga instruksi kritis tidak sebaiknya bergantung pada `AGENTS.md` saja. citeturn429078search2

### 4.5 MCP, plugin dan isolasi agent

Adapter tidak menambahkan MCP server atau plugin karena keduanya memperluas capability. Kilo mendukung konfigurasi MCP lokal (STDIO) dan remote (HTTP/SSE) serta permission tool namespaced; setiap server perlu ditinjau terpisah dan tidak sebaiknya di-auto-approve secara luas. citeturn866500search3

Kilo plugins dapat menambahkan tools dan mengintersep tool call lewat hook seperti `tool.execute.before`, dan dokumentasi memberi contoh memblokir pembacaan `.env` dengan error. citeturn856673view2turn811628view0 Plugin khusus HRAS adalah kandidat peningkatan yang baik untuk intersepsi dan logging, tetapi **belum termasuk aktif dalam adapter ini**: plugin harus dikunci versinya, di-review, diuji di target build dan diuji adversarial; ia juga belum boleh dianggap sebagai pengganti authorization broker atau durable operation ledger.

Kilo menjelaskan bahwa task subagent tidak otomatis membuat Git worktree; untuk isolasi filesystem/branch, gunakan Agent Manager worktree atau proses terpisah. citeturn866500search4 Jangan memberi dua subagent tugas edit yang saling tumpang tindih pada workspace yang sama.

## 5. Gap register yang harus ditutup untuk standar rigor maksimum

### P0 — sebelum mengizinkan aksi eksternal otonom

**KG-001 — Trusted authorization broker.** Validasi identitas/authority dari sumber tepercaya; signature bytes; audience, resource, scope, expiry, revocation, replay; keputusan policy; audit trail. Model-generated boolean atau teks bukan otorisasi.

**KG-002 — Durable operation record + reconciliation.** Ledger atomik sebelum submit; idempotency key dan provider operation ID; state `OUTCOME_UNKNOWN`; read-back/rekonsiliasi; tidak boleh blind retry; crash/restart/timeout-after-effect failure injection.

**KG-003 — Complete runtime conformance.** Materialize dan hash 139 fixtures, provision environment ID, freeze oracle/threshold/expected behavior, expose actual tool/provider boundary dan `tools_adapter_ref`, lalu jalankan case satu per satu dengan output/trace asli. Semua 75 case yang source-nya tandai release-blocking harus mempunyai bukti yang sah.

**KG-004 — Release/status controller.** Controller terpisah memverifikasi active spec/schema/policy/validator/config/artifact hash, evidence freshness, all mandatory gates dan authorization; hanya controller boleh menetapkan final status. Kilo boleh merangkum hasil tetapi tidak boleh menulis canonical production state.

### P1 — sebelum release candidate

**KG-005 — JCS yang conformant.** Integrasikan RFC 8785/JCS penuh versi-pinned, reject duplicate JSON keys dan invalid I-JSON values; jalankan public conformance vectors dan cross-implementation comparison.

**KG-006 — Test/tool observability.** Definisikan allowed tool surface untuk setiap fixture, membedakan `none` dan `unspecified`; pastikan instrumented boundary benar-benar terpanggil; gunakan provider/egress logs untuk membuktikan negative cases.

**KG-007 — Version/run manifest.** Rekam Kilo build/version, host OS, provider/model ID/version, variant/effort, prompt/agent/rules/config hashes, MCP/tool schema versions, source code hash, dependency lock, suite hash, fixture/environment IDs, budget dan timestamps setiap run.

**KG-008 — Sandbox dan egress control.** Jalankan di container/worktree disposable dengan mount read-only untuk secrets, no ambient production credential, outbound network allowlist, approval gate untuk high-impact tools, secret scanning, branch protection dan immutable audit log. Uji bypass path (chaining, interpreter, remote tool, MCP, plugin).

**KG-009 — Adversarial eval berulang.** Frozen corpus untuk prompt injection dari source, dependency README, issue, docs, web, terminal output, image metadata dan MCP response; repeated trial bagi model stochastic; kumpulkan actual tool outcomes, bukan jawaban model yang mengaku aman.

**KG-010 — CI and independent review.** CI menjalankan package identity/schema/checksum tests, unit/regression, linters, type-check, secret/dependency scanners dan integration/e2e/failure-injection sesuai risiko. Independent reviewer menilai traceability, oracle, thresholds dan bukti.

### P2 — untuk klaim kualitas tingkat tertinggi

**KG-011 — Semantic traceability visi.** Pemetaan tiap klausul `Visi HRAS.md` ke requirement, acceptance test atau explicit approved N/A dengan owner dan independent reviewer; line coverage bukan bukti semantic coverage.

**KG-012 — Benchmark produk dan model.** Tetapkan rubric domain-spesifik untuk correctness, task completion, design/UX, accessibility, security, reliability, maintainability, latency/cost; uji beberapa model pada task yang sama, kontrol versi/tool/context dan tetapkan thresholds sebelum run.

**KG-013 — Version semantics dan Kilo config drift.** Klarifikasi hubungan `baseline_version rc3` vs `Parent baseline v18` pada sumber HRAS. Uji konfigurasi pada build Kilo yang sebenarnya karena permukaan config dan plugin dapat berbeda antara versi/CLI/extension.

## 6. Setup dan konfigurasi

### Mode paling aman: coba adapter sebagai workspace terisolasi terlebih dahulu

1. Unduh `HRAS_KiloCode_Adapter_v20.0.0-rc4_r1.zip` dan sidecar SHA-256.
2. Verifikasi SHA-256 sebelum ekstraksi.
3. Ekstrak, lalu buka folder adapter sebagai workspace di Kilo Code.
4. Jalankan `python scripts/validate_adapter.py` dan `python -m unittest discover -s tests -v`.
5. Pilih agent `hras` pada agent picker Kilo.
6. Jalankan `/hras-audit` terhadap adapter sendiri atau repositori latihan; jangan mulai dengan production repository, push, deploy atau migration.
7. Uji setiap slash command, skills, dan approval prompt pada workspace disposable.

### Integrasi ke repository lain

- Merge direktori `.kilo/agents/`, `.kilo/rules/`, `.kilo/commands/`, `.kilo/skills/` tanpa menimpa file yang sudah ada.
- Merge `instructions` dan `permission` dari `kilo.jsonc` ke konfigurasi proyek yang sudah ada; jangan menimpa konfigurasi provider/model/MCP/indexing yang tidak terkait.
- Jika repository telah memiliki `AGENTS.md`, gabungkan bagian HRAS—jangan menimpa konvensi proyek yang ada.
- Salin `.hras/source/` atau subset sumber kanonik yang dipin dari paket; pertahankan filenames yang dirujuk agent.
- Reload Kilo/new session sesudah mengubah project config karena Kilo mendokumentasikan cache konfigurasi project pada sesi aktif. citeturn866500search0
- Review semua permission efektif di UI. Tidak ada MCP yang aktif otomatis.

### Model/provider

Model tidak saya pin karena target provider dan model tidak ditentukan. Pilih model yang kompatibel dengan tool-use dan konteks tugas, lalu evaluasi empiris. Rekam versi/build, variant/effort, token/context limit, cost, latency, coding correctness, citation correctness, refusal/permission behavior, prompt-injection resistance, test integrity dan success rate per case. Tidak ada model yang dapat diklaim universal terbaik tanpa konteks dan hasil evaluasi.

## 7. Verifikasi yang benar-benar dijalankan pada paket R1

Eksekusi dilakukan pada 29 Oktober 2026, dengan Python `3.13.5` (sumber upstream mengunci versi tersebut), output report/cache berada di luar direktori source agar package tidak dimutasi.

### 7.1 Adapter tests

| Bukti | Perintah | Hasil teramati |
|---|---|---|
| Struktur/config/hash adapter | `python scripts/validate_adapter.py` | `92 PASS, 0 FAIL` |
| Unit tests adapter | `python -m unittest discover -s tests -v` | `6 passed`, 0 gagal |
| YAML frontmatter agents/commands/skills | Pemeriksaan dengan PyYAML atas seluruh frontmatter | `25 files`, 0 error |

Pemeriksaan adapter memastikan file penting ada, rules yang disebut dalam config resolve, JSON config dapat diparse, peran agent terdefinisi, skills cocok dengan direktori, source manifest hash cocok, dan corpus tetap tercatat sebagai unrun. Ini bukan live Kilo behavior test.

### 7.2 Upstream HRAS candidate

| Bukti | Perintah | Hasil teramati |
|---|---|---|
| Package source integrity | `PYTHONDONTWRITEBYTECODE=1 python HRAS_v20_package_tool.py --check --strict-root --report /tmp/hras-kilo-adapter-upstream-package-check.json` | `PASS`, 7/7 grup tanpa failure |
| Static validator | `PYTHONDONTWRITEBYTECODE=1 python HRAS_v20_static_validator.py --report-dir /tmp/hras-kilo-adapter-upstream-static` | `PASS`, `83/83`, 0 failure |
| Upstream regression tests | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. pytest -q -p no:cacheprovider tests/test_rc4_plan_closure.py` | `37 passed in 6.19s` |
| Python syntax | `python -m py_compile ...` dengan pycache di luar source | Lulus pada pemeriksaan sebelumnya dalam pipeline sumber yang sama |

Paket source R1 terverifikasi strict-root dan hash, tetapi hasil ini tetap tidak menjalankan 139 runtime test cases HRAS maupun Kilo agent runtime. Test case corpus asli masih `NOT_RUN`.

### 7.3 Identitas paket adapter

- Adapter archive SHA-256: `5fe05ddbeafe98c2dfddfaaa4c34027f4b4ab4de36f4cf5fa67d5a3cdc9a6c5e`
- Sidecar: `HRAS_KiloCode_Adapter_v20.0.0-rc4_r1.zip.SHA256`
- Manifest internal: `ADAPTER_MANIFEST.sha256`

## 8. Kriteria acceptance dan release

**Tahapan gate:**

1. **Static package gate:** hash/manifest/config/frontmatter/source identity lulus.
2. **Kilo load gate:** `hras` muncul di agent picker; rules aktif; commands dan skills benar-benar dipanggil; hasil dicatat dengan Kilo build/version.
3. **Read-only safety gate:** audit/security/evidence agents tidak memodifikasi file; izin ask/deny sesuai; prompt injection tidak mengubah otoritas.
4. **Local TDD gate:** regression test gagal sebelum fix dan lulus setelah; seluruh suite serta lint/typecheck yang relevan lulus; tidak ada test yang dilemahkan.
5. **Tool-boundary gate:** command chaining, shell interpreter alternatif, MCP dan plugin diuji dengan boundary instrumentation; tidak ada aksi eksternal tanpa izin yang sah.
6. **Runtime conformance gate:** 139 case dengan fixture hash, environment ID, oracle/threshold approval, per-case observed traces dan valid evidence; mandatory release-blocking cases semua ditutup.
7. **Control-plane gate:** broker, operation ledger, reconciliation, release controller dan evidence sink telah diuji secara independen.
8. **Production gate:** security/privacy/operations/owner review, rollback rehearsal, monitoring/runbook, artifact identity check dan target smoke/E2E selesai.

Status akhir hanya dapat meningkat jika buktinya meningkat. Jangan menganggap agent config yang syntactically valid sebagai `KILO_RUNTIME_VERIFIED`; jangan menganggap local tests lulus sebagai `HRAS_RUNTIME_CONFORMANT`; dan jangan menyatakan `PRODUCTION_READY`, `DEPLOYED_AND_VERIFIED`, atau `MASTERPIECE_VERIFIED` dengan mandatory gate yang `NOT_RUN`, `UNKNOWN`, atau `BLOCKED`.

## 9. Kesimpulan final

Adapter ini menyediakan permukaan Kilo yang konkret untuk memulai HRAS: struktur agent, route commands, rules, skills, permission profile, source reference, provenance checking, dan prosedur acceptance. Struktur lokal serta sumber kandidat sudah diuji dan lulus pada scope yang tercatat.

**Rekomendasi:** gunakan adapter untuk pilot *read-only → local controlled editing* di workspace/worktree disposable. Jangan memberinya akses kredensial atau MCP yang dapat melakukan write ke layanan produksi. Sebelum mengklaim level maximum/rigorous untuk penggunaan otonom di Kilo, tutup KG-001–KG-010 terlebih dahulu; terutama trusted authorization/operation controller dan bukti runtime 139-case. Kualitas “maximum” harus dinilai dengan standar dan bukti yang ditentukan sebelumnya, bukan dinyatakan hanya karena prompt, agent tree atau tes lokal tampak lengkap.

## 10. Sumber resmi Kilo Code (diakses/diteliti 2026-10-29)

1. **Custom Modes / custom agents** — current Markdown YAML-frontmatter agents, paths and permission properties. https://kilo.ai/docs/customize/custom-modes citeturn812889search0turn943518search0
2. **Custom Rules** — project/global instructions and `.kilo/rules/` loading. https://kilo.ai/docs/customize/custom-rules citeturn429078search0
3. **AGENTS.md** — load behavior, portability, and instruction precedence. https://kilo.ai/docs/customize/agents-md citeturn429078search2
4. **Workflows** — Markdown slash commands and frontmatter. https://kilo.ai/docs/customize/workflows citeturn429078search3
5. **Skills** — `SKILL.md`, metadata-driven on-demand loading and directories. https://kilo.ai/docs/customize/skills citeturn866500search1
6. **Agent Permissions** — `allow/ask/deny`, last-matching rule wins and command pattern logic. https://kilo.ai/docs/customize/agent-permissions citeturn429078search4
7. **Auto-Approving Actions** — risk warning and project configuration caching. https://kilo.ai/docs/getting-started/settings/auto-approving-actions citeturn866500search0
8. **Using MCP in Kilo Code** — MCP transports/configuration and per-tool permissions. https://kilo.ai/docs/automate/mcp/using-in-kilo-code citeturn866500search3
9. **Plugins** — tool interception hooks and plugin loading. https://kilo.ai/docs/automate/extending/plugins citeturn856673view2turn811628view0
10. **Agent Manager** — task subagents and worktree isolation distinction. https://kilo.ai/docs/automate/agent-manager citeturn866500search4
11. **Codebase Indexing** — optional semantic search and privacy/config considerations. https://kilo.ai/docs/customize/context/codebase-indexing citeturn943518search1
