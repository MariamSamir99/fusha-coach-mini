# Splits QA

File: `data/splits.csv`

| check | status | detail |
|---|---|---|
| required columns exist | **PASS** |  |
| no duplicate utterance ids | **PASS** | 0 duplicates |
| split values are train/val/test | **PASS** | found: ['test', 'train', 'val'] |
| split 'train' is not empty | **PASS** | 2957 rows |
| split 'val' is not empty | **PASS** | 984 rows |
| split 'test' is not empty | **PASS** | 900 rows |
| speaker-disjoint (no leakage) | **PASS** |  |
| each speaker in exactly one split | **PASS** | 0 speakers spread across splits |
| group-disjoint (identical-audio ids together) | **PASS** |  |
| group count is reported | **PASS** | 78 groups / 79 speakers |
| labels are strictly 0/1 | **PASS** | 0 bad values |
| test has enough ERROR examples | **PASS** |  |
| test has enough CORRECT examples | **PASS** |  |
| contrast 'S' usable on test | **PASS** | test rows=155, wrong=16 |
| contrast 'H+S' usable on test | **WARN** | test rows=31, wrong=5 |
| contrast 'H' usable on test | **PASS** | test rows=106, wrong=21 |
| all referenced audio files exist | **PASS** | 0 missing |
| every split row exists in the annotation table | **PASS** | 0 unknown ids |
| row count accounted for | **PASS** | annotations=4841 splits=4841 dropped=0 |

**Verdict:** safe to use