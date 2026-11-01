# مستندات ابزار سنجش منابع الگوریتم‌ها

فایل ابزار: `experiments/profile_algorithm_resources.py`
فایل تست: `tests/test_resource_profiling.py`

## روش اندازه‌گیری

- زمان اجرا با `time.perf_counter()` و بر حسب میلی‌ثانیه ثبت می‌شود.
- حافظه با `tracemalloc` و بر حسب مگابایت ثبت می‌شود. این مقدار فقط اوج حافظه‌ی تخصیص‌یافته‌ی تحت ردیابی پایتون است. معادل کل حافظه‌ی فیزیکی فرایند یا مصرف انرژی نیست.
- زمان و حافظه در اجراهای جداگانه اندازه‌گیری می‌شوند تا سربار `tracemalloc` روی زمان اثر نگذارد.
- برای هر ترکیب، یک اجرای گرم‌کننده، حداقل ۵ تکرار زمان‌سنجی و چند تکرار حافظه انجام می‌شود.
- از زمان، میانه و دامنه‌ی بین‌چارکی گزارش می‌شود. از حافظه، میانه گزارش می‌شود.
- گراف ورودی تغییر نمی‌کند. اگر الگوریتمی گراف را تغییر دهد، وضعیت آن `failed` با دلیل `graph_modified` ثبت می‌شود.

## نحوه اجرا

```
python3 -m experiments.profile_algorithm_resources --source project
python3 -m experiments.profile_algorithm_resources --source reference --algorithms exact mc
python3 -m experiments.profile_algorithm_resources --topologies builtin --graphs cycle_8 mesh_3x3 --probabilities 0.1 0.2
python3 -m pytest tests -q
```

گزینه‌های اصلی: `--timing-repeats` (حداقل ۵)، `--memory-repeats`، `--mc-trials`، `--mc-seed`، `--exact-max-edges`، `--output-dir`.

- `--source project` الگوریتم‌های واقعی پوشه‌ی `reliability/` را صدا می‌زند.
- `--source reference` فقط برای تست خود ابزار است و دو پیاده‌سازی مرجع ساده (Exact و Monte Carlo) دارد.

## اتصال به الگوریتم‌های پروژه

ابزار این توابع پکیج `reliability` را صدا می‌زند (نام‌ها در دیکشنری `PROJECT_FUNCTIONS` بالای فایل هستند):

| الگوریتم | تابع |
|---|---|
| exact | `all_terminal_reliability_exact(graph, failure_probability)` |
| r1 | `first_order_approximation(graph, failure_probability)` |
| r2 | `second_order_approximation(graph, failure_probability)` |
| rs | `subway_type_approximation(graph, failure_probability)` |
| mc | `estimate_all_terminal_reliability_monte_carlo(graph, failure_probability, trials, seed)` |

- اگر Rs خطای `SubwayApproximationNotApplicable` بدهد، وضعیت `not_applicable` ثبت می‌شود، نه `failed`.
- توپولوژی‌ها از `build_benchmark_graphs()` در `experiments/compare_approximations.py` گرفته می‌شوند تا `graph_name` با دیتاست انتخاب‌گر یکی باشد. اگر آن ماژول لیستی از احتمال‌ها (`FAILURE_PROBABILITIES`) داشته باشد، همان استفاده می‌شود.
- Exact برای گراف‌های بیش از ۱۶ یال `not_applicable` ثبت می‌شود (قابل تغییر با `--exact-max-edges`).

## ستون‌های CSV

فایل خلاصه (`resource_profile_summary.csv`):

| ستون | معنی |
|---|---|
| graph_name, num_nodes, num_edges | مشخصات توپولوژی |
| failure_probability | احتمال خرابی لینک |
| algorithm | نام الگوریتم |
| mc_trials, mc_seed | فقط برای Monte Carlo؛ برای بقیه خالی |
| runtime_median_ms, runtime_iqr_ms | میانه و دامنه‌ی بین‌چارکی زمان |
| peak_python_memory_median_mb | میانه‌ی اوج حافظه‌ی تحت ردیابی پایتون |
| status | `ok`، `not_applicable`، `failed` یا `unavailable` |
| reason | دلیل وضعیت غیر `ok` |
| python_version, platform | مشخصات محیط اجرا |
| timing_repeats, memory_repeats | تعداد تکرارها |

فایل خام (`resource_profile_raw.csv`) برای هر تکرار یک سطر دارد: `measurement` (time یا memory)، `repeat`، `value`، `unit` و `result_value`.

برای ترکیب با دیتاست انتخاب‌گر، کلیدهای join این سه ستون هستند: `graph_name` و `failure_probability` و `algorithm`.

## وضعیت‌ها

- `not_applicable`: الگوریتم برای آن گراف قابل استفاده نیست، مثلاً Rs روی گراف دارای پل یا Exact روی گراف خیلی بزرگ. این حالت شکست یا صفر ثبت نمی‌شود.
- `unavailable`: پیاده‌سازی الگوریتم پیدا نشد.
- `failed`: الگوریتم خطا داد یا گراف را تغییر داد.

## محدودیت‌ها

- فقط زمان و حافظه‌ی پایتون اندازه‌گیری می‌شود. انرژی، توان و تأخیر سخت‌افزاری اندازه‌گیری نمی‌شود.
- نتایج به لپ‌تاپ و بار لحظه‌ای سیستم وابسته‌اند. برای مقایسه‌ی منصفانه، همه‌ی اجراها باید روی یک دستگاه و با تنظیمات یکسان انجام شوند.
- پیاده‌سازی مرجع Exact با شمارش همه‌ی حالت‌های یال‌ها کار می‌کند و فقط برای گراف‌های کوچک مناسب است.

## بازتولید نتایج

با `--mc-seed` و `--mc-trials` یکسان، مقدار خروجی Monte Carlo قابل تکرار است. زمان و حافظه تا حد نوسان عادی سیستم تکرارپذیرند. نسخه‌ی پایتون و پلتفرم در هر سطر ثبت می‌شود.

## فایل ترکیبی نهایی (ورودی مدل انتخاب‌گر)

```
python3 -m experiments.build_combined_dataset
```

- ورودی‌ها: `data/benchmarks/selector_accuracy_dataset.csv` (دقت و ویژگی‌های گراف، از بخش هوش مصنوعی) و `data/benchmarks/resource_profile_summary.csv` (زمان و حافظه).
- کلید اتصال: `graph_name` + `failure_probability` + `algorithm`. اگر کلیدها یکی نباشند، کلید تکراری باشد یا `is_applicable` با `status` همخوان نباشد، ابزار خطا می‌دهد.
- خروجی: `data/benchmarks/selector_full_dataset.csv` (۵۴۰ سطر). ستون‌های اضافه: `experiment_id`، `topology_type` و ستون‌های منابع (`runtime_median_ms` و ...، با وضعیت در `resource_status`). سطرهای `not_applicable` نگه داشته می‌شوند و ستون‌های زمان و حافظه‌شان خالی است.
- `data/benchmarks/` در Git نسخه‌بندی می‌شود (برخلاف `outputs/`). بعد از اجرای نهایی روی لپ‌تاپ اصلی، دو فایل ورودی و فایل ترکیبی را دوباره بساز و جایگزین کن.

## بنچمارک منابع Edge Deletion

```
python3 -m experiments.profile_edge_deletion_resources
```

- Edge Deletion میانگین قابلیت اطمینان (انتگرال روی q) را تخمین می‌زند، نه R(q) برای یک احتمال خرابی. پس جدا اندازه‌گیری می‌شود و با دیتاست R(q) ترکیب نمی‌شود.
- مقایسه با `exact_average` و تعداد نمونه‌های ۱۰۰، ۵۰۰، ۱۰۰۰ و ۲۵۰۰ روی ۱۲ گراف (۶۰ سطر). خروجی: `outputs/edge_deletion_resource_profile.csv`. نمونه‌ی آن در `sample_outputs/` است.
- روش اندازه‌گیری مثل بقیه است (گرم‌کننده، ۵ تکرار زمان، تکرار جدا برای حافظه، میانه و IQR).
