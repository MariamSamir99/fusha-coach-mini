# Data Audit - MON3EMPASHA Arabic Mispronunciation (working corpus)

Source: `data\annotations.csv`

## Annotation table
- rows: **4841**
- columns: `['audio_path', 'text', 'label', 'speaker_id', 'word_index', 'has_H', 'has_h', 'has_S', 'has_s', 'contrast']`
- detected roles: `{'speaker': 'speaker_id', 'audio': 'audio_path', 'label': 'label', 'text': 'text'}`
- mispronounced: **686** | correct: **4155**
- unique speakers: **79**

## Audio
- files found: **4841** (broken: 0)
- total duration: **0.90 h**
- sample rates: `{16000: 4841}`

## Open items
- [ ] licence terms read and recorded
- [ ] contrast selection justified with per-phoneme counts
- [ ] decision recorded: one contrast or two

## Scope candidates (auto)

Counts are at **target-phoneme level**: a word containing both target
letters is counted once per contrast.

| contrast | utterances | mispronounced | error rate |
|---|---|---|---|
| H | 764 | 111 | 0.145 |
| S | 975 | 123 | 0.126 |

Keep two contrasts only if each has enough mispronounced examples to survive a 60/20/20 speaker split (rule of thumb: >= 60 errors per contrast before splitting). Otherwise reduce to one contrast and say so in the report instead of claiming a reliable comparison.