# خلية النحل AlKhaliya

خلية النحل محرك أتمتة محلي dry-run شبيه n8n: يقرأ workflow JSON، يشغل nodes بسيطة، يصنف الرسائل، يوجهها لطوابير، ويبني payload webhook دون إرسال حقيقي.

## آلية العمل

1. `init` ينشئ workflow خدمة عملاء جاهز.
2. `run` يشغل workflow على رسالة واحدة.
3. `convert-bitext` يحول رسائل Bitext إلى أحداث.
4. `batch/stress` يقيسان نجاح workflow والضغط.

## تشغيل سريع

```powershell
python -m alkhaliya.cli init
python -m alkhaliya.cli run --text "refund my order"
python -m alkhaliya.cli convert-bitext
python -m alkhaliya.cli batch
```

## بيانات الاختبار

تعتمد على بيانات Bitext التي جلبها `C:\Projects\almandoub` من الإنترنت بعدد 12,000 رسالة.

## آخر نتائج

- الاختبارات الذاتية: 2/2 ناجحة.
- Workflow افتراضي: 5 nodes (`classify/route/template/webhook/assert`).
- Benchmark: 12,000 حدث، success=100%، errors=0، p99=0.125ms.
- توزيع الطوابير: human_support=2,149، sales_ops=1,118، finance=1,425، general_inbox=7,308.
- Stress: 36,000 حدث، success=100%، errors=0، p99=0.119ms، peak memory=1.19MB.

## تحسينات إنتاجية 2026-07-04

- كل webhook يعمل بوضع dry-run ويُسجل payload بدلاً من إرسال حقيقي، حتى لا يحدث أثر خارجي أثناء الاختبار.
- كل node يكتب trace بحالة `ok/error`، وهذا يجعل فشل workflow قابلاً للتشخيص.
- `assert` node يضمن وجود المخرجات الحرجة مثل `reply` قبل اعتبار التشغيل ناجحاً.

## التشغيل المؤسسي (Enterprise) — v1.0.0

- **خدمة workflows عبر HTTP**: `python -m alkhaliya.cli serve` → `POST /api/run {"text"}` (dry-run دائماً؛ لا أثر خارجي).
- **الـworkflow يحمل مرة واحدة** عند الإقلاع (`ALKHALIYA_WORKFLOW`، افتراضي `workflows\customer_hive.json`).
- **نقاط فحص**: `/api/health` (مفتوح) · `/api/version` · `/api/metrics`.
- **تهيئة عبر البيئة**: متغيرات `ALKHALIYA_*` — انظر `docs/OPERATIONS.md`.
- **مصادقة**: `ALKHALIYA_API_KEY` → ترويسة `X-API-Key`. **سجلات JSON**: `logs\alkhaliya.service.jsonl`.
