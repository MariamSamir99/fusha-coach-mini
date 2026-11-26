# Integrity check

| check | result |
|---|---|
| files checked | 4841 |
| empty / unreadable | **0** |
| shorter than 0.15s | 0 |
| byte-identical groups | **50** |
| ...crossing splits (leakage) | **0** |
| ...with conflicting labels | 0 |
| speakers | 79 |
| speaker groups | 78 |

## Speakers that are the same person

These ids share byte-identical audio, so they must never be split
across train/val/test:

- **62** = 62, 64

## Consequence

Splitting is done on `group_id` from `data/speaker_groups.csv`.
A group is a set of speaker ids that share at least one identical recording.
This removes leakage without discarding data.