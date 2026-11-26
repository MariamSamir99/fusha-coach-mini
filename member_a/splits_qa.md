# Splits QA

File: `data/splits.csv`

| check | status | detail |
|---|---|---|
| required columns exist | **PASS** |  |
| no duplicate utterance ids | **PASS** | 0 duplicates |
| split values are train/val/test | **PASS** | found: ['test', 'train', 'val'] |
| split 'train' is not empty | **PASS** | 2904 rows |
| split 'val' is not empty | **PASS** | 986 rows |
| split 'test' is not empty | **PASS** | 952 rows |
| speaker-disjoint (no leakage) | **PASS** |  |
| each speaker in exactly one split | **PASS** | 0 speakers spread across splits |
| labels are strictly 0/1 | **PASS** | 0 bad values |
| test has enough ERROR examples | **PASS** |  |
| test has enough CORRECT examples | **PASS** |  |
| contrast 'S' usable on test | **PASS** | test rows=151, wrong=24 |
| contrast 'H+S' usable on test | **WARN** | test rows=32, wrong=3 |
| contrast 'H' usable on test | **PASS** | test rows=123, wrong=17 |
| all referenced audio files exist | **PASS** | 0 missing |
| every split row exists in the annotation table | **PASS** | 0 unknown ids |
| row count accounted for | **PASS** | annotations=4842 splits=4842 dropped=0 |

**Verdict:** safe to use